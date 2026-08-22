"""Trace irrigation recommendations back to their source measurement.

Revision ID: d1f4e2a9b3c7
Revises: c9e21_add_veille_pgvector
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1f4e2a9b3c7"
down_revision: Union[str, Sequence[str], None] = "c9e21_add_veille_pgvector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "twin_recommendations",
        sa.Column("source_reading_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "twin_recommendations",
        sa.Column(
            "generation_mode",
            sa.String(),
            nullable=False,
            server_default=sa.text("'manual'"),
        ),
    )
    op.create_index(
        "uq_twin_recommendations_source_reading_id",
        "twin_recommendations",
        ["source_reading_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_twin_recommendations_source_reading_id",
        table_name="twin_recommendations",
    )
    op.drop_column("twin_recommendations", "generation_mode")
    op.drop_column("twin_recommendations", "source_reading_id")
