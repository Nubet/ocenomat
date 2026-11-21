"""Assessment summary and immutable completion result."""

import sqlalchemy as sa

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessment_summaries",
        sa.Column(
            "assessment_id",
            sa.Uuid(),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("negative_justification", sa.String(10000), nullable=False),
        sa.Column("development_conclusions", sa.String(10000), nullable=False),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outcome", sa.String(10), nullable=True),
        sa.Column("score_total", sa.Integer(), nullable=True),
        sa.Column("score_count", sa.Integer(), nullable=True),
        sa.Column("completed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("outcome IN ('positive', 'negative')"),
        sa.CheckConstraint("score_count BETWEEN 5 AND 8"),
        sa.CheckConstraint("score_total BETWEEN score_count AND 9 * score_count"),
        sa.CheckConstraint(
            "(outcome IS NULL AND score_total IS NULL AND score_count IS NULL "
            "AND completed_by IS NULL AND completed_at IS NULL) OR "
            "(outcome IS NOT NULL AND score_total IS NOT NULL "
            "AND score_count IS NOT NULL "
            "AND completed_by IS NOT NULL AND completed_at IS NOT NULL)"
        ),
        sa.CheckConstraint(
            "outcome != 'negative' OR length(trim(negative_justification)) > 0"
        ),
    )


def downgrade() -> None:
    op.drop_table("assessment_summaries")
