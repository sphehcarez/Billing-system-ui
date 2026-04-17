"""Add line linkage, EDI artifacts, and richer PMB explainability fields.

Revision ID: 20260416_0003
Revises: 20260416_0002
Create Date: 2026-04-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "20260416_0003"
down_revision = "20260416_0002"
branch_labels = None
depends_on = None


def _table_names(inspector) -> set[str]:
    return set(inspector.get_table_names())


def _column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = _table_names(inspector)

    if "claim_line_items" not in table_names:
        op.create_table(
            "claim_line_items",
            sa.Column("claim_line_item_id", sa.String(length=120), primary_key=True),
            sa.Column("claim_id", sa.Integer(), sa.ForeignKey("claims.id"), nullable=False),
            sa.Column("claim_version", sa.Integer(), nullable=False),
            sa.Column("line_id", sa.String(length=120), nullable=False),
            sa.Column("service_code", sa.String(length=120), nullable=False),
            sa.Column("service_description", sa.Text(), nullable=False),
            sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
            sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
            sa.Column("claimed_amount", sa.Numeric(12, 2), nullable=False),
            sa.Column("service_date", sa.String(length=40), nullable=False),
            sa.Column("modifiers_json", JSONB(), nullable=False),
            sa.Column("nappi_code", sa.String(length=120), nullable=True),
            sa.Column("device_id", sa.String(length=120), nullable=True),
            sa.Column("rendering_provider_practice_number", sa.String(length=120), nullable=True),
            sa.Column("requires_preauth", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("requires_attachment", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.UniqueConstraint("claim_id", "claim_version", "line_id", name="uq_claim_line_items_claim_version_line"),
        )
        op.create_index("ix_claim_line_items_claim_version", "claim_line_items", ["claim_id", "claim_version"])

    if "claim_line_diagnosis_links" not in table_names:
        op.create_table(
            "claim_line_diagnosis_links",
            sa.Column("link_id", sa.String(length=120), primary_key=True),
            sa.Column("claim_line_item_id", sa.String(length=120), sa.ForeignKey("claim_line_items.claim_line_item_id"), nullable=False),
            sa.Column("claim_id", sa.Integer(), sa.ForeignKey("claims.id"), nullable=False),
            sa.Column("claim_version", sa.Integer(), nullable=False),
            sa.Column("line_id", sa.String(length=120), nullable=False),
            sa.Column("diagnosis_id", sa.String(length=120), sa.ForeignKey("claim_diagnoses.diagnosis_id"), nullable=False),
            sa.Column("sequence", sa.Integer(), nullable=False),
            sa.UniqueConstraint("claim_line_item_id", "diagnosis_id", name="uq_claim_line_diagnosis_link"),
        )

    if "edi_artifacts" not in table_names:
        op.create_table(
            "edi_artifacts",
            sa.Column("artifact_id", sa.String(length=120), primary_key=True),
            sa.Column("claim_id", sa.Integer(), sa.ForeignKey("claims.id"), nullable=False),
            sa.Column("claim_version", sa.Integer(), nullable=False),
            sa.Column("payload_id", sa.String(length=120), sa.ForeignKey("payloads.payload_id"), nullable=True),
            sa.Column("format", sa.String(length=40), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("content_hash", sa.String(length=255), nullable=False),
            sa.Column("validation_errors_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
            sa.Column("created_at", sa.String(length=40), nullable=False),
            sa.Column("created_by", sa.String(length=120), nullable=False),
        )

    pmb_columns = _column_names(inspector, "pmb_decisions")
    if "evaluated_icd10_list_json" not in pmb_columns:
        op.add_column(
            "pmb_decisions",
            sa.Column("evaluated_icd10_list_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        )
        op.alter_column("pmb_decisions", "evaluated_icd10_list_json", server_default=None)
    if "mapping_table_version" not in pmb_columns:
        op.add_column("pmb_decisions", sa.Column("mapping_table_version", sa.String(length=255), nullable=True))
    if "effective_date_used" not in pmb_columns:
        op.add_column("pmb_decisions", sa.Column("effective_date_used", sa.String(length=40), nullable=True))
    if "detection_reason" not in pmb_columns:
        op.add_column("pmb_decisions", sa.Column("detection_reason", sa.String(length=120), nullable=True))
    if "action_json" not in pmb_columns:
        op.add_column("pmb_decisions", sa.Column("action_json", JSONB(), nullable=True))
    if "line_level_evaluation_limited" not in pmb_columns:
        op.add_column(
            "pmb_decisions",
            sa.Column("line_level_evaluation_limited", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        op.alter_column("pmb_decisions", "line_level_evaluation_limited", server_default=None)

    transport_columns = _column_names(inspector, "transport_logs")
    if "claim_id" not in transport_columns:
        op.add_column("transport_logs", sa.Column("claim_id", sa.Integer(), sa.ForeignKey("claims.id"), nullable=True))
    if "claim_version" not in transport_columns:
        op.add_column("transport_logs", sa.Column("claim_version", sa.Integer(), nullable=True))
    if "artifact_id" not in transport_columns:
        op.add_column("transport_logs", sa.Column("artifact_id", sa.String(length=120), sa.ForeignKey("edi_artifacts.artifact_id"), nullable=True))
    if "submission_id" in transport_columns:
        op.alter_column("transport_logs", "submission_id", existing_type=sa.String(length=120), nullable=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = _table_names(inspector)

    if "transport_logs" in table_names:
        transport_columns = _column_names(inspector, "transport_logs")
        if "artifact_id" in transport_columns:
            op.drop_column("transport_logs", "artifact_id")
        if "claim_version" in transport_columns:
            op.drop_column("transport_logs", "claim_version")
        if "claim_id" in transport_columns:
            op.drop_column("transport_logs", "claim_id")
        if "submission_id" in transport_columns:
            op.alter_column("transport_logs", "submission_id", existing_type=sa.String(length=120), nullable=False)

    if "pmb_decisions" in table_names:
        pmb_columns = _column_names(inspector, "pmb_decisions")
        for column_name in [
            "line_level_evaluation_limited",
            "action_json",
            "detection_reason",
            "effective_date_used",
            "mapping_table_version",
            "evaluated_icd10_list_json",
        ]:
            if column_name in pmb_columns:
                op.drop_column("pmb_decisions", column_name)

    if "edi_artifacts" in table_names:
        op.drop_table("edi_artifacts")
    if "claim_line_diagnosis_links" in table_names:
        op.drop_table("claim_line_diagnosis_links")
    if "claim_line_items" in table_names:
        op.drop_index("ix_claim_line_items_claim_version", table_name="claim_line_items")
        op.drop_table("claim_line_items")
