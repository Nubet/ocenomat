"""Persist explicitly delivered in-app HR reminders."""

import sqlalchemy as sa

from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessment_reminders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "assessment_id", sa.Uuid(), sa.ForeignKey("assessments.id"), nullable=False
        ),
        sa.Column("sender_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recipient_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("idempotency_key", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("sender_id", "idempotency_key"),
    )
    op.create_index(
        "ix_assessment_reminders_assessment_id",
        "assessment_reminders",
        ["assessment_id"],
    )
    op.create_index(
        "ix_assessment_reminders_recipient_id", "assessment_reminders", ["recipient_id"]
    )


def downgrade() -> None:
    if op.get_bind().scalar(
        sa.text("SELECT EXISTS (SELECT 1 FROM assessment_reminders)")
    ):
        raise RuntimeError("Cannot remove delivered reminder history")
    op.drop_table("assessment_reminders")
