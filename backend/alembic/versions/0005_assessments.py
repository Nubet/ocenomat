"""Persistent assessment identity, snapshots and idempotent creation."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "employee_id", sa.Uuid(), sa.ForeignKey("employees.id"), nullable=False
        ),
        sa.Column("assessor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "catalog_version_id",
            sa.Uuid(),
            sa.ForeignKey("catalog_versions.id"),
            nullable=False,
        ),
        sa.Column("employee_snapshot", JSONB(), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("form", sa.String(1), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "CRITERIA_AGREED",
                "IN_PROGRESS",
                "EVALUATION",
                "COMPLETED",
                name="assessmentstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("assessor_id", "idempotency_key"),
        sa.CheckConstraint("revision > 0"),
        sa.CheckConstraint("kind = 'periodic'"),
        sa.CheckConstraint("form = 'C'"),
    )
    op.create_index("ix_assessments_employee_id", "assessments", ["employee_id"])
    op.create_index("ix_assessments_assessor_id", "assessments", ["assessor_id"])


def downgrade() -> None:
    op.drop_table("assessments")
