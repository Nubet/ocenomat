from fractions import Fraction
from uuid import uuid4

import pytest

from app.modules.assessments.rules import (
    REQUIRED_CRITERIA,
    SUGGESTION_POLICY,
    first_result,
    periodic_criteria,
    periodic_result,
    suggest_score,
)


@pytest.mark.parametrize("form", ["B", "C"])
def test_required_criteria_and_three_extras(form):
    extras = [uuid4() for _ in range(3)]
    required = REQUIRED_CRITERIA[form]
    assert len(required) == 5
    assert periodic_criteria(form, extras, (*required, *extras)) == (*required, *extras)


def test_reject_unsupported_form():
    with pytest.raises(ValueError, match="Only periodic"):
        periodic_criteria("A", [], [])


@pytest.mark.parametrize("case", ["duplicate", "required", "unknown", "limit"])
def test_invalid_additional_criteria(case):
    required = REQUIRED_CRITERIA["C"]
    extras = [uuid4() for _ in range(4)]
    additional = {
        "duplicate": [extras[0], extras[0]],
        "required": [required[0]],
        "unknown": [uuid4()],
        "limit": extras,
    }[case]
    with pytest.raises(ValueError):
        periodic_criteria("C", additional, (*required, *extras))


@pytest.mark.parametrize(
    "scores,expected,mean",
    [
        ([5, 5, 5, 5, 5], "positive", Fraction(5)),
        ([3, 3, 3, 5, 5], "negative", Fraction(19, 5)),
        ([3, 3, 5, 5, 5], "positive", Fraction(21, 5)),
        ([1, 9, 9, 9, 9], "negative", Fraction(37, 5)),
        ([None, 9, 9, 9, 9], "incomplete", None),
    ],
)
def test_periodic_result(scores, expected, mean):
    active = REQUIRED_CRITERIA["C"]
    result = periodic_result(active, dict(zip(active, scores, strict=True)))
    assert result.outcome == expected
    assert result.mean == mean


def test_exact_threshold_not_positive():
    active = (*REQUIRED_CRITERIA["C"], uuid4())
    ratings = dict(zip(active, [3, 3, 3, 5, 5, 5], strict=True))
    assert periodic_result(active, ratings).mean == 4
    assert periodic_result(active, ratings).outcome == "negative"


def test_missing_rating_never_becomes_positive():
    active = REQUIRED_CRITERIA["C"]
    assert periodic_result(active, {active[0]: 9}).outcome == "incomplete"
    assert periodic_result(active, {}).mean is None


@pytest.mark.parametrize("invalid", [0, 2, 10, True, "5", 5.0])
def test_invalid_periodic_scores(invalid):
    active = REQUIRED_CRITERIA["C"]
    with pytest.raises(ValueError, match="score"):
        periodic_result(active, {active[0]: invalid})


def test_periodic_rejects_inactive_criterion():
    with pytest.raises(ValueError, match="active"):
        periodic_result(REQUIRED_CRITERIA["C"], {uuid4(): 9})


@pytest.mark.parametrize(
    "observations,expected",
    [
        ([], None),
        ([None, None], None),
        ([None, 2], 5),
        ([0, 4], 5),
        ([0, 1], 1),
        ([2, 3], 5),
        ([4], 9),
    ],
)
def test_behavioral_suggestion(observations, expected):
    suggestion = suggest_score(observations)
    assert suggestion.score == expected
    assert suggestion.policy_version == SUGGESTION_POLICY


@pytest.mark.parametrize("invalid", [-1, 5, True, "2"])
def test_invalid_behavioral_level(invalid):
    with pytest.raises(ValueError):
        suggest_score([invalid])


@pytest.mark.parametrize(
    "scores,report,exam,basis,outcome",
    [
        ([5] * 5, True, "passed", None, "positive"),
        ([3, 5, 5, 5, 7], True, "passed", None, "positive"),
        ([3, 3, 7, 7, 7], True, "passed", None, "negative"),
        ([3, 5, 5, 5, 5], True, "passed", None, "negative"),
        ([7] * 5, False, "passed", None, "negative"),
        ([7] * 5, True, "failed", None, "negative"),
        ([5] * 5, True, "not_applicable", "Verified legal exemption", "positive"),
        ([5] * 5, None, "passed", None, "incomplete"),
        ([5] * 5, True, None, None, "incomplete"),
        ([None, 5, 5, 5, 5], True, "passed", None, "incomplete"),
    ],
)
def test_first_result(scores, report, exam, basis, outcome):
    result = first_result(scores, report, exam, basis)
    assert result.outcome == outcome
    assert (result.mean is None) == (outcome == "incomplete")


def test_exam_exemption_requires_basis():
    with pytest.raises(ValueError, match="basis"):
        first_result([5] * 5, True, "not_applicable")


@pytest.mark.parametrize(
    "scores", [[5] * 4, [5] * 6, [1, 5, 5, 5, 5], [True, 5, 5, 5, 5]]
)
def test_first_rejects_invalid_elements(scores):
    with pytest.raises(ValueError):
        first_result(scores, True, "passed")
