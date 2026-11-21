"""Assessment criteria, dates and recorded actions."""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assessments", sa.Column("date_talk", sa.Date(), nullable=True))
    op.add_column("assessments", sa.Column("date_assessment", sa.Date(), nullable=True))
    for name in ("duties_discussed", "expectations_discussed", "arrangements_shared"):
        op.add_column(
            "assessments",
            sa.Column(name, sa.Boolean(), server_default=sa.false(), nullable=False),
        )
    op.create_check_constraint(
        "ck_assessments_date_order", "assessments", "date_assessment >= date_talk"
    )
    op.create_table(
        "assessment_criteria",
        sa.Column(
            "assessment_id",
            sa.Uuid(),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("criterion_id", sa.Uuid(), primary_key=True),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("justification", sa.String(4000), nullable=True),
        sa.CheckConstraint(
            "(required AND justification IS NULL) OR "
            "(NOT required AND length(trim(justification)) > 0 "
            "AND justification IS NOT NULL)"
        ),
    )
    op.create_table(
        "assessment_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.Uuid(),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("assessment_id", "revision"),
        sa.CheckConstraint("revision > 0"),
    )


def downgrade() -> None:
    op.drop_table("assessment_events")
    op.drop_table("assessment_criteria")
    op.drop_constraint("ck_assessments_date_order", "assessments", type_="check")
    for name in (
        "arrangements_shared",
        "expectations_discussed",
        "duties_discussed",
        "date_assessment",
        "date_talk",
    ):
        op.drop_column("assessments", name)
