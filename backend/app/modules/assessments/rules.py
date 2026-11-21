from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal
from uuid import UUID

from app.modules.catalog.identifiers import stable_id

PERIODIC_SCORES = (1, 3, 5, 7, 9)
FIRST_SCORES = (3, 5, 7)
SUGGESTION_POLICY = "nearest-mean-lower-tie-v1"
COMMON_CRITERIA = (
    "Organizacja pracy i orientacja na osiąganie celów",
    "Współpraca",
    "Komunikacja",
)
REQUIRED_CRITERIA = {
    "C": tuple(
        stable_id(name)
        for name in (
            "Wykorzystywanie wiedzy i doskonalenie zawodowe",
            "Rzetelność",
            *COMMON_CRITERIA,
        )
    ),
    "B": tuple(
        stable_id(name)
        for name in (
            "Zarządzanie ludźmi",
            "Podejmowanie decyzji i odpowiedzialność",
            *COMMON_CRITERIA,
        )
    ),
}


@dataclass(frozen=True)
class Result:
    outcome: Literal["incomplete", "positive", "negative"]
    mean: Fraction | None


@dataclass(frozen=True)
class Suggestion:
    score: int | None
    policy_version: str = SUGGESTION_POLICY


def periodic_criteria(
    form: str, additional: Sequence[UUID], catalog: Collection[UUID]
) -> tuple[UUID, ...]:
    if form not in REQUIRED_CRITERIA:
        raise ValueError("Only periodic forms B and C are supported")
    required = REQUIRED_CRITERIA[form]
    if len(additional) > 3:
        raise ValueError("At most three additional criteria are allowed")
    selected = (*required, *additional)
    if len(set(selected)) != len(selected):
        raise ValueError("Criteria cannot be duplicated")
    if any(not isinstance(c, UUID) or c not in catalog for c in selected):
        raise ValueError("Criteria must exist in the pinned catalog version")
    return selected


def validate_scores(values: Sequence[int | None], allowed: tuple[int, ...]) -> None:
    if any(v is not None and (type(v) is not int or v not in allowed) for v in values):
        raise ValueError("Invalid score")


def periodic_result(
    active_criteria: Sequence[UUID], confirmed_ratings: Mapping[UUID, int | None]
) -> Result:
    if not 5 <= len(active_criteria) <= 8:
        raise ValueError("Expected five to eight active criteria")
    if len(set(active_criteria)) != len(active_criteria):
        raise ValueError("Active criteria must be unique")
    if not set(confirmed_ratings).issubset(active_criteria):
        raise ValueError("Rating does not belong to an active criterion")
    values = [confirmed_ratings.get(c) for c in active_criteria]
    validate_scores(values, PERIODIC_SCORES)
    if any(v is None for v in values):
        return Result("incomplete", None)
    scores = [v for v in values if v is not None]
    mean = Fraction(sum(scores), len(scores))
    return Result("positive" if mean > 4 and 1 not in scores else "negative", mean)


def suggest_score(observations: Sequence[int | None]) -> Suggestion:
    validate_scores(observations, (0, 1, 2, 3, 4))
    scores = [2 * v + 1 for v in observations if v is not None]
    if not scores:
        return Suggestion(None)
    mean = Fraction(sum(scores), len(scores))
    return Suggestion(min(PERIODIC_SCORES, key=lambda score: abs(score - mean)))


def first_result(
    scores: Sequence[int | None],
    report_submitted_on_time: bool | None,
    exam: Literal["passed", "failed", "not_applicable"] | None,
    exemption_basis: str | None = None,
) -> Result:
    if len(scores) != 5:
        raise ValueError("Expected five first-assessment elements")
    validate_scores(scores, FIRST_SCORES)
    if (
        report_submitted_on_time is not None
        and type(report_submitted_on_time) is not bool
    ):
        raise ValueError("Report confirmation must be true, false or unknown")
    if exam not in (None, "passed", "failed", "not_applicable"):
        raise ValueError("Invalid exam state")
    if exam == "not_applicable" and (
        not isinstance(exemption_basis, str) or not exemption_basis.strip()
    ):
        raise ValueError("Exam exemption requires an explicit basis")
    if (
        any(s is None for s in scores)
        or report_submitted_on_time is None
        or exam is None
    ):
        return Result("incomplete", None)
    confirmed = [s for s in scores if s is not None]
    mean = Fraction(sum(confirmed), 5)
    positive = (
        mean >= 5
        and confirmed.count(3) <= 1
        and report_submitted_on_time
        and exam != "failed"
    )
    return Result("positive" if positive else "negative", mean)
