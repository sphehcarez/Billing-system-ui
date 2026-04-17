"""Add display_name columns and copay/invoice/outbox/idempotency tables.

Revision ID: 20260417_0005
Revises: 20260417_0004
Create Date: 2026-04-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "20260417_0005"
down_revision = "20260417_0004"
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

    # -------------------------------------------------------------------------
    # Add display_name to patients, providers, claims (idempotent)
    # -------------------------------------------------------------------------
    for tbl in ("patients", "providers", "claims"):
        if tbl in table_names:
            cols = _column_names(inspector, tbl)
            if "display_name" not in cols:
                op.add_column(tbl, sa.Column("display_name", sa.String(length=200), nullable=True))

    # -------------------------------------------------------------------------
    # patient_balances
    # -------------------------------------------------------------------------
    if "patient_balances" not in table_names:
        op.create_table(
            "patient_balances",
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "balance_cents",
                sa.BigInteger(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "credit_cents",
                sa.BigInteger(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    # -------------------------------------------------------------------------
    # invoices
    # -------------------------------------------------------------------------
    if "invoices" not in table_names:
        op.create_table(
            "invoices",
            sa.Column("id", sa.String(length=32), primary_key=True),
            sa.Column(
                "patient_id",
                sa.Integer(),
                sa.ForeignKey("patients.id"),
                nullable=False,
            ),
            sa.Column(
                "claim_id",
                sa.Integer(),
                sa.ForeignKey("claims.id"),
                nullable=False,
            ),
            sa.Column("total_cents", sa.BigInteger(), nullable=False),
            sa.Column(
                "paid_cents",
                sa.BigInteger(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "status",
                sa.String(length=16),
                nullable=False,
                server_default=sa.text("'OPEN'"),
            ),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.CheckConstraint(
                "status IN ('OPEN','PARTIAL','PAID','VOIDED')",
                name="ck_invoices_status",
            ),
            sa.UniqueConstraint("claim_id", name="uq_invoices_claim_id"),
        )

    # -------------------------------------------------------------------------
    # copay_items
    # -------------------------------------------------------------------------
    if "copay_items" not in table_names:
        op.create_table(
            "copay_items",
            sa.Column("id", sa.String(length=32), primary_key=True),
            sa.Column(
                "invoice_id",
                sa.String(length=32),
                sa.ForeignKey("invoices.id"),
                nullable=False,
            ),
            sa.Column("reason_code", sa.String(length=32), nullable=False),
            sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        )

    # -------------------------------------------------------------------------
    # outbox_events
    # -------------------------------------------------------------------------
    if "outbox_events" not in table_names:
        op.create_table(
            "outbox_events",
            sa.Column(
                "id",
                sa.BigInteger(),
                primary_key=True,
                autoincrement=True,
                nullable=False,
            ),
            sa.Column("event_type", sa.String(length=64), nullable=False),
            sa.Column("payload", JSONB(), nullable=False),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("emitted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        )

    # -------------------------------------------------------------------------
    # idempotency_keys
    # -------------------------------------------------------------------------
    if "idempotency_keys" not in table_names:
        op.create_table(
            "idempotency_keys",
            sa.Column(
                "id",
                sa.BigInteger(),
                primary_key=True,
                autoincrement=True,
                nullable=False,
            ),
            sa.Column(
                "idempotency_key",
                sa.String(length=64),
                nullable=False,
                unique=True,
            ),
            sa.Column("body_hash", sa.String(length=64), nullable=False),
            sa.Column("response_json", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = _table_names(inspector)

    if "idempotency_keys" in table_names:
        op.drop_table("idempotency_keys")
    if "outbox_events" in table_names:
        op.drop_table("outbox_events")
    if "copay_items" in table_names:
        op.drop_table("copay_items")
    if "invoices" in table_names:
        op.drop_table("invoices")
    if "patient_balances" in table_names:
        op.drop_table("patient_balances")

    for tbl in ("patients", "providers", "claims"):
        if tbl in table_names:
            cols = _column_names(inspector, tbl)
            if "display_name" in cols:
                op.drop_column(tbl, "display_name")
