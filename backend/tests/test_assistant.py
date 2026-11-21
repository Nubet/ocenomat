import json
from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import update
from test_assessments import assessment_access as assessment_access
from test_assessments import auth, create
from test_documents import MemoryStorage
from test_knowledge_retriever import corpus as corpus

from app.integrations.llm.protocol import LLMError
from app.modules.ai.schemas import (
    AssistantRequest,
    GroundedAnswer,
    SupportReview,
)
from app.modules.ai.service import answer_question, validate_citations
from app.modules.knowledge.extraction import sha256
from app.modules.knowledge.models import KnowledgeChunk, KnowledgeSource
from app.modules.knowledge.retriever import RetrievalResult, RetrievedChunk

TEXT = "Oceniający może wybrać nie więcej niż trzy dodatkowe kryteria oceny."


class StubProvider:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def generate(self, messages, *, response_model, **kwargs):
        self.calls.append((messages, response_model))
        value = self.results.pop(0)
        if isinstance(value, Exception):
            raise value
        if callable(value):
            value = value()
        return response_model.model_validate(value)


@pytest.fixture
def evidence():
    part = RetrievedChunk(
        chunk_id=uuid4(),
        source_id="synthetic-law",
        canonical_document_id="test",
        title="Synthetic test law",
        source_type="legal_act",
        assessment_kind="periodic",
        document_version="test-only",
        content=TEXT,
        content_sha256=sha256(TEXT.encode()),
        locator="html:#para_5",
        page=None,
        official_url="https://eli.gov.pl/test.html",
        legal_checked_on=date.today(),
        retrieval_score=1,
        context_only=False,
    )
    return RetrievalResult(status="matched", chunks=[part])


def generated(evidence, **overrides):
    return {
        "status": "answered",
        "claims": [
            {
                "text": "Można wybrać najwyżej trzy dodatkowe kryteria.",
                "evidence": [
                    {
                        "chunk_id": str(evidence.chunks[0].chunk_id),
                        "quote": TEXT,
                    }
                ],
            }
        ],
        **overrides,
    }


def review(**overrides):
    return {
        "status": "supported",
        "supported_claims": [0],
        "answers_question": True,
        **overrides,
    }


class StubRetriever:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def retrieve(self, query):
        self.calls.append(query)
        return self.results.pop(0)


def test_answer_requires_provenance_and_separate_support_review(evidence):
    retriever = StubRetriever(evidence, evidence)
    provider = StubProvider(generated(evidence), review())
    result = answer_question(
        AssistantRequest(
            question="Ile kryteriów dodatkowych?", assessment_kind="periodic"
        ),
        retriever,
        provider,
    )
    assert result.status == "answered"
    citation = result.claims[0].citations[0]
    assert citation.quote == TEXT and citation.locator == "html:#para_5"
    assert citation.original_path == "/api/v1/knowledge/sources/synthetic-law/original"
    assert citation.official_url == evidence.chunks[0].official_url
    assert citation.title == evidence.chunks[0].title and citation.page is None
    assert [model for _, model in provider.calls] == [GroundedAnswer, SupportReview]
    assert len(retriever.calls) == 2
    assert "CAŁYCH" in provider.calls[1][0][0].content


@pytest.mark.parametrize(
    "change",
    [
        "invented_id",
        "invented_quote",
        "empty_quote",
        "url",
        "changed",
        "revoked",
        "hash",
        "location",
        "no_claims",
    ],
)
def test_citation_validation_fails_closed(evidence, change):
    answer = generated(evidence)
    current = evidence.model_copy(deep=True)
    reference = answer["claims"][0]["evidence"][0]
    if change == "invented_id":
        reference["chunk_id"] = str(uuid4())
    elif change == "invented_quote":
        reference["quote"] = "Cztery kryteria są obowiązkowe."
    elif change == "empty_quote":
        reference["quote"] = " " * 8
    elif change == "url":
        answer["claims"][0]["text"] = "https://invented.invalid/§999"
    elif change == "changed":
        current.chunks[0].content = "Inna treść"
    elif change == "revoked":
        current.chunks = []
    elif change == "hash":
        evidence.chunks[0].content_sha256 = "0" * 64
        current = evidence
    elif change == "location":
        evidence.chunks[0].locator = ""
        current = evidence
    else:
        answer["claims"] = []
    assert (
        validate_citations(GroundedAnswer.model_validate(answer), evidence, current)
        is None
    )


