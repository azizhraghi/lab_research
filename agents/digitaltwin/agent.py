"""
Digital Twin Agent — orchestrates sensor ingestion, irrigation recommendations,
and simulation scenarios for irrigated parcels.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shared.base_agent import BaseAgent
from shared.schemas import Event, AgentAction, ActionResult
from agents.digitaltwin.models import (
    Parcel, SensorReading, IrrigationRecommendation, SimulationScenario
)
from agents.digitaltwin.services.irrigation import (
    IrrigationInput, CROP_COEFFICIENTS, calculate_irrigation_recommendation
)
from agents.digitaltwin.services.simulator import run_simulation


class DigitalTwinAgent(BaseAgent):
    name = "digital_twin"
    permissions = ["twin.read", "twin.write"]
    requires_human_approval = []

    async def _setup_subscriptions(self):
        pass

    async def handle_event(self, event: Event) -> Optional[AgentAction]:
        return None

    async def execute_action(self, action: AgentAction) -> ActionResult:
        return ActionResult(
            action_id=action.id,
            status="completed",
            result_data={"message": "Action executed by DigitalTwinAgent"},
        )

    # ── Core capabilities ───────────────────────────

    async def ingest_reading(
        self, db: AsyncSession, parcel_id: int, reading_data: dict
    ) -> SensorReading:
        """Store a sensor reading for a parcel."""
        reading = SensorReading(parcel_id=parcel_id, **reading_data)
        db.add(reading)
        await db.flush()
        return reading

    async def generate_recommendation(
        self, db: AsyncSession, parcel_id: int
    ) -> IrrigationRecommendation:
        """Generate an irrigation recommendation from the latest sensor reading."""
        # Get parcel
        parcel = await db.get(Parcel, parcel_id)
        if not parcel:
            raise ValueError(f"Parcel {parcel_id} not found")

        # Get latest reading
        stmt = (
            select(SensorReading)
            .where(SensorReading.parcel_id == parcel_id)
            .order_by(SensorReading.recorded_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        latest = result.scalar_one_or_none()
        if not latest:
            raise ValueError(f"No sensor readings for parcel {parcel_id}")

        # Run the physics model
        kc = CROP_COEFFICIENTS.get(parcel.crop_type, 1.0)
        inp = IrrigationInput(
            soil_moisture_mm=latest.soil_moisture_mm,
            field_capacity_mm=parcel.field_capacity_mm,
            wilting_point_mm=parcel.wilting_point_mm,
            rainfall_mm=latest.rainfall_mm,
            evapotranspiration_mm=latest.evapotranspiration_mm,
            crop_coefficient=kc,
        )
        result = calculate_irrigation_recommendation(inp)

        # Store the recommendation
        rec = IrrigationRecommendation(
            parcel_id=parcel_id,
            water_balance_mm=result.water_balance_mm,
            recommended_irrigation_mm=result.recommended_irrigation_mm,
            confidence=result.confidence,
            rationale=result.rationale,
        )
        db.add(rec)
        await db.flush()
        return rec

    async def run_scenario(
        self, db: AsyncSession, parcel_id: int, scenario_data: dict
    ) -> SimulationScenario:
        """Run a what-if simulation on a parcel."""
        # Get parcel
        parcel = await db.get(Parcel, parcel_id)
        if not parcel:
            raise ValueError(f"Parcel {parcel_id} not found")

        # Get latest reading
        stmt = (
            select(SensorReading)
            .where(SensorReading.parcel_id == parcel_id)
            .order_by(SensorReading.recorded_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        latest = result.scalar_one_or_none()
        if not latest:
            raise ValueError(f"No sensor readings for parcel {parcel_id}")

        # Run the simulation engine
        sim_result = await run_simulation(
            soil_moisture_mm=latest.soil_moisture_mm,
            field_capacity_mm=parcel.field_capacity_mm,
            wilting_point_mm=parcel.wilting_point_mm,
            rainfall_mm=latest.rainfall_mm,
            evapotranspiration_mm=latest.evapotranspiration_mm,
            crop_type=parcel.crop_type,
            parcel_name=parcel.name,
            **scenario_data,
        )

        # Store the scenario
        scenario = SimulationScenario(
            parcel_id=parcel_id,
            scenario_name=scenario_data.get("scenario_name", "Custom scenario"),
            rainfall_factor=scenario_data.get("rainfall_factor", 1.0),
            et_factor=scenario_data.get("et_factor", 1.0),
            temperature_delta_c=scenario_data.get("temperature_delta_c", 0.0),
            **sim_result,
        )
        db.add(scenario)
        await db.flush()
        return scenario


digital_twin_agent = DigitalTwinAgent()
