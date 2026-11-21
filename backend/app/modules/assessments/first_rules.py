from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

FIRST_ELEMENTS = {
    "reliability": "Rzetelność",
    "knowledge": "Wykorzystywanie wiedzy i doskonalenie zawodowe",
    "organization": "Organizacja pracy i orientacja na osiąganie celów",
    "communication": "Komunikacja",
    "cooperation": "Współpraca",
}


def calendar_months(value: date, months: int) -> date:
    year, month = divmod(value.year * 12 + value.month - 1 + months, 12)
    month += 1
    return date(year, month, min(value.day, monthrange(year, month)[1]))


@dataclass(frozen=True)
class FirstDeadlines:
    introduction_by: date
    assessment_from: date
    assessment_by: date


def first_deadlines(
    hired_on: date, contract_end: date, replacement_agreed_on: date | None = None
) -> FirstDeadlines:
    if hired_on < date(2015, 8, 27):
        raise ValueError("Employment predates the supported 2015 regulation")
    if replacement_agreed_on is not None and not (
        hired_on <= replacement_agreed_on <= contract_end
    ):
        raise ValueError("Replacement agreement must fall within employment")
    earliest = calendar_months(hired_on, 8)
    latest = calendar_months(contract_end, -1)
    if earliest > latest:
        raise ValueError("Contract leaves no statutory assessment window")
    return FirstDeadlines(
        (replacement_agreed_on or hired_on) + timedelta(days=21), earliest, latest
    )