@pytest.mark.parametrize(
    "verdict",
    [
        review(status="insufficient_evidence"),
        review(supported_claims=[]),
        review(supported_claims=[0, 0]),
        review(answers_question=False),
        review(status="conflicting_sources"),
    ],
)
def test_valid_citation_is_not_enough_to_accept_unsupported_claim(evidence, verdict):
    answer = generated(evidence)
    answer["claims"][0]["text"] = (
        "Należy wybrać dokładnie cztery kryteria bez wyjątków."
    )
    result = answer_question(
        AssistantRequest(question="Ile kryteriów?"),
        StubRetriever(evidence),
        StubProvider(answer, verdict),
    )
    expected = (
        "conflicting_sources"
        if verdict["status"] == "conflicting_sources"
        else "insufficient_evidence"
    )
    assert result.status == expected and result.claims == []
    assert "cztery" not in result.model_dump_json()


def test_no_evidence_does_not_require_provider_or_send_question():
    retriever = StubRetriever(RetrievalResult(status="insufficient_evidence"))
    assert (
        answer_question(
            AssistantRequest(question="Tajemne dane"), retriever, None
        ).status
        == "insufficient_evidence"
    )


@pytest.mark.parametrize("status", ["insufficient_evidence", "conflicting_sources"])
def test_refusal_does_not_echo_untrusted_model_claims(evidence, status):
    provider = StubProvider(generated(evidence, status=status))
    result = answer_question(
        AssistantRequest(question="Pytanie"), StubRetriever(evidence), provider
    )
    assert result.status == status and result.claims == [] and len(provider.calls) == 1


def test_approval_changed_after_generation_is_rejected(evidence):
    result = answer_question(
        AssistantRequest(question="Pytanie"),
        StubRetriever(evidence, RetrievalResult(status="insufficient_evidence")),
        StubProvider(generated(evidence), review()),
    )
    assert result.status == "insufficient_evidence" and not result.claims


@pytest.mark.parametrize(
    "payload",
    [
        {"question": " "},
        {"question": "a" * 1001},
        {"question": "Test", "roles": ["ADMIN"]},
        {"question": "Test", "employee": "Anna"},
    ],
)
def test_request_rejects_blank_oversized_and_client_context(payload):
    with pytest.raises(ValidationError):
        AssistantRequest.model_validate(payload)


@pytest.fixture
def assistant_api(assessment_access, corpus):
    access = assessment_access
    session, add, _ = corpus
    source, chunks = add(contents=(TEXT,))
    content = b"<html>Original source</html>"
    source.original_sha256 = sha256(content)
    source.original_size = len(content)
    source.provenance = {**source.provenance, "original_sha256": source.original_sha256}
    source_id, chunk_id = source.source_id, chunks[0].id
    session.commit()
    access.storage = MemoryStorage()
    access.storage.objects[source_id] = content
    access.client.app.state.object_storage = access.storage
    access.client.app.state.llm_provider = StubProvider(
        {
            "status": "answered",
            "claims": [
                {
                    "text": "Najwyżej trzy dodatkowe kryteria.",
                    "evidence": [{"chunk_id": str(chunk_id), "quote": TEXT}],
                }
            ],
        },
        review(),
    )
    return SimpleNamespace(
        access=access, source_id=source_id, chunk_id=chunk_id, content=content
    )


def ask(api, name="a", **data):
    return api.access.client.post(
        "/api/v1/ai/assistant",
        headers=auth(api.access, name),
        json={
            "question": "Ile dodatkowych kryteriów?",
            "assessment_kind": "periodic",
            **data,
        },
    )


@pytest.mark.integration
def test_api_generates_real_citations_and_downloads_immutable_original(assistant_api):
    api = assistant_api
    response = ask(api)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "private, no-store"
    data = response.json()
    assert data["status"] == "answered"
    citation = data["claims"][0]["citations"][0]
    download = api.access.client.get(
        citation["original_path"], headers=auth(api.access)
    )
    assert download.content == api.content
    assert "attachment" in download.headers["content-disposition"]
    assert "sandbox" in download.headers["content-security-policy"]
    assert (
        "storage_key" not in response.text and "original_filename" not in response.text
    )
    assert len(api.access.client.app.state.llm_provider.calls) == 2


