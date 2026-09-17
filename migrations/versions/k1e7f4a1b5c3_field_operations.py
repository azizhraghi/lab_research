"""Add sensor gateways, measurement review, and irrigation field tasks.

Revision ID: k1e7f4a1b5c3
Revises: j9d6e3f0a4b2
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "k1e7f4a1b5c3"
down_revision: Union[str, Sequence[str], None] = "j9d6e3f0a4b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("twin_sensor_readings", sa.Column("quality_issues", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("twin_sensor_readings", sa.Column("review_status", sa.String(), nullable=False, server_default="not_required"))
    op.add_column("twin_sensor_readings", sa.Column("reviewed_by", sa.String(), nullable=True))
    op.add_column("twin_sensor_readings", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.add_column("twin_sensor_readings", sa.Column("review_notes", sa.Text(), nullable=True))
    op.create_index("ix_twin_sensor_readings_review_status", "twin_sensor_readings", ["review_status"])

    op.create_table(
        "twin_sensor_devices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("parcel_id", sa.Integer(), sa.ForeignKey("twin_parcels.id"), nullable=False),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sensor_type", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False, unique=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("battery_percent", sa.Float(), nullable=True),
        sa.Column("last_contact_at", sa.DateTime(), nullable=True),
        sa.Column("last_upload_at", sa.DateTime(), nullable=True),
        sa.Column("consecutive_upload_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("rotated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_twin_sensor_devices_parcel_id", "twin_sensor_devices", ["parcel_id"])
    op.create_index("ix_twin_sensor_devices_code", "twin_sensor_devices", ["code"])
    op.create_index("ix_twin_sensor_devices_last_contact_at", "twin_sensor_devices", ["last_contact_at"])

    op.create_table(
        "qualite_measurement_reviews",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("reading_id", sa.String(), nullable=False, unique=True),
        sa.Column("parcel_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("quality_flag", sa.String(), nullable=False),
        sa.Column("issues", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("annotation", sa.String(), nullable=True),
        sa.Column("reviewer_id", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("correction", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_qualite_measurement_reviews_status", "qualite_measurement_reviews", ["status"])
    op.create_index("ix_qualite_measurement_reviews_reading_id", "qualite_measurement_reviews", ["reading_id"])
    op.create_index("ix_qualite_measurement_reviews_parcel_id", "qualite_measurement_reviews", ["parcel_id"])

    op.add_column("optimisation_runs", sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("optimisation_runs", sa.Column("approved_by", sa.String(), nullable=True))
    op.add_column("optimisation_runs", sa.Column("approved_at", sa.DateTime(), nullable=True))
    op.create_index("ix_optimisation_runs_is_approved", "optimisation_runs", ["is_approved"])

    op.create_table(
        "twin_irrigation_schedule_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("optimization_run_id", sa.Integer(), sa.ForeignKey("optimisation_runs.id"), nullable=False),
        sa.Column("parcel_id", sa.Integer(), sa.ForeignKey("twin_parcels.id"), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("planned_amount_mm", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("assigned_to", sa.String(), nullable=True),
        sa.Column("approved_by", sa.String(), nullable=False),
        sa.Column("completed_by", sa.String(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("actual_amount_mm", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("irrigation_event_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_twin_irrigation_schedule_tasks_optimization_run_id", "twin_irrigation_schedule_tasks", ["optimization_run_id"])
    op.create_index("ix_twin_irrigation_schedule_tasks_parcel_id", "twin_irrigation_schedule_tasks", ["parcel_id"])
    op.create_index("ix_twin_irrigation_schedule_tasks_scheduled_date", "twin_irrigation_schedule_tasks", ["scheduled_date"])
    op.create_index("ix_twin_irrigation_schedule_tasks_status", "twin_irrigation_schedule_tasks", ["status"])
    op.create_index("ix_twin_irrigation_schedule_tasks_irrigation_event_id", "twin_irrigation_schedule_tasks", ["irrigation_event_id"])


def downgrade() -> None:
    for index in ("ix_twin_irrigation_schedule_tasks_irrigation_event_id", "ix_twin_irrigation_schedule_tasks_status", "ix_twin_irrigation_schedule_tasks_scheduled_date", "ix_twin_irrigation_schedule_tasks_parcel_id", "ix_twin_irrigation_schedule_tasks_optimization_run_id"):
        op.drop_index(index, table_name="twin_irrigation_schedule_tasks")
    op.drop_table("twin_irrigation_schedule_tasks")
    op.drop_index("ix_optimisation_runs_is_approved", table_name="optimisation_runs")
    op.drop_column("optimisation_runs", "approved_at")
    op.drop_column("optimisation_runs", "approved_by")
    op.drop_column("optimisation_runs", "is_approved")
    for index in ("ix_qualite_measurement_reviews_parcel_id", "ix_qualite_measurement_reviews_reading_id", "ix_qualite_measurement_reviews_status"):
        op.drop_index(index, table_name="qualite_measurement_reviews")
    op.drop_table("qualite_measurement_reviews")
    for index in ("ix_twin_sensor_devices_last_contact_at", "ix_twin_sensor_devices_code", "ix_twin_sensor_devices_parcel_id"):
        op.drop_index(index, table_name="twin_sensor_devices")
    op.drop_table("twin_sensor_devices")
    op.drop_index("ix_twin_sensor_readings_review_status", table_name="twin_sensor_readings")
    for column in ("review_notes", "reviewed_at", "reviewed_by", "review_status", "quality_issues"):
        op.drop_column("twin_sensor_readings", column)
