"""Add digital twin, simulation, and optimisation models

Revision ID: a71301_twin_sim_opt
Revises: df701e9f135b
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a71301_twin_sim_opt"
down_revision: Union[str, Sequence[str], None] = "df701e9f135b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "twin_parcels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("crop_type", sa.String(), nullable=True),
        sa.Column("area_ha", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("soil_type", sa.String(), nullable=True),
        sa.Column("field_capacity_mm", sa.Float(), nullable=True),
        sa.Column("wilting_point_mm", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_twin_parcels_id"), "twin_parcels", ["id"], unique=False)
    op.create_index(op.f("ix_twin_parcels_name"), "twin_parcels", ["name"], unique=False)
    op.create_index(op.f("ix_twin_parcels_code"), "twin_parcels", ["code"], unique=True)

    op.create_table(
        "twin_sensor_readings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parcel_id", sa.Integer(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=True),
        sa.Column("soil_moisture_mm", sa.Float(), nullable=True),
        sa.Column("rainfall_mm", sa.Float(), nullable=True),
        sa.Column("evapotranspiration_mm", sa.Float(), nullable=True),
        sa.Column("temperature_c", sa.Float(), nullable=True),
        sa.Column("sensor_code", sa.String(), nullable=True),
        sa.Column("quality_flag", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["parcel_id"], ["twin_parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_twin_sensor_readings_id"), "twin_sensor_readings", ["id"], unique=False)
    op.create_index(op.f("ix_twin_sensor_readings_parcel_id"), "twin_sensor_readings", ["parcel_id"], unique=False)
    op.create_index(op.f("ix_twin_sensor_readings_recorded_at"), "twin_sensor_readings", ["recorded_at"], unique=False)

    op.create_table(
        "twin_recommendations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parcel_id", sa.Integer(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("water_balance_mm", sa.Float(), nullable=True),
        sa.Column("recommended_irrigation_mm", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("is_validated", sa.Boolean(), nullable=True),
        sa.Column("validated_by", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["parcel_id"], ["twin_parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_twin_recommendations_id"), "twin_recommendations", ["id"], unique=False)
    op.create_index(op.f("ix_twin_recommendations_parcel_id"), "twin_recommendations", ["parcel_id"], unique=False)

    op.create_table(
        "twin_simulations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parcel_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("scenario_name", sa.String(), nullable=True),
        sa.Column("rainfall_factor", sa.Float(), nullable=True),
        sa.Column("et_factor", sa.Float(), nullable=True),
        sa.Column("temperature_delta_c", sa.Float(), nullable=True),
        sa.Column("baseline_irrigation_mm", sa.Float(), nullable=True),
        sa.Column("simulated_irrigation_mm", sa.Float(), nullable=True),
        sa.Column("baseline_balance_mm", sa.Float(), nullable=True),
        sa.Column("simulated_balance_mm", sa.Float(), nullable=True),
        sa.Column("ai_analysis", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["parcel_id"], ["twin_parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_twin_simulations_id"), "twin_simulations", ["id"], unique=False)
    op.create_index(op.f("ix_twin_simulations_parcel_id"), "twin_simulations", ["parcel_id"], unique=False)

    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parcel_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("scenario_name", sa.String(), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("rainfall_factor", sa.Float(), nullable=False),
        sa.Column("et_factor", sa.Float(), nullable=False),
        sa.Column("temperature_delta_c", sa.Float(), nullable=False),
        sa.Column("initial_moisture_mm", sa.Float(), nullable=True),
        sa.Column("baseline_summary", sa.JSON(), nullable=False),
        sa.Column("scenario_summary", sa.JSON(), nullable=False),
        sa.Column("deltas", sa.JSON(), nullable=False),
        sa.Column("time_series", sa.JSON(), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["parcel_id"], ["twin_parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_simulation_runs_id"), "simulation_runs", ["id"], unique=False)
    op.create_index(op.f("ix_simulation_runs_parcel_id"), "simulation_runs", ["parcel_id"], unique=False)

    op.create_table(
        "optimisation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parcel_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("run_name", sa.String(), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("max_irrigation_mm_per_day", sa.Float(), nullable=False),
        sa.Column("water_quota_mm", sa.Float(), nullable=True),
        sa.Column("rainfall_factor", sa.Float(), nullable=False),
        sa.Column("et_factor", sa.Float(), nullable=False),
        sa.Column("temperature_delta_c", sa.Float(), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("schedule", sa.JSON(), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["parcel_id"], ["twin_parcels.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_optimisation_runs_id"), "optimisation_runs", ["id"], unique=False)
    op.create_index(op.f("ix_optimisation_runs_parcel_id"), "optimisation_runs", ["parcel_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_optimisation_runs_parcel_id"), table_name="optimisation_runs")
    op.drop_index(op.f("ix_optimisation_runs_id"), table_name="optimisation_runs")
    op.drop_table("optimisation_runs")
    op.drop_index(op.f("ix_simulation_runs_parcel_id"), table_name="simulation_runs")
    op.drop_index(op.f("ix_simulation_runs_id"), table_name="simulation_runs")
    op.drop_table("simulation_runs")
    op.drop_index(op.f("ix_twin_simulations_parcel_id"), table_name="twin_simulations")
    op.drop_index(op.f("ix_twin_simulations_id"), table_name="twin_simulations")
    op.drop_table("twin_simulations")
    op.drop_index(op.f("ix_twin_recommendations_parcel_id"), table_name="twin_recommendations")
    op.drop_index(op.f("ix_twin_recommendations_id"), table_name="twin_recommendations")
    op.drop_table("twin_recommendations")
    op.drop_index(op.f("ix_twin_sensor_readings_recorded_at"), table_name="twin_sensor_readings")
    op.drop_index(op.f("ix_twin_sensor_readings_parcel_id"), table_name="twin_sensor_readings")
    op.drop_index(op.f("ix_twin_sensor_readings_id"), table_name="twin_sensor_readings")
    op.drop_table("twin_sensor_readings")
    op.drop_index(op.f("ix_twin_parcels_code"), table_name="twin_parcels")
    op.drop_index(op.f("ix_twin_parcels_name"), table_name="twin_parcels")
    op.drop_index(op.f("ix_twin_parcels_id"), table_name="twin_parcels")
    op.drop_table("twin_parcels")
