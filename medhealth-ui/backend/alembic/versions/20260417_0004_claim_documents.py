"""Add claim document persistence for attachment workflows.

Revision ID: 20260417_0004
Revises: 20260416_0003
Create Date: 2026-04-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260417_0004"
down_revision = "20260416_0003"
branch_labels = None
depends_on = None


def _table_names(inspector) -> set[str]:
    return set(inspector.get_table_names())


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = _table_names(inspector)

    if "claim_documents" not in table_names:
        op.create_table(
            "claim_documents",
            sa.Column("document_id", sa.String(length=120), primary_key=True),
            sa.Column("claim_id", sa.Integer(), sa.ForeignKey("claims.id"), nullable=False),
            sa.Column("claim_version", sa.Integer(), nullable=False),
            sa.Column("encounter_id", sa.String(length=120), nullable=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id"), nullable=False),
            sa.Column("provider_id", sa.Integer(), sa.ForeignKey("providers.id"), nullable=False),
            sa.Column("doc_type", sa.String(length=80), nullable=False),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("storage_ref", sa.String(length=255), nullable=False),
            sa.Column("file_hash", sa.String(length=255), nullable=False),
            sa.Column("uploaded_at", sa.String(length=40), nullable=False),
            sa.Column("uploaded_by", sa.String(length=120), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False, server_default="AVAILABLE"),
        )
        op.create_index("ix_claim_documents_claim_version", "claim_documents", ["claim_id", "claim_version"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = _table_names(inspector)
    if "claim_documents" in table_names:
        op.drop_index("ix_claim_documents_claim_version", table_name="claim_documents")
        op.drop_table("claim_documents")
