"""Explicit, additive demo import through the normal assessment services."""

import argparse
from collections import Counter
from dataclasses import replace
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import NAMESPACE_URL, UUID, uuid5
from zoneinfo import ZoneInfo

from docx import Document as WordDocument
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_database_engine
from app.demo.data import PREVIOUS_PERIOD, TEAMS, Person, Team
from app.integrations.storage import ObjectStorage
from app.modules.assessments.completion import complete_assessment, save_summary
from app.modules.assessments.evaluation import confirm_rating, save_answers
from app.modules.assessments.first import save_first
from app.modules.assessments.first_rules import calendar_months, first_deadlines
from app.modules.assessments.first_schemas import (
    FirstData,
    FirstQualification,
    FirstUpdate,
)
from app.modules.assessments.models import Assessment
from app.modules.assessments.rules import REQUIRED_CRITERIA
from app.modules.assessments.schemas import (
    AdditionalCriterion,
    AnswersUpdate,
    AssessmentCreate,
    ConversationUpdate,
    CriteriaUpdate,
    DatesUpdate,
    IndicatorAnswerInput,
    ObservationCreate,
    RatingConfirm,
    SummaryUpdate,
)
from app.modules.assessments.service import (
    add_observation,
    agree_criteria,
    confirm_conversation,
    create_assessment,
    save_conversation,
    save_criteria,
    save_dates,
    start_period,
)
from app.modules.catalog.models import CatalogVersion
from app.modules.documents.import_osp import import_osp
from app.modules.documents.models import Document, JobDescription
from app.modules.documents.service import discard_uncommitted_object, upload_document
from app.modules.employees.models import (
    Employee,
    ManagerEmployeeAssignment,
    OrganizationalUnit,
    PositionKind,
)
from app.modules.employees.seed import UNIT_ID, UNIT_NAME
from app.modules.monitoring.service import send_reminder
from app.modules.users.models import Role, User

DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def demo_id(value: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"kompas:demo:v1:{value}")


def word_file(title: str, sections: dict[str, str]) -> bytes:
    document = WordDocument()
    document.add_heading(title, 0)
    for heading, content in sections.items():
        document.add_heading(heading, 1)
        document.add_paragraph(content)
    document.sections[0].footer.paragraphs[0].text = (
        "Scenariusz demonstracyjny — osoby i zdarzenia fikcyjne. "
        "Materiał nie jest dokumentem urzędowym Ministerstwa Cyfryzacji."
    )
    stream = BytesIO()
    document.save(stream)
    return stream.getvalue()


def job_sections(person: Person, team: Team, slot: int) -> dict[str, str]:
    return {
        "Stanowisko i komórka": (
            f"{person.position}\n{team.name}\nOsoba w scenariuszu: {person.name}"
        ),
        "Cel stanowiska": team.mission,
        "Główne zadanie i oczekiwany rezultat": person.task
        + " Rezultat: uzgodniony materiał z widoczną podstawą, "
        "właścicielem i terminem dalszego działania.",
        "Odpowiedzialność": (
            "Bezpośrednie kierowanie zespołem: planowanie, delegowanie, "
            "informacja zwrotna i nadzór nad realizacją zadań."
        )
        if slot == 0
        else (
            "Samodzielne prowadzenie powierzonych spraw; "
            "eskalacja wątpliwości i ryzyka opóźnienia do przełożonego. "
            "Stanowisko nie kieruje pracownikami."
        ),
        "Wiedza i umiejętności": team.knowledge,
        "Współpraca": (
            "Właściciele spraw w komórce, komórki merytoryczne "
            "i organizacyjne urzędu. Przekazywanie materiałów uprawnionym "
            "odbiorcom, utrzymywanie śladu uzgodnień."
        ),
        "Warunki i planowanie": (
            "Praca biurowa, zadania planowane w cyklu miesięcznym "
            "i kwartalnym, okresowe spiętrzenie terminów. "
            "Bez danych niejawnych w materiałach scenariusza."
        ),
    }


