import hashlib
from uuid import uuid4

import pytest
from sqlalchemy import delete, event, func, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from test_assessments import assessment_access as assessment_access
from test_assessments import auth, create
from test_document_validation import docx_bytes, pdf_bytes

from app.integrations.storage import StorageUnavailable
from app.modules.assessments.models import Assessment, AssessmentEvent, AssessmentStatus
from app.modules.documents.models import Document
from app.modules.documents.validation import DOCX_TYPE, MAX_FILE_SIZE, PDF_TYPE
from app.modules.employees.models import ManagerEmployeeAssignment

pytestmark = pytest.mark.integration


class MemoryStorage:
    def __init__(self):
        self.objects = {}
        self.calls = []
        self.fail = set()

    def put(self, key, content, media_type):
        self.calls.append(("put", key))
        self.objects[key] = content
        if "put" in self.fail:
            raise StorageUnavailable("private connection details")

    def get(self, key, size):
        self.calls.append(("get", key))
        if "get" in self.fail or key not in self.objects:
            raise StorageUnavailable("private connection details")
        return self.objects[key]

    def delete(self, key):
        self.calls.append(("delete", key))
        if "delete" in self.fail:
            raise StorageUnavailable("private connection details")
        self.objects.pop(key, None)


@pytest.fixture
def documents(assessment_access):
    access = assessment_access
    assessment = create(access).json()
    access.path = f"/api/v1/assessments/{assessment['id']}"
    access.storage = MemoryStorage()
    access.client.app.state.object_storage = access.storage
    return access


def upload(
    access,
    *,
    revision=1,
    filename="Zażółć.pdf",
    content=None,
    name="a",
    media_type=PDF_TYPE,
    path=None,
):
    return access.client.post(
        (path or access.path) + "/documents",
        params={"revision": revision, "filename": filename},
        headers={**auth(access, name), "Content-Type": media_type},
        content=pdf_bytes() if content is None else content,
    )


def test_upload_metadata_list_download_and_retry(documents):
    access = documents
    content = pdf_bytes()
    response = upload(access, content=content)
    assert response.status_code == 201, response.text
    result = response.json()
    doc = result["document"]
    assert result["assessment_revision"] == 2
    assert doc["filename"] == "Zażółć.pdf" and doc["kind"] == "attachment"
    assert (
        doc["size"] == len(content)
        and doc["sha256"] == hashlib.sha256(content).hexdigest()
    )
    assert doc["author_id"] == str(access.users["a"].id) and doc["created_at"]
    assert "object_key" not in doc
    assert response.headers["cache-control"] == "private, no-store"
    for _ in range(2):
        listing = access.client.get(access.path + "/documents", headers=auth(access))
        assert listing.json() == [doc]
        assert listing.headers["cache-control"] == "private, no-store"
        download = access.client.get(
            f"{access.path}/documents/{doc['id']}/download", headers=auth(access)
        )
        assert (
            download.content == content and download.headers["content-type"] == PDF_TYPE
        )
        assert "%C5%BC" in download.headers["content-disposition"]
        assert download.headers["content-disposition"].startswith("attachment;")
        assert download.headers["x-content-type-options"] == "nosniff"
        assert download.headers["cache-control"] == "private, no-store"
    assert upload(access).status_code == 409
    assert len(access.storage.objects) == 1
    assert access.client.get(access.path, headers=auth(access)).json()["revision"] == 2
    events = access.session.scalars(select(AssessmentEvent)).all()
    assert len(events) == 1 and events[0].kind == "document_uploaded"


def test_docx_is_stored_as_docx(documents):
    access = documents
    response = upload(
        access, filename="Opis.docx", media_type=DOCX_TYPE, content=docx_bytes()
    )
    assert response.status_code == 201, response.text
    assert response.json()["document"]["media_type"] == DOCX_TYPE


