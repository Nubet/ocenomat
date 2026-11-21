from collections import Counter
from datetime import date
from io import BytesIO
from uuid import uuid4

import pytest
from docx import Document as WordDocument
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_documents import MemoryStorage

from app.demo.data import TEAMS
from app.demo.seed import demo_id, populate_demo
from app.integrations.storage import StorageUnavailable
from app.modules.assessments.models import Assessment, AssessmentEvent, AssessmentStatus
from app.modules.assessments.schemas import AssessmentResponse
from app.modules.catalog.identifiers import stable_id
from app.modules.catalog.models import CatalogVersion
from app.modules.documents.models import Document, JobDescription
from app.modules.employees.models import Employee
from app.modules.monitoring.models import AssessmentReminder
from app.modules.monitoring.service import monitoring
from app.modules.users.models import Role, User, UserRole


@pytest.fixture
def demo_source(database):
    _, _, session = database
    manager = User(
        auth_subject=uuid4(),
        display_name="Demo manager",
        roles=[UserRole(role=Role.MANAGER)],
    )
    hr = User(
        auth_subject=uuid4(), display_name="Demo HR", roles=[UserRole(role=Role.HR)]
    )
    names = {
        "RZETELNOŚĆ",
        "KOMUNIKACJA",
        "WYKORZYSTYWANIE WIEDZY I DOSKONALENIE ZAWODOWE",
        "ORGANIZACJA PRACY i ORIENTACJA NA OSIĄGANIE CELÓW",
        "WSPÓŁPRACA",
        "ZARZĄDZANIE LUDŹMI",
        "PODEJMOWANIE DECYZJI I ODPOWIEDZIALNOŚĆ",
        *(name for team in TEAMS for name in team.additional),
    }
    session.add_all(
        [
            manager,
            hr,
            CatalogVersion(
                id=uuid4(),
                version="demo-test",
                source_name="Test fixture",
                source_sha256="1" * 64,
                criteria=[
                    {
                        "id": str(stable_id(name)),
                        "name": name,
                        "indicators": [
                            {
                                "id": str(uuid4()),
                                "description": "Observed behaviour",
                                "levels": [
                                    {
                                        "level": i,
                                        "name": str(i),
                                        "description": f"Behaviour level {i}",
                                    }
                                    for i in range(5)
                                ],
                            }
                            for _ in range(3)
                        ],
                    }
                    for name in sorted(names)
                ],
            ),
        ]
    )
    session.commit()
    return session, manager, hr


@pytest.mark.integration
def test_real_workflows_files_results_and_non_destructive_retry(demo_source):
    session, manager, hr = demo_source
    storage = MemoryStorage()
    uploaded = []
    today = date(2026, 11, 21)
    result = populate_demo(session, manager.auth_subject, storage, today, uploaded)
    assert result == {"created_employees": 60, "created_assessments": 60}
    processes = list(session.scalars(select(Assessment)))
    assert len(processes) == 60
    assert Counter(a.kind for a in processes) == {"periodic": 48, "first": 12}
    assert {a.form for a in processes} == {"B", "C", "P"}
    assert {a.status for a in processes} == set(AssessmentStatus)
    assert any(
        r.score != r.suggested_score and r.score is not None
        for a in processes
        for r in a.ratings
    )
    assert Counter(a.result.outcome for a in processes if a.status == "completed") == {
        "positive": 19,
        "negative": 2,
    }
    for assessment in processes:
        AssessmentResponse.model_validate(assessment)
        if assessment.status == "completed":
            assert assessment.summary.completed_by == manager.id
            assert assessment.result.outcome != "incomplete"
        assert (
            session.scalar(
                select(func.count())
                .select_from(AssessmentEvent)
                .where(
                    AssessmentEvent.assessment_id == assessment.id,
                )
            )
            == assessment.revision - 1
        )
    assert len(uploaded) == len(storage.objects) == 78
    assert session.scalar(select(func.count()).select_from(JobDescription)) == 54
    data = monitoring(session, manager, today, hr=False)
    assert len(data.reminders) == 3
    assert any(d.overdue for d in data.deadlines)
    assert any(d.due_soon and not d.overdue for d in data.deadlines)
    assert monitoring(session, hr, today, hr=True).total == 60
    assert monitoring(session, hr, today, hr=False).total == 0
    first = next(a for a in processes if a.kind == "first" and a.status == "completed")
    assert first.first.report_tasks and first.first.report_learning
    osp = session.get(JobDescription, first.job_description_id)
    document = session.get(Document, osp.document_id)
    word = WordDocument(BytesIO(storage.objects[document.object_key]))
    assert first.employee_snapshot["name"] in "\n".join(p.text for p in word.paragraphs)
    assert "fikcyjne" in word.sections[0].footer.paragraphs[0].text
    employee = session.get(Employee, demo_id("employee:cyber:3"))
    employee.position = "Stanowisko zmienione przez użytkownika"
    session.commit()
    fingerprint = {a.id: (a.revision, a.status) for a in processes}
    again = populate_demo(session, manager.auth_subject, storage, today, uploaded)
    assert again == {"preserved_employees": 60}
    assert {
        a.id: (a.revision, a.status) for a in session.scalars(select(Assessment))
    } == fingerprint
    assert employee.position == "Stanowisko zmienione przez użytkownika"
    assert len(uploaded) == len(storage.objects) == 78
    assert session.scalar(select(func.count()).select_from(AssessmentReminder)) == 3


@pytest.mark.integration
def test_wrong_role_is_rejected_before_inserting_people(demo_source):
    session, _, hr = demo_source
    with pytest.raises(ValueError, match="active MANAGER"):
        populate_demo(session, hr.auth_subject, MemoryStorage(), date(2026, 11, 21), [])
    assert session.scalar(select(func.count()).select_from(Employee)) == 0


@pytest.mark.integration
def test_storage_failure_rolls_back_the_import_despite_service_commits(demo_source):
    session, manager, _ = demo_source
    subject = manager.auth_subject
    storage = MemoryStorage()
    storage.fail.add("put")
    with pytest.raises(StorageUnavailable):
        with session.connection().begin_nested():
            with Session(
                bind=session.connection(), join_transaction_mode="create_savepoint"
            ) as importing:
                populate_demo(importing, subject, storage, date(2026, 11, 21), [])
    session.expire_all()
    assert session.scalar(select(func.count()).select_from(Employee)) == 0
    assert session.scalar(select(func.count()).select_from(Assessment)) == 0
    assert not storage.objects