def attach(
    session: Session,
    manager: User,
    assessment: Assessment,
    storage: ObjectStorage,
    uploaded: list[tuple[UUID, str]],
    filename: str,
    sections: dict[str, str],
    *,
    kind: str = "attachment",
) -> None:
    result = upload_document(
        session,
        manager,
        assessment,
        assessment.revision,
        filename,
        DOCX_TYPE,
        word_file(
            "Opis stanowiska pracy" if kind == "osp" else "Notatka robocza", sections
        ),
        storage,
        kind=kind,
    )
    document = session.get(Document, result.document.id)
    uploaded.append((document.id, document.object_key))


def periodic_case(
    session: Session,
    manager: User,
    assessment: Assessment,
    person: Person,
    team: Team,
    slot: int,
    team_index: int,
    today: date,
    *,
    history: bool = False,
) -> None:
    catalog = session.get(CatalogVersion, assessment.catalog_version_id)
    required = set(REQUIRED_CRITERIA[assessment.form])
    additional = [
        item
        for item in catalog.criteria
        if item["name"] in team.additional and UUID(item["id"]) not in required
    ]
    save_criteria(
        session,
        manager,
        assessment.id,
        CriteriaUpdate(
            revision=assessment.revision,
            additional=[
                AdditionalCriterion(
                    criterion_id=UUID(item["id"]),
                    justification=f"{person.task} {team.mission}",
                )
                for item in additional
            ],
        ),
    )
    if history:
        due = calendar_months(today + timedelta(days=5 + team_index * 3), -24)
    elif slot in (0, 5):
        due = today - timedelta(days=15 + team_index * 2)
    elif slot == 1:
        due = today + timedelta(days=5 + team_index * 3)
    elif slot == 8:
        due = today - timedelta(days=7 + team_index)
    elif slot == 2:
        due = calendar_months(today, 8) + timedelta(days=team_index * 2)
    else:
        due = calendar_months(today - timedelta(days=14 + team_index), 24)
    opened = calendar_months(due, -24) + timedelta(days=14)
    save_dates(
        session,
        manager,
        assessment.id,
        DatesUpdate(
            revision=assessment.revision,
            date_talk=opened,
            date_assessment=due,
            duties_discussed=True,
            expectations_discussed=True,
            arrangements_shared=True,
        ),
    )
    if slot == 3 and not history:
        return
    agree_criteria(session, manager, assessment.id, assessment.revision)
    if slot == 4 and not history:
        return
    start_period(session, manager, assessment.id, assessment.revision)
    observed = min(today - timedelta(days=35), due - timedelta(days=35))
    cooperation = next(
        item
        for item in assessment.criteria
        if next(
            c["name"] for c in catalog.criteria if UUID(c["id"]) == item.criterion_id
        )
        == ("ZARZĄDZANIE LUDŹMI" if assessment.form == "B" else "WSPÓŁPRACA")
    )
    reliability = next(
        c
        for c in catalog.criteria
        if c["name"]
        == (
            "PODEJMOWANIE DECYZJI I ODPOWIEDZIALNOŚĆ"
            if assessment.form == "B"
            else "RZETELNOŚĆ"
        )
    )
    add_observation(
        session,
        manager,
        assessment.id,
        ObservationCreate(
            revision=assessment.revision,
            criterion_id=UUID(reliability["id"]),
            occurred_on=observed,
            text=person.evidence,
        ),
    )
    add_observation(
        session,
        manager,
        assessment.id,
        ObservationCreate(
            revision=assessment.revision,
            criterion_id=cooperation.criterion_id,
            occurred_on=observed + timedelta(days=7),
            text=(
                "Na przeglądzie zadania: "
                + person.task
                + " Omówiono zależności od innych osób "
                "i sposób przekazania rezultatu. Uzgodnione dalsze działanie: "
                + person.development
            ),
        ),
    )
    conversation_date = min(today - timedelta(days=3), due - timedelta(days=2))
    save_conversation(
        session,
        manager,
        assessment.id,
        ConversationUpdate(
            revision=assessment.revision,
            agenda=(
                f"Omówienie zadania: {person.task} "
                "Porównanie obserwacji i perspektywy pracownika; "
                "uzgodnienie kolejnego kroku rozwojowego."
            ),
            strengths=person.evidence,
            growth=person.development,
            occurred_on=conversation_date if history or slot in (0, 1, 5) else None,
        ),
    )
    if slot not in (0, 1, 5) and not history:
        return
    confirm_conversation(session, manager, assessment.id, assessment.revision)
    negative = team_index == 0 and slot == 5 and not history
    for index, selection in enumerate(assessment.criteria):
        criterion = next(
            c for c in catalog.criteria if UUID(c["id"]) == selection.criterion_id
        )
        # Leave decisions open for the jury in each current evaluation case.
        if slot == 1 and not history and index >= 3:
            break
        levels = (
            (1, 1, 1, 2)
            if negative
            else (2, 3, 2, 2)
            if history or slot == 5
            else (3, 2, 3, 3)
        )
        answers = [
            IndicatorAnswerInput(
                indicator_id=UUID(indicator["id"]),
                level=levels[i % len(levels)],
                note=(
                    f"Przykład z okresu: {person.evidence}\n"
                    f"Do omówienia przy decyzji: {person.development}"
                ),
            )
            for i, indicator in enumerate(criterion["indicators"])
        ]
        manager_override = (
            not history
            and team_index == 0
            and slot == 0
            and criterion["name"] == "ZARZĄDZANIE LUDŹMI"
        )
        if manager_override:
            answers[0].note += (
                " Przełożony wybiera 5 zamiast sugestii 7: podział zadań był skuteczny,"
                " ale nie utrwalono regularnego sprawdzania realizacji zaleceń."
            )
        save_answers(
            session,
            manager,
            assessment.id,
            selection.criterion_id,
            AnswersUpdate(revision=assessment.revision, answers=answers),
        )
        if slot != 1 or history or index < 2:
            rating = next(
                r
                for r in assessment.ratings
                if r.criterion_id == selection.criterion_id
            )
            confirm_rating(
                session,
                manager,
                assessment.id,
                selection.criterion_id,
                RatingConfirm(
                    revision=assessment.revision,
                    score=3
                    if negative
                    else 5
                    if manager_override
                    else rating.suggested_score,
                ),
            )
    save_summary(
        session,
        manager,
        assessment.id,
        SummaryUpdate(
            revision=assessment.revision,
            negative_justification=(
                f"{person.evidence} Oczekiwano weryfikacji źródeł przed przekazaniem "
                "i zgłaszania ryzyka przed terminem. Wsparcie opiekuna i dwa przeglądy "
                "nie przyniosły trwałej poprawy. "
                "Ocena dotyczy udokumentowanych zachowań w okresie, nie cech osoby."
            )
            if negative
            else "",
            development_conclusions=person.development,
        ),
    )
    if slot != 1 or history:
        complete_assessment(session, manager, assessment.id, assessment.revision)


