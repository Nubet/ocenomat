"""Employees, organizational units and manager assignments."""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizational_units",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.CheckConstraint("length(trim(name)) > 0"),
    )
    op.create_table(
        "employees",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("position", sa.String(200), nullable=False),
        sa.Column(
            "position_kind",
            sa.Enum(
                "OFFICE_HEAD",
                "DIRECT_MANAGER",
                "OTHER",
                name="positionkind",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "unit_id",
            sa.Uuid(),
            sa.ForeignKey("organizational_units.id"),
            nullable=False,
        ),
        sa.CheckConstraint("length(trim(name)) > 0"),
        sa.CheckConstraint("length(trim(position)) > 0"),
    )
    op.create_table(
        "manager_employee_assignments",
        sa.Column(
            "manager_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "employee_id",
            sa.Uuid(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_index(
        "ix_manager_employee_assignments_employee_id",
        "manager_employee_assignments",
        ["employee_id"],
    )


def downgrade() -> None:
    op.drop_table("manager_employee_assignments")
    op.drop_table("employees")
    op.drop_table("organizational_units")
