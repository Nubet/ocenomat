import argparse
import json
from pathlib import Path
from time import perf_counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_database_engine
from app.integrations.llm.factory import create_llm_provider
from app.integrations.llm.protocol import LLMError, LLMProvider
from app.modules.ai.schemas import AssistantRequest
from app.modules.ai.service import answer_question
from app.modules.knowledge.retriever import (
    KnowledgeRetriever,
    PostgresKnowledgeRetriever,
    RetrievalQuery,
)

DATASET = Path(__file__).resolve().parents[3] / "resources/assistant-evaluation.json"


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: Literal["first", "periodic"]
    question: str = Field(min_length=1, max_length=1000)
    expected_answer: str = Field(min_length=1)
    expected_status: Literal["answered", "insufficient_evidence"] = "answered"
    references: list[tuple[str, str]] = Field(default_factory=list)
    missing_basis: str | None = None


def evaluate(
    cases: list[EvaluationCase],
    retriever: KnowledgeRetriever,
    provider: LLMProvider | None = None,
) -> dict:
    results = []
    provider_error = None
    for case in cases:
        start = perf_counter()
        evidence = retriever.retrieve(
            RetrievalQuery(question=case.question, assessment_kind=case.kind)
        )
        found = {(part.source_id, part.locator) for part in evidence.chunks[:5]}
        row = {
            "id": case.id,
            "question": case.question,
            "expected_answer": case.expected_answer,
            "expected_status": case.expected_status,
            "missing_basis": case.missing_basis,
            "retrieval_seconds": round(perf_counter() - start, 4),
            "retrieval_status": evidence.status,
            "top5": sorted(found),
            "reference_hit": (
                set(case.references).issubset(found) if case.references else None
            ),
        }
        if provider is not None and provider_error is None:
            start = perf_counter()
            try:
                response = answer_question(
                    AssistantRequest(question=case.question, assessment_kind=case.kind),
                    retriever,
                    provider,
                )
                row["response"] = response.model_dump(mode="json")
                row["status_matches"] = response.status == case.expected_status
            except LLMError as error:
                provider_error = error.code
            row["answer_seconds"] = round(perf_counter() - start, 4)
        results.append(row)
    measured = [row for row in results if row["reference_hit"] is not None]
    return {
        "cases": len(results),
        "retrieval_reference_cases": len(measured),
        "retrieval_hits": sum(row["reference_hit"] for row in measured),
        "generated_responses": sum("response" in row for row in results),
        "provider_error": provider_error,
        "manual_review_required": True,
        "note": (
            "Retrieval hits and matching statuses do not measure semantic correctness."
        ),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate the public reference corpus."
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Call the configured LLM (may incur costs).",
    )
    args = parser.parse_args()
    cases = [
        EvaluationCase.model_validate(item)
        for item in json.loads(DATASET.read_text())["cases"]
    ]
    if len(cases) < 30 or len({case.id for case in cases}) != len(cases):
        raise ValueError("At least 30 uniquely identified reference cases are required")
    if any(
        case.expected_status == "answered" and not case.references for case in cases
    ):
        raise ValueError("Answerable cases require source references")
    settings = Settings()
    engine = create_database_engine(settings)
    provider = None
    try:
        provider = create_llm_provider(settings) if args.generate else None
        with Session(engine) as session:
            session.execute(text("SET TRANSACTION READ ONLY"))
            report = evaluate(cases, PostgresKnowledgeRetriever(session), provider)
        if args.generate and provider is None:
            report["provider_error"] = "not_configured"
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        if provider is not None:
            provider.close()
        engine.dispose()


if __name__ == "__main__":
    main()
