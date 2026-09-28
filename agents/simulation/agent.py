from __future__ import annotations
from agents.digitaltwin.services.experiment import experiment_inputs, experiment_snapshot

import datetime as dt
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.base_agent import BaseAgent
from shared.schemas import ActionResult, AgentAction, Event
from agents.digitaltwin.models import Parcel, SensorReading
from agents.digitaltwin.services.eligibility import operational_readings
from agents.digitaltwin.services.forecast import (
    get_active_crop_coefficient,
    get_current_forecast_coverage,
)
from agents.digitaltwin.services.irrigation import CROP_COEFFICIENTS
from agents.simulation.models import SimulationRun
from agents.simulation.schemas import SimulationRunRequest
from agents.simulation.services.water_balance import (
    ProjectionConfig,
    run_water_balance_projection,
)


class SimulationAgent(BaseAgent):
    name = "simulation"
    permissions = ["simulation.read", "simulation.write"]
    requires_human_approval = []

    async def _setup_subscriptions(self):
        pass

    async def handle_event(self, event: Event) -> Optional[AgentAction]:
        return None

    async def execute_action(self, action: AgentAction) -> ActionResult:
        return ActionResult(
            action_id=action.id,
            status="completed",
            result_data={"message": "Action executed by SimulationAgent"},
        )

    async def run_parcel_projection(
        self,
        db: AsyncSession,
        parcel_id: int,
        request: SimulationRunRequest,
    ) -> SimulationRun:
        parcel = await db.get(Parcel, parcel_id)
        if not parcel:
            raise ValueError(f"Parcel {parcel_id} not found")

        readings, start_date = await experiment_inputs(db, parcel, request)
        latest_reading = readings[-1] if readings else None
        forecast = await get_current_forecast_coverage(
            db=db,
            parcel_id=parcel_id,
            horizon_days=request.horizon_days,
            start_date=start_date,
        )
        crop_coefficient, calibration_metadata = await get_active_crop_coefficient(
            db=db,
            parcel_id=parcel_id,
            fallback=float(CROP_COEFFICIENTS.get(parcel.crop_type, 1.0)),
        )

        projection = run_water_balance_projection(
            parcel=parcel,
            readings=readings,
            weather_inputs=forecast.inputs,
            config=ProjectionConfig(
                **request.model_dump(exclude={"mode"}),
                crop_coefficient=crop_coefficient,
                weather_source=f"{forecast.provider} / {forecast.provider_model}",
                forecast_retrieved_at=forecast.retrieved_at,
                start_date=forecast.start_date,
            ),
        )
        projection["assumptions"].update(experiment_snapshot(parcel, request, readings, forecast))
        projection["assumptions"].update(calibration_metadata)

        run = SimulationRun(
            parcel_id=parcel_id,
            scenario_name=request.scenario_name,
            horizon_days=request.horizon_days,
            rainfall_factor=request.rainfall_factor,
            et_factor=request.et_factor,
            temperature_delta_c=request.temperature_delta_c,
            initial_moisture_mm=request.initial_moisture_mm,
            baseline_summary=projection["baseline_summary"],
            scenario_summary=projection["scenario_summary"],
            deltas=projection["deltas"],
            time_series=projection["time_series"],
            assumptions=projection["assumptions"],
        )
        db.add(run)
        await db.flush()
        return run


simulation_agent = SimulationAgent()
