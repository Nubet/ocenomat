"""Index the original fragment text without modifying source or review records."""

import sqlalchemy as sa

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_knowledge_chunks_search",
            "knowledge_chunks",
            [
                sa.text(
                    "to_tsvector('simple'::regconfig, "
                    "translate(lower(content), 'ąćęłńóśźż', 'acelnoszz'))"
                )
            ],
            postgresql_using="gin",
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index("ix_knowledge_chunks_search", postgresql_concurrently=True)