def qualification(today: date, team_index: int, slot: int) -> FirstQualification:
    hired = (
        today - timedelta(days=7)
        if slot == 6 and team_index == 0
        else (
            calendar_months(today, -9)
            if slot == 7
            else calendar_months(today, -8)
            - timedelta(days=20 if team_index == 2 else 0)
        )
    )
    replacement = slot == 7 and team_index == 4
    return FirstQualification(
        hired_on=hired,
        contract_end=calendar_months(hired, 12),
        employment_basis="replacement" if replacement else "first_contract",
        eligibility_confirmed=True,
        qualification_basis=(
            "HR potwierdził kwalifikację do pierwszej oceny; "
            "sprawdzono brak wcześniejszej pozytywnej pierwszej oceny. "
            + (
                "Umowa na zastępstwo; strony uzgodniły przeprowadzenie pierwszej oceny."
                if replacement
                else "Pierwsza umowa na czas określony z art. 35 ust. 3."
            )
        ),
        ksap_graduate=slot == 7 and team_index == 1,
        nomination_requested=False,
        replacement_agreed_on=hired + timedelta(days=5) if replacement else None,
    )


def first_case(
    session: Session,
    manager: User,
    assessment: Assessment,
    person: Person,
    team: Team,
    slot: int,
    team_index: int,
    today: date,
) -> None:
    if slot == 6 and team_index == 0:
        return
    data = FirstData.model_validate(assessment.first)
    bounds = first_deadlines(
        data.hired_on, data.contract_end, data.replacement_agreed_on
    )
    data.intro_on = data.hired_on + timedelta(days=10)
    data.intro_confirmed = data.arrangements_shared = True
    data.report_from = (
        today - timedelta(days=25) if slot == 7 else bounds.assessment_from
    )
    data.report_to = (
        today - timedelta(days=10)
        if slot == 7
        else bounds.assessment_from + timedelta(days=14)
    )
    save_first(
        session,
        manager,
        assessment.id,
        FirstUpdate(
            revision=assessment.revision,
            data=data,
            action="confirm_introduction",
        ),
    )
    if slot == 6:
        return
    data.report_period_from = data.hired_on
    data.report_period_to = calendar_months(data.hired_on, 7) - timedelta(days=1)
    data.report_submitted_on = today - timedelta(days=12)
    data.report_tasks = (
        f"{person.task} {person.evidence} Pracę wykonywano z opiekunem; "
        "po przeglądzie powierzono samodzielne sprawdzenie kolejnej partii materiałów."
    )
    data.report_problems = (
        "Najwięcej trudności sprawiało ustalenie, które braki wymagają wyjaśnienia "
        "z właścicielem sprawy. Pomagały wspólne przeglądy "
        "i zapisywanie podstaw uzgodnień."
    )
    data.report_learning = (
        "Poznano zasady obiegu i akceptacji dokumentów. "
        f"Zakres wiedzy stosowanej w zadaniach: {team.knowledge} "
        "Wnioski z konsultacji z opiekunem wykorzystano przy kolejnym zadaniu."
    )
    data.report_conclusions = person.development
    exempt = data.ksap_graduate or data.employment_basis == "replacement"
    data.exam = (
        "not_applicable" if exempt else "failed" if team_index == 3 else "passed"
    )
    data.exam_basis = (
        (
            "Ukończenie KSAP w kształceniu stacjonarnym; "
            if data.ksap_graduate
            else "Zatrudnienie w celu zastępstwa nieobecnego pracownika; "
        )
        + "ustawowe wyłączenie obowiązku służby przygotowawczej "
        "potwierdzone przez HR, nie uznaniowe zwolnienie z jej odbywania."
        if exempt
        else f"Protokół komisji z {calendar_months(data.hired_on, 6)}; "
        + (
            "wynik negatywny mimo zakończenia służby przygotowawczej."
            if data.exam == "failed"
            else "egzamin zaliczony; nie utożsamiano go ze zwolnieniem "
            "z odbywania służby przygotowawczej."
        )
    )
    data.conversation_on = today - timedelta(days=8)
    data.conversation_confirmed = True
    data.conversation_notes = (
        f"Omówiono sprawozdanie i przykład: {person.evidence} "
        f"Uzgodniono: {person.development} Pracownik wskazał potrzebę "
        "dalszych konsultacji przy nietypowych sprawach."
    )
    save_first(
        session,
        manager,
        assessment.id,
        FirstUpdate(
            revision=assessment.revision,
            data=data,
            action="confirm_conversation",
        ),
    )
    data.assessed_on = today - timedelta(days=5)
    scores = (
        (5, 5, 5, 7, 5),
        (7, 7, 5, 7, 5),
        (5, 5, 5, 5, 5),
        (5, 5, 5, 5, 5),
        (5, 7, 5, 5, 7),
        (7, 5, 7, 5, 7),
    )
    data.scores = dict(zip(data.scores, scores[team_index], strict=True))
    data.justification = (
        (
            "Pomimo postępu w zadaniach i terminowego sprawozdania nie został "
            "spełniony warunek zdania egzaminu kończącego służbę przygotowawczą. "
            "Wynik pierwszej oceny ustalono "
            "odrębnie od ocen pięciu elementów."
        )
        if data.exam == "failed"
        else f"Terminowe sprawozdanie oraz obserwacje: {person.evidence} "
        "Potwierdzono samodzielną realizację powierzonych zadań w uzgodnionym zakresie."
    )
    data.development_conclusions = person.development
    data.unit_head_name = (
        "Elżbieta Wysocka",
        "Henryk Rogowski",
        "Barbara Lipińska",
        "Stefan Zięba",
        "Małgorzata Polak",
        "Leszek Czerwiński",
    )[team_index]
    data.unit_head_position = "Dyrektor komórki organizacyjnej"
    data.unit_head_agreed = team_index % 2 == 1
    save_first(
        session,
        manager,
        assessment.id,
        FirstUpdate(
            revision=assessment.revision,
            data=data,
            action="complete" if team_index % 2 == 1 else "save",
        ),
    )


