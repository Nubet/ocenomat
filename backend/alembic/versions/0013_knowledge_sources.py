"""Immutable originals and explicitly reviewed knowledge fragments."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_sources",
        sa.Column("source_id", sa.String(100), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("assessment_kind", sa.String(10), nullable=False),
        sa.Column("document_version", sa.String(100), nullable=False),
        sa.Column("original_path", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("original_sha256", sa.String(64), nullable=False),
        sa.Column("original_size", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.String(128), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False, unique=True),
        sa.Column("extractor_version", sa.String(40), nullable=False),
        sa.Column("extraction_sha256", sa.String(64), nullable=False),
        sa.Column(
            "parent_source_id",
            sa.String(100),
            sa.ForeignKey("knowledge_sources.source_id"),
        ),
        sa.Column("legal_status", sa.String(30), nullable=False),
        sa.Column("verification_status", sa.String(20), nullable=False),
        sa.Column("warnings", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "original_sha256 ~ '^[0-9a-f]{64}$'", name="ck_knowledge_source_hash"
        ),
        sa.CheckConstraint(
            "original_size BETWEEN 1 AND 10485760", name="ck_knowledge_source_size"
        ),
        sa.CheckConstraint(
            "legal_status IN ('unknown', 'historical', 'verified_current')",
            name="ck_knowledge_legal_status",
        ),
        sa.CheckConstraint(
            "verification_status IN "
            "('unverified', 'needs_review', 'approved', 'rejected')",
            name="ck_knowledge_source_status",
        ),
        sa.CheckConstraint(
            "assessment_kind IN ('first', 'periodic', 'both')", name="ck_knowledge_kind"
        ),
        sa.CheckConstraint(
            "parent_source_id IS NULL OR parent_source_id != source_id",
            name="ck_knowledge_parent",
        ),
    )
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "source_id",
            sa.String(100),
            sa.ForeignKey("knowledge_sources.source_id"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("locator", sa.String(500), nullable=False),
        sa.Column("page", sa.Integer()),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("verification_status", sa.String(20), nullable=False),
        sa.Column("warnings", postgresql.JSONB(), nullable=False),
        sa.Column("review", postgresql.JSONB(none_as_null=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "source_id", "chunk_index", name="uq_knowledge_chunk_index"
        ),
        sa.UniqueConstraint("source_id", "locator", name="uq_knowledge_chunk_locator"),
        sa.CheckConstraint(
            "chunk_index >= 0 AND (page IS NULL OR page > 0)",
            name="ck_knowledge_chunk_location",
        ),
        sa.CheckConstraint(
            "char_length(content) BETWEEN 1 AND 100000",
            name="ck_knowledge_chunk_content",
        ),
        sa.CheckConstraint(
            "content_sha256 ~ '^[0-9a-f]{64}$'", name="ck_knowledge_chunk_hash"
        ),
        sa.CheckConstraint(
            "verification_status IN "
            "('unverified', 'needs_review', 'approved', 'rejected')",
            name="ck_knowledge_chunk_status",
        ),
        sa.CheckConstraint(
            "verification_status NOT IN ('approved', 'rejected') OR review IS NOT NULL",
            name="ck_knowledge_chunk_review",
        ),
    )


def downgrade() -> None:
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM knowledge_sources)")):
        raise RuntimeError("Cannot downgrade while knowledge sources exist")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_sources")
