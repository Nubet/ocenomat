from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AssessmentStatus(StrEnum):
    DRAFT = "draft"
    CRITERIA_AGREED = "criteria_agreed"
    IN_PROGRESS = "in_progress"
    EVALUATION = "evaluation"
    COMPLETED = "completed"


class Assessment(Base):
    __tablename__ = "assessments"
    __table_args__ = (
        UniqueConstraint("assessor_id", "idempotency_key"),
        CheckConstraint("revision > 0"),
        CheckConstraint("kind = 'periodic'"),
        CheckConstraint("form = 'C'"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id"), index=True)
    assessor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    catalog_version_id: Mapped[UUID] = mapped_column(ForeignKey("catalog_versions.id"))
    employee_snapshot: Mapped[dict] = mapped_column(JSONB)
    kind: Mapped[str] = mapped_column(String(20))
    form: Mapped[str] = mapped_column(String(1))
    status: Mapped[AssessmentStatus] = mapped_column(
        Enum(AssessmentStatus, native_enum=False, create_constraint=True),
        default=AssessmentStatus.DRAFT,
    )
    revision: Mapped[int] = mapped_column(default=1)
    idempotency_key: Mapped[UUID] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
