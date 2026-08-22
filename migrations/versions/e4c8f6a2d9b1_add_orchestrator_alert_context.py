"""Persist structured context for actionable orchestrator alerts.

Revision ID: e4c8f6a2d9b1
Revises: d1f4e2a9b3c7
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4c8f6a2d9b1"
down_revision: Union[str, Sequence[str], None] = "d1f4e2a9b3c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orch_alertes",
        sa.Column("context", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_column("orch_alertes", "context")