@pytest.mark.parametrize("name", ["b", "hr", "admin", "none", "mixed"])
def test_other_roles_cannot_upload_list_or_download(documents, name):
    access = documents
    doc = upload(access).json()["document"]
    if name == "b":
        access.session.add(
            ManagerEmployeeAssignment(
                manager_id=access.users["b"].id, employee_id=access.employees[0]
            )
        )
        access.session.commit()
    access.storage.calls.clear()
    assert upload(access, name=name, revision=2).status_code == 404
    assert (
        access.client.get(
            access.path + "/documents", headers=auth(access, name)
        ).status_code
        == 404
    )
    assert (
        access.client.get(
            f"{access.path}/documents/{doc['id']}/download", headers=auth(access, name)
        ).status_code
        == 404
    )
    assert access.storage.calls == []


def test_revoked_assignment_and_other_assessment_id_do_not_grant_file_access(documents):
    access = documents
    doc = upload(access).json()["document"]
    other = create(access).json()
    assert (
        access.client.get(
            f"/api/v1/assessments/{other['id']}/documents/{doc['id']}/download",
            headers=auth(access),
        ).status_code
        == 404
    )
    access.session.execute(
        delete(ManagerEmployeeAssignment).where(
            ManagerEmployeeAssignment.manager_id == access.users["a"].id
        )
    )
    access.session.commit()
    access.storage.calls.clear()
    assert upload(access, revision=2).status_code == 404
    assert (
        access.client.get(access.path + "/documents", headers=auth(access)).status_code
        == 404
    )
    assert (
        access.client.get(
            f"{access.path}/documents/{doc['id']}/download", headers=auth(access)
        ).status_code
        == 404
    )
    assert access.storage.calls == []


def test_unauthenticated_and_unknown_resource_requests(documents):
    access = documents
    assert (
        access.client.post(
            access.path + "/documents",
            params={"revision": 1, "filename": "x.pdf"},
            content=b"x",
        ).status_code
        == 401
    )
    assert upload(access, path=f"/api/v1/assessments/{uuid4()}").status_code == 404
    assert (
        access.client.get(
            f"{access.path}/documents/{uuid4()}/download", headers=auth(access)
        ).status_code
        == 404
    )
    assert access.storage.calls == []


@pytest.mark.parametrize(
    "content,filename,media_type,expected",
    [
        (b"x" * (MAX_FILE_SIZE + 1), "x.pdf", PDF_TYPE, 413),
        (b"not pdf", "x.pdf", PDF_TYPE, 422),
        (pdf_bytes(), "../x.pdf", PDF_TYPE, 422),
        (pdf_bytes(), "x.pdf", "text/html", 422),
    ],
)
def test_invalid_upload_does_not_write_storage_or_database(
    documents, content, filename, media_type, expected
):
    access = documents
    response = upload(access, content=content, filename=filename, media_type=media_type)
    assert response.status_code == expected, response.text
    assert access.storage.calls == []
    assert access.session.scalar(select(func.count()).select_from(Document)) == 0
    assert access.client.get(access.path, headers=auth(access)).json()["revision"] == 1


@pytest.mark.parametrize("status", list(AssessmentStatus))
def test_upload_respects_assessment_lifecycle(documents, status):
    access = documents
    assessment = access.session.get(Assessment, access.path.rsplit("/", 1)[1])
    assessment.status = status
    access.session.commit()
    response = upload(access)
    if status == AssessmentStatus.COMPLETED:
        assert response.status_code == 409 and access.storage.calls == []
    else:
        assert response.status_code == 201, response.text


def test_existing_files_remain_readable_after_completion(documents):
    access = documents
    doc = upload(access).json()["document"]
    assessment = access.session.get(Assessment, doc["assessment_id"])
    assessment.status = AssessmentStatus.COMPLETED
    access.session.commit()
    assert access.client.get(
        access.path + "/documents", headers=auth(access)
    ).json() == [doc]
    assert (
        access.client.get(
            f"{access.path}/documents/{doc['id']}/download", headers=auth(access)
        ).content
        == pdf_bytes()
    )


