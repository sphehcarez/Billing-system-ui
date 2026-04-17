"""Add PMB explainability fields.

Revision ID: 20260416_0002
Revises: 20260416_0001
Create Date: 2026-04-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260416_0002"
down_revision = "20260416_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("pmb_decisions")}
    if "condition_name" not in columns:
        op.add_column("pmb_decisions", sa.Column("condition_name", sa.String(length=255), nullable=True))
    if "auto_flagged" not in columns:
        op.add_column(
            "pmb_decisions",
            sa.Column("auto_flagged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        op.alter_column("pmb_decisions", "auto_flagged", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("pmb_decisions")}
    if "auto_flagged" in columns:
        op.drop_column("pmb_decisions", "auto_flagged")
    if "condition_name" in columns:
        op.drop_column("pmb_decisions", "condition_name")
