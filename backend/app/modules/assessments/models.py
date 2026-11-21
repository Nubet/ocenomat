from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
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
    observations: Mapped[list["AssessmentObservation"]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="(AssessmentObservation.occurred_on, "
        "AssessmentObservation.recorded_at, AssessmentObservation.id)",
    )
    conversation: Mapped["AssessmentConversation | None"] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    ratings: Mapped[list["CriterionRating"]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="CriterionRating.criterion_id",
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


class AssessmentObservation(Base):
    __tablename__ = "assessment_observations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["assessment_id", "criterion_id"],
            ["assessment_criteria.assessment_id", "assessment_criteria.criterion_id"],
        ),
        CheckConstraint("length(trim(text)) > 0"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), index=True
    )
    criterion_id: Mapped[UUID] = mapped_column()
    text: Mapped[str] = mapped_column(String(10000))
    occurred_on: Mapped[date] = mapped_column(Date)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AssessmentConversation(Base):
    __tablename__ = "assessment_conversations"

    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True
    )
    agenda: Mapped[str] = mapped_column(String(10000))
    strengths: Mapped[str] = mapped_column(String(10000))
    growth: Mapped[str] = mapped_column(String(10000))
    occurred_on: Mapped[date | None] = mapped_column(Date)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))


class CriterionRating(Base):
    __tablename__ = "criterion_ratings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["assessment_id", "criterion_id"],
            ["assessment_criteria.assessment_id", "assessment_criteria.criterion_id"],
        ),
        CheckConstraint("suggested_score IN (1, 3, 5, 7, 9)"),
        CheckConstraint("score IN (1, 3, 5, 7, 9)"),
        CheckConstraint(
            "(score IS NULL AND confirmed_by IS NULL AND confirmed_at IS NULL) OR "
            "(score IS NOT NULL AND confirmed_by IS NOT NULL "
            "AND confirmed_at IS NOT NULL)"
        ),
    )

    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True
    )
    criterion_id: Mapped[UUID] = mapped_column(primary_key=True)
    suggested_score: Mapped[int | None] = mapped_column()
    policy_version: Mapped[str] = mapped_column(String(80))
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    score: Mapped[int | None] = mapped_column()
    confirmed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    answers: Mapped[list["IndicatorAnswer"]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="IndicatorAnswer.indicator_id",
    )


class IndicatorAnswer(Base):
    __tablename__ = "indicator_answers"
    __table_args__ = (
        ForeignKeyConstraint(
            ["assessment_id", "criterion_id"],
            ["criterion_ratings.assessment_id", "criterion_ratings.criterion_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("level BETWEEN 0 AND 4"),
    )

    assessment_id: Mapped[UUID] = mapped_column(primary_key=True)
    criterion_id: Mapped[UUID] = mapped_column(primary_key=True)
    indicator_id: Mapped[UUID] = mapped_column(primary_key=True)
    level: Mapped[int | None] = mapped_column()
    note: Mapped[str] = mapped_column(String(4000))