@pytest.mark.integration
@pytest.mark.parametrize("name", ["b", "hr", "admin", "none"])
def test_unauthorized_assessment_never_reaches_llm_or_storage(assistant_api, name):
    api = assistant_api
    assessment_id = create(api.access).json()["id"]
    response = ask(api, name, assessment_id=assessment_id)
    assert response.status_code == 404
    assert (
        not api.access.client.app.state.llm_provider.calls
        and not api.access.storage.calls
    )


@pytest.mark.integration
def test_unauthenticated_requests_are_rejected(assistant_api):
    client = assistant_api.access.client
    assert (
        client.post("/api/v1/ai/assistant", json={"question": "test"}).status_code
        == 401
    )
    assert (
        client.get(
            f"/api/v1/knowledge/sources/{assistant_api.source_id}/original"
        ).status_code
        == 401
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    "code,status",
    [
        ("timeout", 504),
        ("rate_limited", 429),
        ("unavailable", 503),
        ("invalid_response", 502),
    ],
)
def test_provider_errors_are_not_evidence_refusals(assistant_api, code, status, caplog):
    api = assistant_api
    api.access.client.app.state.llm_provider = StubProvider(LLMError(code))
    response = ask(api)
    assert (
        response.status_code == status
        and response.json()["detail"]["code"] == f"llm_{code}"
    )
    assert "Ile dodatkowych" not in caplog.text


@pytest.mark.integration
def test_missing_provider_is_only_an_error_when_evidence_exists(assistant_api):
    api = assistant_api
    api.access.client.app.state.llm_provider = None
    assert ask(api).status_code == 503
    assert (
        ask(api, question="Podróże międzygalaktyczne").json()["status"]
        == "insufficient_evidence"
    )


@pytest.mark.integration
def test_context_is_server_owned_and_result_uses_existing_engine_without_llm(
    assistant_api,
):
    api = assistant_api
    assessment = create(api.access).json()
    before = api.access.client.get(
        f"/api/v1/assessments/{assessment['id']}", headers=auth(api.access)
    ).json()
    response = ask(api, assessment_id=assessment["id"], task="assessment_result")
    assert response.json()["result"] == {"outcome": "incomplete", "mean": None}
    assert not api.access.client.app.state.llm_provider.calls
    assert (
        ask(api, assessment_id=assessment["id"], assessment_kind="first").status_code
        == 422
    )
    after = api.access.client.get(
        f"/api/v1/assessments/{assessment['id']}", headers=auth(api.access)
    ).json()
    assert before == after
    response = ask(api, assessment_id=assessment["id"])
    assert response.json()["status"] == "answered"
    messages = api.access.client.app.state.llm_provider.calls[0][0]
    context = json.loads(messages[1].content)
    assert context["assessment_kind"] == "periodic"
    assert (
        "Test Anna" not in messages[1].content
        and assessment["id"] not in messages[1].content
    )


@pytest.mark.integration
def test_mid_request_approval_revocation_is_seen_by_retriever(assistant_api):
    api = assistant_api
    provider = api.access.client.app.state.llm_provider

    def revoke():
        api.access.session.get_bind().execute(
            update(KnowledgeChunk)
            .where(KnowledgeChunk.id == api.chunk_id)
            .values(verification_status="needs_review")
        )
        return review()

    provider.results[1] = revoke
    assert ask(api).json()["status"] == "insufficient_evidence"


@pytest.mark.integration
@pytest.mark.parametrize("private", [True, False])
def test_source_access_filters_before_storage_and_checksum_is_checked(
    assistant_api, private
):
    api = assistant_api
    if private:
        api.access.session.execute(
            update(KnowledgeSource)
            .where(KnowledgeSource.source_id == api.source_id)
            .values(source_type="sample_job_description")
        )
        api.access.session.commit()
    else:
        api.access.storage.objects[api.source_id] = b"tampered"
    response = api.access.client.get(
        f"/api/v1/knowledge/sources/{api.source_id}/original", headers=auth(api.access)
    )
    assert response.status_code == (404 if private else 503)
    if private:
        assert not api.access.storage.calls
