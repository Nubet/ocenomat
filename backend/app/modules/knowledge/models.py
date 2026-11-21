from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    __table_args__ = (
        CheckConstraint(
            "original_sha256 ~ '^[0-9a-f]{64}$'", name="ck_knowledge_source_hash"
        ),
        CheckConstraint(
            "original_size BETWEEN 1 AND 10485760", name="ck_knowledge_source_size"
        ),
        CheckConstraint(
            "legal_status IN ('unknown', 'historical', 'verified_current')",
            name="ck_knowledge_legal_status",
        ),
        CheckConstraint(
            "verification_status IN "
            "('unverified', 'needs_review', 'approved', 'rejected')",
            name="ck_knowledge_source_status",
        ),
        CheckConstraint(
            "assessment_kind IN ('first', 'periodic', 'both')", name="ck_knowledge_kind"
        ),
        CheckConstraint(
            "parent_source_id IS NULL OR parent_source_id != source_id",
            name="ck_knowledge_parent",
        ),
    )

    source_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    source_type: Mapped[str] = mapped_column(String(40))
    assessment_kind: Mapped[str] = mapped_column(String(10))
    document_version: Mapped[str] = mapped_column(String(100))
    original_path: Mapped[str] = mapped_column(Text)
    original_filename: Mapped[str] = mapped_column(String(255))
    original_sha256: Mapped[str] = mapped_column(String(64))
    original_size: Mapped[int]
    media_type: Mapped[str] = mapped_column(String(128))
    storage_key: Mapped[str] = mapped_column(Text, unique=True)
    extractor_version: Mapped[str] = mapped_column(String(40))
    extraction_sha256: Mapped[str] = mapped_column(String(64))
    parent_source_id: Mapped[str | None] = mapped_column(
        ForeignKey("knowledge_sources.source_id")
    )
    legal_status: Mapped[str] = mapped_column(String(30))
    verification_status: Mapped[str] = mapped_column(String(20), default="needs_review")
    warnings: Mapped[list] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("source_id", "chunk_index", name="uq_knowledge_chunk_index"),
        UniqueConstraint("source_id", "locator", name="uq_knowledge_chunk_locator"),
        CheckConstraint(
            "chunk_index >= 0 AND (page IS NULL OR page > 0)",
            name="ck_knowledge_chunk_location",
        ),
        CheckConstraint(
            "char_length(content) BETWEEN 1 AND 100000",
            name="ck_knowledge_chunk_content",
        ),
        CheckConstraint(
            "content_sha256 ~ '^[0-9a-f]{64}$'", name="ck_knowledge_chunk_hash"
        ),
        CheckConstraint(
            "verification_status IN "
            "('unverified', 'needs_review', 'approved', 'rejected')",
            name="ck_knowledge_chunk_status",
        ),
        CheckConstraint(
            "verification_status NOT IN ('approved', 'rejected') OR review IS NOT NULL",
            name="ck_knowledge_chunk_review",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("knowledge_sources.source_id"))
    chunk_index: Mapped[int]
    locator: Mapped[str] = mapped_column(String(500))
    page: Mapped[int | None]
    content: Mapped[str] = mapped_column(Text)
    content_sha256: Mapped[str] = mapped_column(String(64))
    verification_status: Mapped[str] = mapped_column(String(20), default="needs_review")
    warnings: Mapped[list] = mapped_column(JSONB)
    review: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