def populate_demo(
    session: Session,
    manager_subject: UUID,
    storage: ObjectStorage,
    today: date,
    uploaded: list[tuple[UUID, str]],
) -> Counter:
    """Caller holds an outer transaction; service commits release only savepoints."""
    session.execute(text("SELECT pg_advisory_xact_lock(741302004)"))
    manager = session.scalar(select(User).where(User.auth_subject == manager_subject))
    if (
        manager is None
        or not manager.active
        or Role.MANAGER not in {r.role for r in manager.roles}
    ):
        raise ValueError("An existing active MANAGER is required")
    if session.scalar(select(CatalogVersion.id).limit(1)) is None:
        raise ValueError("Import the real competency catalog before loading demo cases")
    counts = Counter()
    for team_index, team in enumerate(TEAMS):
        unit_id = demo_id(f"unit:{team.slug}")
        if session.get(OrganizationalUnit, unit_id) is None:
            session.add(OrganizationalUnit(id=unit_id, name=team.name))
            session.flush()
        for slot, person in enumerate(team.people):
            slug = f"{team.slug}:{slot}"
            employee_id = demo_id(f"employee:{slug}")
            employee = session.get(Employee, employee_id)
            if employee is not None:
                if (
                    session.get(ManagerEmployeeAssignment, (manager.id, employee_id))
                    is None
                ):
                    raise ValueError(
                        "Existing demo belongs to another assignment; import refused"
                    )
                counts["preserved_employees"] += 1
                continue
            session.add(
                Employee(
                    id=employee_id,
                    name=person.name,
                    position=person.position,
                    position_kind=PositionKind.DIRECT_MANAGER
                    if slot == 0
                    else PositionKind.OTHER,
                    unit_id=unit_id,
                )
            )
            session.flush()
            session.add(
                ManagerEmployeeAssignment(
                    manager_id=manager.id, employee_id=employee_id
                )
            )
            session.flush()
            counts["created_employees"] += 1
            if slot == 9:
                continue
            is_first = slot in (6, 7)
            assessment, _ = create_assessment(
                session,
                manager,
                AssessmentCreate(
                    employee_id=employee_id,
                    kind="first" if is_first else "periodic",
                    qualification=qualification(today, team_index, slot)
                    if is_first
                    else None,
                ),
                demo_id(f"assessment:{slug}"),
            )
            attach(
                session,
                manager,
                assessment,
                storage,
                uploaded,
                f"OSP-{team.slug}-{slot + 1:02}.docx",
                job_sections(person, team, slot),
                kind="osp",
            )
            if slot in (0, 1, 5, 7):
                attach(
                    session,
                    manager,
                    assessment,
                    storage,
                    uploaded,
                    f"Material-do-rozmowy-{team.slug}-{slot + 1:02}.docx",
                    {
                        "Pracownik": person.name,
                        "Zakres zadania": person.task,
                        "Obserwacja do omówienia": person.evidence,
                        "Kolejne działanie rozwojowe": person.development,
                        "Status materiału": (
                            "Notatka robocza prowadzącego. Nie zastępuje sprawozdania "
                            "pracownika, protokołu egzaminu ani potwierdzenia rozmowy."
                        ),
                    },
                )
            if is_first:
                first_case(
                    session, manager, assessment, person, team, slot, team_index, today
                )
            else:
                periodic_case(
                    session, manager, assessment, person, team, slot, team_index, today
                )
            counts["created_assessments"] += 1
            if slot == 1:
                previous, _ = create_assessment(
                    session,
                    manager,
                    AssessmentCreate(
                        employee_id=employee_id,
                        kind="periodic",
                    ),
                    demo_id(f"assessment:history:{slug}"),
                )
                periodic_case(
                    session,
                    manager,
                    previous,
                    replace(
                        person,
                        evidence=PREVIOUS_PERIOD[team_index][0],
                        development=PREVIOUS_PERIOD[team_index][1],
                    ),
                    team,
                    1,
                    team_index,
                    today,
                    history=True,
                )
                counts["created_assessments"] += 1
    for team in TEAMS:
        employee_id = demo_id(f"employee:{team.slug}:9")
        if (
            session.scalar(
                select(JobDescription.id).where(
                    JobDescription.employee_id == employee_id,
                )
            )
            is None
        ):
            with TemporaryDirectory() as directory:
                path = Path(directory) / f"OSP-{team.slug}-10.docx"
                path.write_bytes(
                    word_file(
                        "Opis stanowiska pracy", job_sections(team.people[9], team, 9)
                    )
                )
                description = import_osp(session, manager, employee_id, path, storage)
                document = description.document
                uploaded.append((document.id, document.object_key))
    # Rename only the old seed's unit; preserve every employee, assessment and document.
    legacy = session.get(OrganizationalUnit, UNIT_ID)
    if legacy is not None and legacy.name == "Jednostka testowa — dane fikcyjne":
        legacy.name = UNIT_NAME
    hr = next(
        (
            u
            for u in session.scalars(select(User))
            if u.active and Role.HR in {r.role for r in u.roles}
        ),
        None,
    )
    if hr is not None:
        for team in TEAMS[:3]:
            assessment = session.scalar(
                select(Assessment).where(
                    Assessment.assessor_id == manager.id,
                    Assessment.idempotency_key == demo_id(f"assessment:{team.slug}:8"),
                )
            )
            send_reminder(
                session, hr, assessment.id, demo_id(f"reminder:{team.slug}:8")
            )
    session.flush()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load authored fictional jury scenarios; preserve existing work"
    )
    parser.add_argument("--manager-subject", type=UUID, required=True)
    parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=datetime.now(ZoneInfo("Europe/Warsaw")).date(),
    )
    args = parser.parse_args()
    settings = Settings()
    engine = create_database_engine(settings)
    storage = ObjectStorage(settings)
    uploaded: list[tuple[UUID, str]] = []
    try:
        storage.initialize_bucket()
        try:
            with engine.begin() as connection:
                with Session(
                    bind=connection, join_transaction_mode="create_savepoint"
                ) as session:
                    counts = populate_demo(
                        session, args.manager_subject, storage, args.as_of, uploaded
                    )
        except Exception:
            with Session(engine) as session:
                for document_id, key in uploaded:
                    discard_uncommitted_object(session, document_id, key, storage, True)
            raise
        print(
            f"Demo scenarios as of {args.as_of}: {dict(counts)}; "
            f"stored files: {len(uploaded)}"
        )
    finally:
        storage.close()
        engine.dispose()


if __name__ == "__main__":
    main()
