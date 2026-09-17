"""Record completed agent deliveries for idempotent retry.

Revision ID: j9d6e3f0a4b2
Revises: i8c5d2e9f3a1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "j9d6e3f0a4b2"
down_revision: Union[str, Sequence[str], None] = "i8c5d2e9f3a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_event_receipts",
        sa.Column("agent_name", sa.String(), primary_key=True),
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("status", sa.String(), nullable=False, server_default="processing"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_system_event_receipts_status", "system_event_receipts", ["status"])
    op.create_index("ix_system_event_receipts_locked_until", "system_event_receipts", ["locked_until"])
    op.create_index("ix_system_event_receipts_created_at", "system_event_receipts", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_system_event_receipts_created_at", table_name="system_event_receipts")
    op.drop_index("ix_system_event_receipts_locked_until", table_name="system_event_receipts")
    op.drop_index("ix_system_event_receipts_status", table_name="system_event_receipts")
    op.drop_table("system_event_receipts")
