"""Separate first-assessment data and deadline history; preserve periodic records."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("assessments_kind_check", "assessments", type_="check")
    op.drop_constraint("ck_assessments_form", "assessments", type_="check")
    op.create_check_constraint(
        "ck_assessments_form",
        "assessments",
        "(kind = 'periodic' AND form IN ('B', 'C')) OR (kind = 'first' AND form = 'P')",
    )
    op.create_table(
        "first_assessments",
        sa.Column(
            "assessment_id",
            sa.Uuid(),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        *[
            sa.Column(name, sa.Date(), nullable=False)
            for name in ("hired_on", "contract_end")
        ],
        sa.Column("employment_basis", sa.String(20), nullable=False),
        sa.Column("qualification_basis", sa.String(4000), nullable=False),
        *[
            sa.Column(name, sa.Boolean(), nullable=False)
            for name in (
                "eligibility_confirmed",
                "ksap_graduate",
                "nomination_requested",
                "intro_confirmed",
                "arrangements_shared",
                "report_missing",
                "conversation_confirmed",
                "unit_head_agreed",
            )
        ],
        *[
            sa.Column(name, sa.Date())
            for name in (
                "replacement_agreed_on",
                "intro_on",
                "report_from",
                "report_to",
                "report_period_from",
                "report_period_to",
                "report_submitted_on",
                "conversation_on",
                "assessed_on",
            )
        ],
        *[
            sa.Column(name, sa.String(10000), nullable=False)
            for name in (
                "report_tasks",
                "report_problems",
                "report_learning",
                "report_conclusions",
                "exam_basis",
                "conversation_notes",
                "justification",
                "development_conclusions",
                "unit_head_name",
                "unit_head_position",
            )
        ],
        sa.Column("exam", sa.String(20)),
        sa.Column("scores", postgresql.JSONB(), nullable=False),
        sa.CheckConstraint("employment_basis IN ('first_contract', 'replacement')"),
        sa.CheckConstraint("eligibility_confirmed"),
        sa.CheckConstraint("NOT (ksap_graduate AND nomination_requested)"),
        sa.CheckConstraint("contract_end > hired_on"),
        sa.CheckConstraint("report_to >= report_from"),
        sa.CheckConstraint("exam IN ('passed', 'failed', 'not_applicable')"),
        sa.CheckConstraint("NOT report_missing OR report_submitted_on IS NULL"),
    )
    op.create_table(
        "first_deadline_changes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "assessment_id", sa.Uuid(), sa.ForeignKey("assessments.id"), nullable=False
        ),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("reason", sa.String(30), nullable=False),
        sa.Column("basis", sa.String(4000), nullable=False),
        *[
            sa.Column(name, sa.Date(), nullable=False)
            for name in (
                "circumstance_from",
                "circumstance_to",
                "previous_contract_end",
                "previous_report_from",
                "previous_report_to",
                "contract_end",
                "report_from",
                "report_to",
                "notified_on",
            )
        ],
        sa.UniqueConstraint("assessment_id", "revision"),
        sa.CheckConstraint(
            "reason IN ('justified_absence', 'outside_workplace', 'contract_extension')"
        ),
        sa.CheckConstraint("circumstance_to >= circumstance_from"),
        sa.CheckConstraint("length(trim(basis)) > 0"),
    )
    op.create_index(
        "ix_first_deadline_changes_assessment_id",
        "first_deadline_changes",
        ["assessment_id"],
    )
    op.drop_constraint("ck_document_kind", "documents", type_="check")
    op.create_check_constraint(
        "ck_document_kind",
        "documents",
        "kind IN ('attachment', 'osp', 'periodic_pdf', 'first_pdf')",
    )
    op.drop_constraint("ck_document_generation", "documents", type_="check")
    op.create_check_constraint(
        "ck_document_generation",
        "documents",
        "(kind IN ('periodic_pdf', 'first_pdf') AND template_version IS NOT NULL AND "
        "assessment_revision IS NOT NULL AND assessment_revision > 0 "
        "AND generation_data IS NOT NULL) OR "
        "(kind NOT IN ('periodic_pdf', 'first_pdf') AND template_version IS NULL "
        "AND assessment_revision IS NULL AND generation_data IS NULL)",
    )


def downgrade() -> None:
    # The CHECK blocks rollback with existing first assessments before dropping data.
    op.create_check_constraint(
        "assessments_kind_check", "assessments", "kind = 'periodic'"
    )
    op.drop_constraint("ck_document_kind", "documents", type_="check")
    op.create_check_constraint(
        "ck_document_kind", "documents", "kind IN ('attachment', 'osp', 'periodic_pdf')"
    )
    op.drop_constraint("ck_document_generation", "documents", type_="check")
    op.create_check_constraint(
        "ck_document_generation",
        "documents",
        "(kind = 'periodic_pdf' AND template_version IS NOT NULL "
        "AND assessment_revision IS NOT NULL "
        "AND assessment_revision > 0 AND generation_data IS NOT NULL) OR "
        "(kind != 'periodic_pdf' AND template_version IS NULL "
        "AND assessment_revision IS NULL AND generation_data IS NULL)",
    )
    op.drop_constraint("ck_assessments_form", "assessments", type_="check")
    op.create_check_constraint(
        "ck_assessments_form", "assessments", "form IN ('B', 'C')"
    )
    op.drop_table("first_deadline_changes")
    op.drop_table("first_assessments")
