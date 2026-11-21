"""Preserve source URLs and canonical representation mappings without backfill."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "knowledge_sources",
        sa.Column("provenance", postgresql.JSONB(none_as_null=True)),
    )


def downgrade() -> None:
    if op.get_bind().scalar(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM knowledge_sources "
            "WHERE provenance IS NOT NULL)"
        )
    ):
        raise RuntimeError(
            "Export provenance before downgrading; metadata must not be discarded"
        )
    op.drop_column("knowledge_sources", "provenance")
