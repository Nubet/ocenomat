from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
        CheckConstraint(
            "date_assessment >= date_talk", name="ck_assessments_date_order"
        ),
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
    date_talk: Mapped[date | None] = mapped_column(Date)
    date_assessment: Mapped[date | None] = mapped_column(Date)
    duties_discussed: Mapped[bool] = mapped_column(
        default=False, server_default="false"
    )
    expectations_discussed: Mapped[bool] = mapped_column(
        default=False, server_default="false"
    )
    arrangements_shared: Mapped[bool] = mapped_column(
        default=False, server_default="false"
    )
    criteria: Mapped[list["AssessmentCriterion"]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="AssessmentCriterion.criterion_id",
    )


class AssessmentCriterion(Base):
    __tablename__ = "assessment_criteria"
    __table_args__ = (
        CheckConstraint(
            "(required AND justification IS NULL) OR "
            "(NOT required AND length(trim(justification)) > 0 "
            "AND justification IS NOT NULL)"
        ),
    )

    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True
    )
    criterion_id: Mapped[UUID] = mapped_column(primary_key=True)
    required: Mapped[bool] = mapped_column()
    justification: Mapped[str | None] = mapped_column(String(4000))


class AssessmentEvent(Base):
    __tablename__ = "assessment_events"
    __table_args__ = (
        UniqueConstraint("assessment_id", "revision"),
        CheckConstraint("revision > 0"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE")
    )
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    revision: Mapped[int] = mapped_column()
    kind: Mapped[str] = mapped_column(String(40))
    occurred_on: Mapped[date | None] = mapped_column(Date)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
