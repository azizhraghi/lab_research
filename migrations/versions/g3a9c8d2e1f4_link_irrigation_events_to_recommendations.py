"""Trace actual irrigation applications back to reviewed advice.

Revision ID: g3a9c8d2e1f4
Revises: f2d7b4c1e8a6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g3a9c8d2e1f4"
down_revision: Union[str, Sequence[str], None] = "f2d7b4c1e8a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The router validates the referenced recommendation, its parcel and its
    # approval status. A direct FK cannot be added in-place on SQLite, which is
    # the supported development database, so keep this an indexed soft link.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("twin_irrigation_events")}
    if "recommendation_id" not in columns:
        op.add_column(
            "twin_irrigation_events",
            sa.Column("recommendation_id", sa.Integer(), nullable=True),
        )
    indexes = {index["name"] for index in inspector.get_indexes("twin_irrigation_events")}
    if "ix_twin_irrigation_events_recommendation_id" not in indexes:
        op.create_index(
            "ix_twin_irrigation_events_recommendation_id",
            "twin_irrigation_events",
            ["recommendation_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("twin_irrigation_events")}
    if "ix_twin_irrigation_events_recommendation_id" in indexes:
        op.drop_index(
            "ix_twin_irrigation_events_recommendation_id",
            table_name="twin_irrigation_events",
        )
    columns = {column["name"] for column in inspector.get_columns("twin_irrigation_events")}
    if "recommendation_id" in columns:
        op.drop_column("twin_irrigation_events", "recommendation_id")
