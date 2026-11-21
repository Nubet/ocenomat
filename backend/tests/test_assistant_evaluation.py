from test_assistant import StubProvider, StubRetriever
from test_assistant import evidence as evidence

from app.integrations.llm.protocol import LLMError
from app.modules.ai.evaluate import EvaluationCase, evaluate
from app.modules.knowledge.retriever import RetrievalResult


def test_evaluation_separates_retrieval_from_generation_and_stops_provider_retries(
    evidence,
):
    part = evidence.chunks[0]
    cases = [
        EvaluationCase(
            id="answerable",
            kind="periodic",
            question="Ile kryteriów dodatkowych?",
            expected_answer="Najwyżej trzy.",
            references=[(part.source_id, part.locator)],
        ),
        EvaluationCase(
            id="missing",
            kind="first",
            question="Co nakazuje fikcyjny paragraf?",
            expected_answer="Brak podstaw.",
            expected_status="insufficient_evidence",
            missing_basis="Fikcyjny paragraf.",
        ),
    ]
    retriever = StubRetriever(
        evidence, evidence, RetrievalResult(status="insufficient_evidence")
    )
    provider = StubProvider(LLMError("unavailable"))
    report = evaluate(cases, retriever, provider)
    assert report["retrieval_reference_cases"] == report["retrieval_hits"] == 1
    assert report["generated_responses"] == 0
    assert report["provider_error"] == "unavailable"
    assert report["manual_review_required"] is True
    assert report["results"][1]["reference_hit"] is None
    assert len(provider.calls) == 1
