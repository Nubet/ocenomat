"""Allow manager form B without changing existing assessment snapshots."""

from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("assessments_form_check", "assessments", type_="check")
    op.create_check_constraint(
        "ck_assessments_form", "assessments", "form IN ('B', 'C')"
    )


def downgrade() -> None:
    # Existing B records must block rollback rather than be rewritten as C.
    op.drop_constraint("ck_assessments_form", "assessments", type_="check")
    op.create_check_constraint("assessments_form_check", "assessments", "form = 'C'")
