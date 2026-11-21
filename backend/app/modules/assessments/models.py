from datetime import date, datetime
from enum import StrEnum
from fractions import Fraction
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
from app.modules.assessments.rules import Result, first_result, periodic_result


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
        CheckConstraint(
            "(kind = 'periodic' AND form IN ('B', 'C')) OR "
            "(kind = 'first' AND form = 'P')",
            name="ck_assessments_form",
        ),
        CheckConstraint(
            "date_assessment >= date_talk", name="ck_assessments_date_order"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id"), index=True)
    assessor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    catalog_version_id: Mapped[UUID] = mapped_column(ForeignKey("catalog_versions.id"))
    job_description_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "job_descriptions.id", name="fk_assessment_job_description", use_alter=True
        )
    )
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
    summary: Mapped["AssessmentSummary | None"] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )
    first: Mapped["FirstAssessment | None"] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )
    first_deadline_changes: Mapped[list["FirstDeadlineChange"]] = relationship(
        lazy="selectin", order_by="FirstDeadlineChange.revision"
    )

    @property
    def result(self) -> Result:
        if self.kind == "first":
            if self.first is None:
                return Result("incomplete", None)
            details = self.first
            on_time = (
                details.report_from <= details.report_submitted_on <= details.report_to
                if details.report_submitted_on
                and details.report_from
                and details.report_to
                else False
                if details.report_missing
                else None
            )
            return first_result(
                list(details.scores.values()), on_time, details.exam, details.exam_basis
            )
        if self.summary is not None and self.summary.outcome is not None:
            return Result(
                self.summary.outcome,
                Fraction(self.summary.score_total, self.summary.score_count),
            )
        if len(self.criteria) < 5:
            return Result("incomplete", None)
        return periodic_result(
            [item.criterion_id for item in self.criteria],
            {item.criterion_id: item.score for item in self.ratings},
        )


class FirstAssessment(Base):
    __tablename__ = "first_assessments"
    __table_args__ = (
        CheckConstraint("employment_basis IN ('first_contract', 'replacement')"),
        CheckConstraint("eligibility_confirmed"),
        CheckConstraint("NOT (ksap_graduate AND nomination_requested)"),
        CheckConstraint("contract_end > hired_on"),
        CheckConstraint("report_to >= report_from"),
        CheckConstraint("exam IN ('passed', 'failed', 'not_applicable')"),
        CheckConstraint("NOT report_missing OR report_submitted_on IS NULL"),
    )

    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True
    )
    hired_on: Mapped[date] = mapped_column(Date)
    contract_end: Mapped[date] = mapped_column(Date)
    employment_basis: Mapped[str] = mapped_column(String(20))
    eligibility_confirmed: Mapped[bool] = mapped_column()
    qualification_basis: Mapped[str] = mapped_column(String(4000))
    ksap_graduate: Mapped[bool] = mapped_column()
    nomination_requested: Mapped[bool] = mapped_column()
    replacement_agreed_on: Mapped[date | None] = mapped_column(Date)
    intro_on: Mapped[date | None] = mapped_column(Date)
    intro_confirmed: Mapped[bool] = mapped_column(default=False)
    arrangements_shared: Mapped[bool] = mapped_column(default=False)
    report_from: Mapped[date | None] = mapped_column(Date)
    report_to: Mapped[date | None] = mapped_column(Date)
    report_period_from: Mapped[date | None] = mapped_column(Date)
    report_period_to: Mapped[date | None] = mapped_column(Date)
    report_submitted_on: Mapped[date | None] = mapped_column(Date)
    report_missing: Mapped[bool] = mapped_column(default=False)
    report_tasks: Mapped[str] = mapped_column(String(10000), default="")
    report_problems: Mapped[str] = mapped_column(String(10000), default="")
    report_learning: Mapped[str] = mapped_column(String(10000), default="")
    report_conclusions: Mapped[str] = mapped_column(String(10000), default="")
    exam: Mapped[str | None] = mapped_column(String(20))
    exam_basis: Mapped[str] = mapped_column(String(10000), default="")
    conversation_on: Mapped[date | None] = mapped_column(Date)
    conversation_notes: Mapped[str] = mapped_column(String(10000), default="")
    conversation_confirmed: Mapped[bool] = mapped_column(default=False)
    assessed_on: Mapped[date | None] = mapped_column(Date)
    scores: Mapped[dict] = mapped_column(JSONB)
    justification: Mapped[str] = mapped_column(String(10000), default="")
    development_conclusions: Mapped[str] = mapped_column(String(10000), default="")
    unit_head_name: Mapped[str] = mapped_column(String(10000), default="")
    unit_head_position: Mapped[str] = mapped_column(String(10000), default="")
    unit_head_agreed: Mapped[bool] = mapped_column(default=False)


class FirstDeadlineChange(Base):
    __tablename__ = "first_deadline_changes"
    __table_args__ = (
        UniqueConstraint("assessment_id", "revision"),
        CheckConstraint(
            "reason IN ('justified_absence', 'outside_workplace', 'contract_extension')"
        ),
        CheckConstraint("circumstance_to >= circumstance_from"),
        CheckConstraint("length(trim(basis)) > 0"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id"), index=True
    )
    revision: Mapped[int] = mapped_column()
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    reason: Mapped[str] = mapped_column(String(30))
    basis: Mapped[str] = mapped_column(String(4000))
    circumstance_from: Mapped[date] = mapped_column(Date)
    circumstance_to: Mapped[date] = mapped_column(Date)
    previous_contract_end: Mapped[date] = mapped_column(Date)
    previous_report_from: Mapped[date] = mapped_column(Date)
    previous_report_to: Mapped[date] = mapped_column(Date)
    contract_end: Mapped[date] = mapped_column(Date)
    report_from: Mapped[date] = mapped_column(Date)
    report_to: Mapped[date] = mapped_column(Date)
    notified_on: Mapped[date] = mapped_column(Date)


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


class AssessmentSummary(Base):
    __tablename__ = "assessment_summaries"
    __table_args__ = (
        CheckConstraint("outcome IN ('positive', 'negative')"),
        CheckConstraint("score_count BETWEEN 5 AND 8"),
        CheckConstraint("score_total BETWEEN score_count AND 9 * score_count"),
        CheckConstraint(
            "(outcome IS NULL AND score_total IS NULL AND score_count IS NULL "
            "AND completed_by IS NULL AND completed_at IS NULL) OR "
            "(outcome IS NOT NULL AND score_total IS NOT NULL "
            "AND score_count IS NOT NULL "
            "AND completed_by IS NOT NULL AND completed_at IS NOT NULL)"
        ),
        CheckConstraint(
            "outcome != 'negative' OR length(trim(negative_justification)) > 0"
        ),
    )

    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True
    )
    negative_justification: Mapped[str] = mapped_column(String(10000))
    development_conclusions: Mapped[str] = mapped_column(String(10000))
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str | None] = mapped_column(String(10))
    score_total: Mapped[int | None] = mapped_column()
    score_count: Mapped[int | None] = mapped_column()
    completed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
