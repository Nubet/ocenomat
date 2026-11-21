"""Indicator answers and manually confirmed criterion ratings."""

import sqlalchemy as sa

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "criterion_ratings",
        sa.Column(
            "assessment_id",
            sa.Uuid(),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("criterion_id", sa.Uuid(), primary_key=True),
        sa.Column("suggested_score", sa.Integer(), nullable=True),
        sa.Column("policy_version", sa.String(80), nullable=False),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("confirmed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["assessment_id", "criterion_id"],
            ["assessment_criteria.assessment_id", "assessment_criteria.criterion_id"],
        ),
        sa.CheckConstraint("suggested_score IN (1, 3, 5, 7, 9)"),
        sa.CheckConstraint("score IN (1, 3, 5, 7, 9)"),
        sa.CheckConstraint(
            "(score IS NULL AND confirmed_by IS NULL AND confirmed_at IS NULL) OR "
            "(score IS NOT NULL AND confirmed_by IS NOT NULL "
            "AND confirmed_at IS NOT NULL)"
        ),
    )
    op.create_table(
        "indicator_answers",
        sa.Column("assessment_id", sa.Uuid(), primary_key=True),
        sa.Column("criterion_id", sa.Uuid(), primary_key=True),
        sa.Column("indicator_id", sa.Uuid(), primary_key=True),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(4000), nullable=False),
        sa.ForeignKeyConstraint(
            ["assessment_id", "criterion_id"],
            ["criterion_ratings.assessment_id", "criterion_ratings.criterion_id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("level BETWEEN 0 AND 4"),
    )


def downgrade() -> None:
    op.drop_table("indicator_answers")
    op.drop_table("criterion_ratings")
