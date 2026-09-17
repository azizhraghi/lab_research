"""
Digital Twin Agent — orchestrates sensor ingestion, irrigation recommendations,
and simulation scenarios for irrigated parcels.
"""
from typing import Optional
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shared.base_agent import BaseAgent
from shared.schemas import Event, AgentAction, ActionResult
from shared.outbox import enqueue_event, outbox_dispatcher
from agents.digitaltwin.models import (
    Parcel, SensorReading, IrrigationRecommendation, SimulationScenario
)
from agents.digitaltwin.services.irrigation import (
    IrrigationInput, CROP_COEFFICIENTS, calculate_irrigation_recommendation
)
from agents.digitaltwin.services.forecast import get_active_crop_coefficient
from agents.digitaltwin.services.simulator import run_simulation
from agents.digitaltwin.services.eligibility import operational_readings


class DigitalTwinAgent(BaseAgent):
    name = "digital_twin"
    permissions = ["twin.read", "twin.write"]
    requires_human_approval = []

    async def _setup_subscriptions(self):
        await self._subscribe("events", self._on_bus_event)

    async def _on_bus_event(self, event: Event) -> None:
        """Create advice only after the quality agent accepts a new reading."""
        if event.type != "twin.reading_validated":
            return

        parcel_id = event.payload.get("parcel_id")
        reading_id = event.payload.get("reading_id")
        if not isinstance(parcel_id, int) or not isinstance(reading_id, int):
            return

        from shared.database import AsyncSessionLocal

        try:
            async with AsyncSessionLocal() as db:
                recommendation = await self.generate_recommendation(
                    db,
                    parcel_id,
                    source_reading_id=reading_id,
                    generation_mode="automatic",
                )
                parcel = await db.get(Parcel, parcel_id)
                # Store the downstream review request with the recommendation.
                # If either insert fails, neither part of the workflow survives.
                await enqueue_event(db, "events", Event(
                    id=str(uuid4()),
                    type="twin.recommendation_generated",
                    source_agent=self.name,
                    payload={
                        "parcel_id": parcel_id,
                        "reading_id": reading_id,
                        "recommendation_id": recommendation.id,
                        "recommended_irrigation_mm": recommendation.recommended_irrigation_mm,
                        "parcel_name": parcel.name if parcel else None,
                        "project_id": parcel.project_id if parcel else None,
                        "generation_mode": recommendation.generation_mode,
                        "review_required": True,
                    },
                ))
                await db.commit()
        except ValueError as exc:
            print(f"[{self.name}] No automatic recommendation: {exc}")
            return
        outbox_dispatcher.notify()

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
        # Client flags never grant eligibility while background validation runs.
        reading_data.update(quality_flag="pending", review_status="pending_validation")
        reading = SensorReading(parcel_id=parcel_id, **reading_data)
        db.add(reading)
        await db.flush()
        return reading

    async def generate_recommendation(
        self,
        db: AsyncSession,
        parcel_id: int,
        source_reading_id: int | None = None,
        generation_mode: str = "manual",
    ) -> IrrigationRecommendation:
        """Generate traceable advice from one reading, never field actuation."""
        # Get parcel
        parcel = await db.get(Parcel, parcel_id)
        if not parcel:
            raise ValueError(f"Parcel {parcel_id} not found")

        latest = (await operational_readings(db, parcel, source_reading_id))[-1]

        # A reading is the durable idempotency key. This also means the manual
        # endpoint safely returns an already-generated agent recommendation
        # instead of violating the unique source_reading_id constraint.
        existing_result = await db.execute(
            select(IrrigationRecommendation).where(
                IrrigationRecommendation.source_reading_id == latest.id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            return existing

        # Run the physics model. The crop coefficient honours a human-applied
        # calibration profile when one exists, so calibrating moves this number
        # the same way it moves simulation and optimisation.
        kc, _calibration_metadata = await get_active_crop_coefficient(
            db=db,
            parcel_id=parcel_id,
            fallback=float(CROP_COEFFICIENTS.get(parcel.crop_type, 1.0)),
        )
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
            source_reading_id=latest.id,
            generation_mode=generation_mode,
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

        latest = (await operational_readings(db, parcel))[-1]

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
