"""create postgres claims platform schema

Revision ID: 20260416_0001
Revises: 
Create Date: 2026-04-16 00:00:00
"""

from __future__ import annotations

from alembic import op

from db_schema import metadata


revision = "20260416_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    metadata.drop_all(bind=bind)
