"""Persist reviewed planning tasks and proposals.

Revision ID: h6b4e1c9a2d7
Revises: g3a9c8d2e1f4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "h6b4e1c9a2d7"
down_revision: Union[str, Sequence[str], None] = "g3a9c8d2e1f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orch_planning_tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("priority", sa.String(), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("duration_hours", sa.Float(), nullable=False, server_default="1"),
        sa.Column("required_skills", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("required_equipment_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("assigned_personnel_id", sa.String(), nullable=True),
        sa.Column("scheduled_start", sa.DateTime(), nullable=True),
        sa.Column("scheduled_end", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_orch_planning_tasks_project_id", "orch_planning_tasks", ["project_id"])
    op.create_index("ix_orch_planning_tasks_status", "orch_planning_tasks", ["status"])
    op.create_index("ix_orch_planning_tasks_assigned_personnel_id", "orch_planning_tasks", ["assigned_personnel_id"])
    op.create_table(
        "orch_planning_proposals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("status", sa.String(), nullable=False, server_default="proposed"),
        sa.Column("proposed_assignments", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("conflicts", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by", sa.String(), nullable=True),
    )
    op.create_index("ix_orch_planning_proposals_status", "orch_planning_proposals", ["status"])


def downgrade() -> None:
    op.drop_index("ix_orch_planning_proposals_status", table_name="orch_planning_proposals")
    op.drop_table("orch_planning_proposals")
    op.drop_index("ix_orch_planning_tasks_assigned_personnel_id", table_name="orch_planning_tasks")
    op.drop_index("ix_orch_planning_tasks_status", table_name="orch_planning_tasks")
    op.drop_index("ix_orch_planning_tasks_project_id", table_name="orch_planning_tasks")
    op.drop_table("orch_planning_tasks")
