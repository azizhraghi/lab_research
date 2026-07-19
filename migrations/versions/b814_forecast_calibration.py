"""Add traceable weather forecasts and calibration profiles

Revision ID: b814_forecast_calibration
Revises: a71301_twin_sim_opt
Create Date: 2026-07-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b814_forecast_calibration"
down_revision: Union[str, Sequence[str], None] = "a71301_twin_sim_opt"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "twin_sensor_readings",
        sa.Column(
            "data_origin",
            sa.String(),
            nullable=False,
            server_default=sa.text("'unknown'"),
        ),
    )

    op.create_table(
        "twin_weather_forecasts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parcel_id", sa.Integer(), nullable=False),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("provider_model", sa.String(), nullable=False),
        sa.Column("precipitation_mm", sa.Float(), nullable=False),
        sa.Column("et0_fao_mm", sa.Float(), nullable=False),
        sa.Column("temperature_mean_c", sa.Float(), nullable=True),
        sa.Column("precipitation_probability_pct", sa.Float(), nullable=True),
        sa.Column("source_metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["parcel_id"], ["twin_parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_twin_weather_forecasts_id"),
        "twin_weather_forecasts",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_twin_weather_forecasts_parcel_id"),
        "twin_weather_forecasts",
        ["parcel_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_twin_weather_forecasts_forecast_date"),
        "twin_weather_forecasts",
        ["forecast_date"],
        unique=False,
    )

    op.create_table(
        "twin_irrigation_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parcel_id", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("amount_mm", sa.Float(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["parcel_id"], ["twin_parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_twin_irrigation_events_id"),
        "twin_irrigation_events",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_twin_irrigation_events_parcel_id"),
        "twin_irrigation_events",
        ["parcel_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_twin_irrigation_events_occurred_at"),
        "twin_irrigation_events",
        ["occurred_at"],
        unique=False,
    )

    op.create_table(
        "twin_calibration_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parcel_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("source_start_date", sa.Date(), nullable=False),
        sa.Column("source_end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("data_quality", sa.JSON(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["parcel_id"], ["twin_parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_twin_calibration_profiles_id"),
        "twin_calibration_profiles",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_twin_calibration_profiles_parcel_id"),
        "twin_calibration_profiles",
        ["parcel_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_twin_calibration_profiles_parcel_id"),
        table_name="twin_calibration_profiles",
    )
    op.drop_index(
        op.f("ix_twin_calibration_profiles_id"),
        table_name="twin_calibration_profiles",
    )
    op.drop_table("twin_calibration_profiles")
    op.drop_index(
        op.f("ix_twin_irrigation_events_occurred_at"),
        table_name="twin_irrigation_events",
    )
    op.drop_index(
        op.f("ix_twin_irrigation_events_parcel_id"),
        table_name="twin_irrigation_events",
    )
    op.drop_index(
        op.f("ix_twin_irrigation_events_id"),
        table_name="twin_irrigation_events",
    )
    op.drop_table("twin_irrigation_events")
    op.drop_index(
        op.f("ix_twin_weather_forecasts_forecast_date"),
        table_name="twin_weather_forecasts",
    )
    op.drop_index(
        op.f("ix_twin_weather_forecasts_parcel_id"),
        table_name="twin_weather_forecasts",
    )
    op.drop_index(
        op.f("ix_twin_weather_forecasts_id"),
        table_name="twin_weather_forecasts",
    )
    op.drop_table("twin_weather_forecasts")
    op.drop_column("twin_sensor_readings", "data_origin")