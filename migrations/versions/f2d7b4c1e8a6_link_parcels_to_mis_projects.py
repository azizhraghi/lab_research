"""Link Digital Twin parcels to the MIS project that requested them.

Revision ID: f2d7b4c1e8a6
Revises: e4c8f6a2d9b1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2d7b4c1e8a6"
down_revision: Union[str, Sequence[str], None] = "e4c8f6a2d9b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This deliberately remains an indexed application-level link instead of a
    # cross-module database FK: standalone parcels are supported and existing
    # MIS project deletion behaviour must not be changed by this migration.
    op.add_column("twin_parcels", sa.Column("project_id", sa.String(), nullable=True))
    op.create_index("ix_twin_parcels_project_id", "twin_parcels", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_twin_parcels_project_id", table_name="twin_parcels")
    op.drop_column("twin_parcels", "project_id")
