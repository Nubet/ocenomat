"""Dated observations and the assessment conversation."""

import sqlalchemy as sa

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessment_observations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.Uuid(),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("criterion_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.String(10000), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id", "criterion_id"],
            ["assessment_criteria.assessment_id", "assessment_criteria.criterion_id"],
        ),
        sa.CheckConstraint("length(trim(text)) > 0"),
    )
    op.create_index(
        "ix_assessment_observations_assessment_id",
        "assessment_observations",
        ["assessment_id"],
    )
    op.create_table(
        "assessment_conversations",
        sa.Column(
            "assessment_id",
            sa.Uuid(),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("agenda", sa.String(10000), nullable=False),
        sa.Column("strengths", sa.String(10000), nullable=False),
        sa.Column("growth", sa.String(10000), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=True),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("assessment_conversations")
    op.drop_table("assessment_observations")
