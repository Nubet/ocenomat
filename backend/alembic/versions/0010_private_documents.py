"""Private assessment attachment metadata."""

import sqlalchemy as sa

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "assessment_id", sa.Uuid(), sa.ForeignKey("assessments.id"), nullable=False
        ),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("media_type", sa.String(100), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("object_key", sa.String(150), nullable=False, unique=True),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("size BETWEEN 1 AND 10485760"),
        sa.CheckConstraint("kind = 'attachment'"),
        sa.CheckConstraint("length(filename) BETWEEN 1 AND 255"),
        sa.CheckConstraint("sha256 ~ '^[0-9a-f]{64}$'"),
    )
    op.create_index("ix_documents_assessment_id", "documents", ["assessment_id"])


def downgrade() -> None:
    op.drop_table("documents")