def test_failed_storage_write_is_compensated_even_if_put_reached_storage(documents):
    access = documents
    access.storage.fail = {"put"}
    response = upload(access)
    assert response.status_code == 503 and "private connection" not in response.text
    assert access.storage.objects == {}
    assert [name for name, _ in access.storage.calls] == ["put", "delete"]
    assert access.client.get(access.path, headers=auth(access)).json()["revision"] == 1
    assert access.session.scalar(select(func.count()).select_from(Document)) == 0


@pytest.mark.parametrize("failed_model", [Document, AssessmentEvent])
def test_database_failure_rolls_back_and_removes_uploaded_object(
    documents, failed_model
):
    access = documents

    def fail(session, *_):
        if any(isinstance(row, failed_model) for row in session.new):
            raise IntegrityError(
                "private statement", {}, Exception("private database details")
            )

    event.listen(Session, "before_flush", fail)
    try:
        response = upload(access)
    finally:
        event.remove(Session, "before_flush", fail)
    assert response.status_code == 503 and "private" not in response.text
    assert access.storage.objects == {}
    assert access.client.get(access.path, headers=auth(access)).json()["revision"] == 1
    for model in (Document, AssessmentEvent):
        assert access.session.scalar(select(func.count()).select_from(model)) == 0


def test_cleanup_failure_records_only_generated_key_for_operator(documents, caplog):
    access = documents
    access.storage.fail = {"put", "delete"}
    assert upload(access).status_code == 503
    key = next(iter(access.storage.objects))
    assert f"Storage cleanup required for object {key}" in caplog.text
    assert "Zażółć" not in caplog.text and "private connection" not in caplog.text


def test_lost_commit_acknowledgement_never_deletes_committed_file(
    documents, monkeypatch
):
    access = documents
    commit = Session.commit

    def commit_then_disconnect(session):
        commit(session)
        raise OperationalError("COMMIT", {}, Exception("acknowledgement lost"))

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", commit_then_disconnect)
        assert upload(access).status_code == 503
    listing = access.client.get(access.path + "/documents", headers=auth(access)).json()
    assert len(listing) == 1 and len(access.storage.objects) == 1
    doc = listing[0]
    assert (
        access.client.get(
            f"{access.path}/documents/{doc['id']}/download", headers=auth(access)
        ).content
        == pdf_bytes()
    )
    assert access.client.get(access.path, headers=auth(access)).json()["revision"] == 2


def test_uncertain_commit_keeps_object_when_database_cannot_confirm_rollback(
    documents, monkeypatch, caplog
):
    access = documents
    commit = Session.commit
    get = Session.get

    def commit_then_disconnect(session):
        commit(session)
        raise OperationalError("COMMIT", {}, Exception("acknowledgement lost"))

    def unavailable(session, entity, *args, **kwargs):
        if entity is Document:
            raise OperationalError("SELECT", {}, Exception("database unavailable"))
        return get(session, entity, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", commit_then_disconnect)
        patch.setattr(Session, "get", unavailable)
        assert upload(access).status_code == 503
    assert len(access.storage.objects) == 1
    key = next(iter(access.storage.objects))
    assert f"Storage reconciliation required for object {key}" in caplog.text


@pytest.mark.parametrize("failure", ["get", "missing", "checksum", "unconfigured"])
def test_download_dependency_failures_do_not_return_partial_content(documents, failure):
    access = documents
    doc = upload(access).json()["document"]
    if failure == "get":
        access.storage.fail = {"get"}
    elif failure == "missing":
        access.storage.objects.clear()
    elif failure == "checksum":
        access.storage.objects[next(iter(access.storage.objects))] = b"corrupt"
    else:
        access.client.app.state.object_storage = None
    response = access.client.get(
        f"{access.path}/documents/{doc['id']}/download", headers=auth(access)
    )
    assert response.status_code == 503 and "private connection" not in response.text
    assert access.client.get(
        access.path + "/documents", headers=auth(access)
    ).json() == [doc]


def test_missing_configuration_never_falls_back_to_demo(documents):
    access = documents
    access.client.app.state.object_storage = None
    assert upload(access).status_code == 503
    assert upload(access, name="hr").status_code == 404
    assert (
        access.client.get(access.path + "/documents", headers=auth(access)).json() == []
    )
