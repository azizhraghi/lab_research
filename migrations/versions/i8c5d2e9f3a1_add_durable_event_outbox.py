"""Persist outgoing agent events before delivery.

Revision ID: i8c5d2e9f3a1
Revises: h6b4e1c9a2d7
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "i8c5d2e9f3a1"
down_revision: Union[str, Sequence[str], None] = "h6b4e1c9a2d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_outbox",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("stream", sa.String(), nullable=False),
        sa.Column("event", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=False),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_system_outbox_stream", "system_outbox", ["stream"])
    op.create_index("ix_system_outbox_status", "system_outbox", ["status"])
    op.create_index("ix_system_outbox_next_attempt_at", "system_outbox", ["next_attempt_at"])
    op.create_index("ix_system_outbox_locked_until", "system_outbox", ["locked_until"])
    op.create_index("ix_system_outbox_created_at", "system_outbox", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_system_outbox_created_at", table_name="system_outbox")
    op.drop_index("ix_system_outbox_locked_until", table_name="system_outbox")
    op.drop_index("ix_system_outbox_next_attempt_at", table_name="system_outbox")
    op.drop_index("ix_system_outbox_status", table_name="system_outbox")
    op.drop_index("ix_system_outbox_stream", table_name="system_outbox")
    op.drop_table("system_outbox")
