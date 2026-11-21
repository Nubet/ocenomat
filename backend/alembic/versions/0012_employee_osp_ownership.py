"""OSP sources belong to employees independently of an assessment."""

import sqlalchemy as sa

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "documents", "assessment_id", existing_type=sa.Uuid(), nullable=True
    )
    op.execute("UPDATE documents SET assessment_id = NULL WHERE kind = 'osp'")
    op.create_check_constraint(
        "ck_document_owner",
        "documents",
        "(kind = 'osp' AND assessment_id IS NULL) OR "
        "(kind != 'osp' AND assessment_id IS NOT NULL)",
    )


def downgrade() -> None:
    if op.get_bind().scalar(
        sa.text("SELECT EXISTS (SELECT 1 FROM documents WHERE kind = 'osp')")
    ):
        raise RuntimeError("Cannot downgrade while employee OSP sources exist")
    op.drop_constraint("ck_document_owner", "documents", type_="check")
    op.alter_column(
        "documents", "assessment_id", existing_type=sa.Uuid(), nullable=False
    )
