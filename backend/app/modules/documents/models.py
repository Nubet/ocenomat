from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("size BETWEEN 1 AND 10485760"),
        CheckConstraint(
            "kind IN ('attachment', 'osp', 'periodic_pdf')", name="ck_document_kind"
        ),
        CheckConstraint(
            "(kind = 'periodic_pdf' AND template_version IS NOT NULL AND "
            "assessment_revision IS NOT NULL AND assessment_revision > 0 "
            "AND generation_data IS NOT NULL) OR "
            "(kind != 'periodic_pdf' AND template_version IS NULL AND "
            "assessment_revision IS NULL AND generation_data IS NULL)",
            name="ck_document_generation",
        ),
        UniqueConstraint(
            "assessment_id",
            "assessment_revision",
            "template_version",
            name="uq_document_generation",
        ),
        CheckConstraint("length(filename) BETWEEN 1 AND 255"),
        CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'"),
        CheckConstraint(
            "(kind = 'osp' AND assessment_id IS NULL) OR "
            "(kind != 'osp' AND assessment_id IS NOT NULL)",
            name="ck_document_owner",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    assessment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("assessments.id"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20), default="attachment")
    filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column()
    sha256: Mapped[str] = mapped_column(String(64))
    object_key: Mapped[str] = mapped_column(String(150), unique=True)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    template_version: Mapped[str | None] = mapped_column(String(100))
    assessment_revision: Mapped[int | None] = mapped_column()
    generation_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    __table_args__ = (
        UniqueConstraint("employee_id", "version"),
        CheckConstraint("version > 0"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id"), index=True)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"), unique=True)
    version: Mapped[int] = mapped_column()
    document: Mapped[Document] = relationship(lazy="joined")
