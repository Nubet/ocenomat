"""Versioned job descriptions and immutable generated documents."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("documents_kind_check", "documents", type_="check")
    op.create_check_constraint(
        "ck_document_kind", "documents", "kind IN ('attachment', 'osp', 'periodic_pdf')"
    )
    op.add_column("documents", sa.Column("template_version", sa.String(100)))
    op.add_column("documents", sa.Column("assessment_revision", sa.Integer()))
    op.add_column("documents", sa.Column("generation_data", postgresql.JSONB()))
    op.create_check_constraint(
        "ck_document_generation",
        "documents",
        "(kind = 'periodic_pdf' AND template_version IS NOT NULL AND "
        "assessment_revision IS NOT NULL AND assessment_revision > 0 "
        "AND generation_data IS NOT NULL) OR "
        "(kind != 'periodic_pdf' AND template_version IS NULL AND "
        "assessment_revision IS NULL AND generation_data IS NULL)",
    )
    op.create_unique_constraint(
        "uq_document_generation",
        "documents",
        ["assessment_id", "assessment_revision", "template_version"],
    )
    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "employee_id", sa.Uuid(), sa.ForeignKey("employees.id"), nullable=False
        ),
        sa.Column(
            "document_id",
            sa.Uuid(),
            sa.ForeignKey("documents.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("employee_id", "version"),
        sa.CheckConstraint("version > 0"),
    )
    op.create_index(
        "ix_job_descriptions_employee_id", "job_descriptions", ["employee_id"]
    )
    op.add_column(
        "assessments",
        sa.Column(
            "job_description_id",
            sa.Uuid(),
            sa.ForeignKey("job_descriptions.id", name="fk_assessment_job_description"),
        ),
    )


def downgrade() -> None:
    # Retain metadata rather than silently discard new document kinds on rollback.
    connection = op.get_bind()
    if connection.scalar(
        sa.text("SELECT EXISTS (SELECT 1 FROM documents WHERE kind != 'attachment')")
    ):
        raise RuntimeError("Cannot downgrade while OSP or generated documents exist")
    op.drop_column("assessments", "job_description_id")
    op.drop_table("job_descriptions")
    op.drop_constraint("uq_document_generation", "documents", type_="unique")
    op.drop_constraint("ck_document_generation", "documents", type_="check")
    for column in ("generation_data", "assessment_revision", "template_version"):
        op.drop_column("documents", column)
    op.drop_constraint("ck_document_kind", "documents", type_="check")
    op.create_check_constraint(
        "documents_kind_check", "documents", "kind = 'attachment'"
    )
