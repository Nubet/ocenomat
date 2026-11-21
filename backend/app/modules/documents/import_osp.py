"""Explicit operator import of a source OSP for an assigned employee."""

import argparse
import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.database import create_database_engine
from app.integrations.storage import ObjectStorage
from app.modules.assessments.service import AssessmentError
from app.modules.documents.models import Document, JobDescription
from app.modules.documents.service import (
    discard_uncommitted_object,
    record_job_description,
)
from app.modules.documents.validation import (
    MAX_FILE_SIZE,
    validate_content,
    validate_filename,
)
from app.modules.employees.models import ManagerEmployeeAssignment
from app.modules.users.models import Role, User


def import_osp(
    session: Session, user: User, employee_id: UUID, path: Path, storage: ObjectStorage
) -> JobDescription:
    document_id = uuid4()
    key = f"job-descriptions/{employee_id}/{document_id}"
    attempted = False
    commit_pending = False
    try:
        assignment = session.scalar(
            select(ManagerEmployeeAssignment)
            .where(
                ManagerEmployeeAssignment.manager_id == user.id,
                ManagerEmployeeAssignment.employee_id == employee_id,
            )
            .with_for_update()
        )
        if (
            not user.active
            or Role.MANAGER not in {role.role for role in user.roles}
            or assignment is None
        ):
            raise AssessmentError("not_found", "Assigned employee not found")
        filename = validate_filename(path.name)
        with path.open("rb") as source:
            content = source.read(MAX_FILE_SIZE + 1)
        media_type = validate_content(content, filename, "application/octet-stream")
        digest = hashlib.sha256(content).hexdigest()
        previous = session.scalar(
            select(JobDescription)
            .where(JobDescription.employee_id == employee_id)
            .order_by(JobDescription.version.desc())
            .limit(1)
        )
        if (
            previous is not None
            and previous.document.sha256 == digest
            and previous.document.filename == filename
        ):
            session.commit()
            return previous
        document = Document(
            id=document_id,
            kind="osp",
            filename=filename,
            media_type=media_type,
            size=len(content),
            sha256=digest,
            object_key=key,
            author_id=user.id,
        )
        attempted = True
        storage.put(key, content, media_type)
        session.add(document)
        session.flush()
        result = record_job_description(session, employee_id, document)
        commit_pending = True
        session.commit()
        return result
    except Exception:
        session.rollback()
        if attempted:
            discard_uncommitted_object(
                session, document_id, key, storage, commit_pending
            )
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--employee-id", required=True, type=UUID)
    parser.add_argument("--author-subject", required=True, type=UUID)
    args = parser.parse_args()
    settings = Settings()
    engine = create_database_engine(settings)
    storage = ObjectStorage(settings)
    try:
        with Session(engine) as session:
            user = session.scalar(
                select(User).where(User.auth_subject == args.author_subject)
            )
            if user is None:
                raise ValueError("Author not found")
            result = import_osp(session, user, args.employee_id, args.path, storage)
            print(
                f"OSP {result.id}, version {result.version}, "
                f"employee {result.employee_id}"
            )
    except Exception:
        raise SystemExit(
            "OSP import failed; verify source, assignment and dependencies"
        ) from None
    finally:
        storage.close()
        engine.dispose()


if __name__ == "__main__":
    main()
