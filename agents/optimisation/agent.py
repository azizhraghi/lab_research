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
from agents.optimisation.models import OptimizationRun
from agents.simulation.services.water_balance import ProjectionConfig, run_water_balance_projection
from agents.optimisation.schemas import OptimizationRunRequest
from agents.optimisation.services.scheduler import (
    OptimizationConfig,
    optimize_irrigation_schedule,
)


class OptimisationAgent(BaseAgent):
    name = "optimisation"
    permissions = ["optimisation.read", "optimisation.write"]
    requires_human_approval = []

    async def _setup_subscriptions(self):
        pass

    async def handle_event(self, event: Event) -> Optional[AgentAction]:
        return None

    async def execute_action(self, action: AgentAction) -> ActionResult:
        return ActionResult(
            action_id=action.id,
            status="completed",
            result_data={"message": "Action executed by OptimisationAgent"},
        )

    async def optimise_irrigation(
        self,
        db: AsyncSession,
        parcel_id: int,
        request: OptimizationRunRequest,
    ) -> OptimizationRun:
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

        optimization = optimize_irrigation_schedule(
            parcel=parcel,
            readings=readings,
            weather_inputs=forecast.inputs,
            config=OptimizationConfig(
                **request.model_dump(exclude={"mode"}),
                crop_coefficient=crop_coefficient,
                weather_source=f"{forecast.provider} / {forecast.provider_model}",
                forecast_retrieved_at=forecast.retrieved_at,
                start_date=forecast.start_date,
            ),
        )
        optimization["assumptions"].update(experiment_snapshot(parcel, request, readings, forecast))
        optimization["assumptions"].update(calibration_metadata)
        comparison = run_water_balance_projection(
            parcel, readings, ProjectionConfig(
                scenario_name=request.run_name, horizon_days=request.horizon_days,
                rainfall_factor=request.rainfall_factor, et_factor=request.et_factor,
                temperature_delta_c=request.temperature_delta_c,
                initial_moisture_mm=request.initial_moisture_mm,
                crop_coefficient=crop_coefficient, start_date=forecast.start_date,
            ), weather_inputs=forecast.inputs,
        )
        optimization['assumptions']['comparison'] = comparison

        run = OptimizationRun(
            parcel_id=parcel_id,
            run_name=request.run_name,
            horizon_days=request.horizon_days,
            max_irrigation_mm_per_day=request.max_irrigation_mm_per_day,
            water_quota_mm=request.water_quota_mm,
            rainfall_factor=request.rainfall_factor,
            et_factor=request.et_factor,
            temperature_delta_c=request.temperature_delta_c,
            constraints=optimization["constraints"],
            summary=optimization["summary"],
            schedule=optimization["schedule"],
            assumptions=optimization["assumptions"],
        )
        db.add(run)
        await db.flush()
        return run


optimisation_agent = OptimisationAgent()
