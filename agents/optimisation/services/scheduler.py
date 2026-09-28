from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Iterable

from agents.digitaltwin.models import Parcel, SensorReading
from agents.digitaltwin.services.forecast import WeatherInput
from agents.digitaltwin.services.irrigation import CROP_COEFFICIENTS
from agents.simulation.services.water_balance import TEMP_ET_SENSITIVITY_PER_C


@dataclass(frozen=True)
class OptimizationConfig:
    run_name: str
    horizon_days: int
    max_irrigation_mm_per_day: float
    initial_moisture_mm: float | None = None
    water_quota_mm: float | None = None
    rainfall_factor: float = 1.0
    et_factor: float = 1.0
    temperature_delta_c: float = 0.0
    trigger_depletion_fraction: float = 0.45
    refill_depletion_fraction: float = 0.15
    crop_coefficient: float | None = None
    weather_source: str = "historical readings"
    forecast_retrieved_at: dt.datetime | None = None
    start_date: dt.date | None = None


def optimize_irrigation_schedule(
    parcel: Parcel,
    readings: Iterable[SensorReading],
    config: OptimizationConfig,
    weather_inputs: Iterable[WeatherInput] | None = None,
) -> dict[str, Any]:
    """Build a constrained schedule from explicit weather inputs and field limits."""
    ordered = sorted(readings, key=lambda row: row.recorded_at)
    if not ordered and config.initial_moisture_mm is None:
        raise ValueError("At least one sensor/weather reading is required")

    latest = ordered[-1] if ordered else None
    crop_coefficient = (
        float(config.crop_coefficient)
        if config.crop_coefficient is not None
        else CROP_COEFFICIENTS.get(parcel.crop_type, 1.0)
    )
    target_min = _target_minimum(parcel, config.trigger_depletion_fraction)
    target_refill = _target_refill(parcel, config.refill_depletion_fraction)
    template = list(weather_inputs) if weather_inputs is not None else _weather_template(ordered, config.horizon_days)
    if len(template) != config.horizon_days:
        raise ValueError(
            f"Expected {config.horizon_days} daily weather inputs, received {len(template)}"
        )
    start_date = config.start_date or (latest.recorded_at.date() + dt.timedelta(days=1))
    temp_multiplier = max(
        0.55,
        1.0 + (config.temperature_delta_c * TEMP_ET_SENSITIVITY_PER_C),
    )

    moisture = min(max(float(config.initial_moisture_mm if config.initial_moisture_mm is not None else latest.soil_moisture_mm), 0.0), parcel.field_capacity_mm)
    remaining_quota = (
        float("inf")
        if config.water_quota_mm is None
        else float(config.water_quota_mm)
    )
    schedule: list[dict[str, Any]] = []

    for index, weather in enumerate(template, start=1):
        rainfall = max(0.0, weather.rainfall_mm * config.rainfall_factor)
        et0 = max(0.0, weather.et0_fao_mm * config.et_factor * temp_multiplier)
        crop_et = et0 * crop_coefficient
        start_moisture = moisture
        projected = min(
            parcel.field_capacity_mm,
            max(0.0, moisture + rainfall - crop_et),
        )
        before_irrigation = projected
        deficit_to_refill = max(target_refill - projected, 0.0)

        irrigation = 0.0
        decision = "monitor"
        if projected < target_min and remaining_quota > 0:
            irrigation = min(
                deficit_to_refill,
                config.max_irrigation_mm_per_day,
                remaining_quota,
            )
            projected = min(parcel.field_capacity_mm, projected + irrigation)
            remaining_quota -= irrigation
            decision = "irrigate" if irrigation > 0 else "quota_exhausted"

        stress = projected < target_min
        if stress and decision == "monitor":
            decision = "stress_unresolved"

        moisture = projected
        schedule.append({
            "day": index,
            "date": (start_date + dt.timedelta(days=index - 1)).isoformat(),
            "soil_moisture_start_mm": round(start_moisture, 2),
            "rainfall_mm": round(rainfall, 2),
            "reference_et_mm": round(et0, 2),
            "crop_et_mm": round(crop_et, 2),
            "projected_moisture_before_irrigation_mm": round(before_irrigation, 2),
            "irrigation_mm": round(irrigation, 2),
            "soil_moisture_end_mm": round(moisture, 2),
            "stress": stress,
            "decision": decision,
        })

    total_irrigation = sum(row["irrigation_mm"] for row in schedule)
    stress_days = sum(1 for row in schedule if row["stress"])
    irrigation_days = sum(1 for row in schedule if row["irrigation_mm"] > 0)
    final_moisture = schedule[-1]["soil_moisture_end_mm"] if schedule else moisture
    min_moisture = min(
        (row["soil_moisture_end_mm"] for row in schedule),
        default=moisture,
    )
    risk_score = min(
        100.0,
        (stress_days / max(len(schedule), 1)) * 75.0
        + max(target_min - min_moisture, 0.0) / max(target_min, 1.0) * 25.0,
    )
    efficiency_score = max(
        0.0,
        100.0 - risk_score - (irrigation_days / max(len(schedule), 1)) * 8.0,
    )

    quota_remaining = (
        None if config.water_quota_mm is None else max(remaining_quota, 0.0)
    )
    quota_use_pct = None
    if config.water_quota_mm and config.water_quota_mm > 0:
        quota_use_pct = min(
            100.0,
            (total_irrigation / config.water_quota_mm) * 100.0,
        )

    return {
        "constraints": {
            "max_irrigation_mm_per_day": config.max_irrigation_mm_per_day,
            "water_quota_mm": config.water_quota_mm,
            "trigger_moisture_mm": round(target_min, 2),
            "refill_target_mm": round(target_refill, 2),
            "rainfall_factor": config.rainfall_factor,
            "et_factor": config.et_factor,
            "temperature_delta_c": config.temperature_delta_c,
        },
        "summary": {
            "total_irrigation_mm": round(total_irrigation, 2),
            "irrigation_days": irrigation_days,
            "stress_days": stress_days,
            "final_moisture_mm": round(final_moisture, 2),
            "min_moisture_mm": round(min_moisture, 2),
            "quota_remaining_mm": (
                None if quota_remaining is None else round(quota_remaining, 2)
            ),
            "quota_use_pct": (
                None if quota_use_pct is None else round(quota_use_pct, 1)
            ),
            "risk_score": round(risk_score, 1),
            "efficiency_score": round(efficiency_score, 1),
        },
        "schedule": schedule,
        "assumptions": {
            "optimizer": "threshold-based constrained greedy scheduler",
            "objective": "minimize irrigation while keeping moisture above management trigger",
            "crop_coefficient": crop_coefficient,
            "temperature_et_sensitivity_per_c": TEMP_ET_SENSITIVITY_PER_C,
            "weather_source": config.weather_source,
            "forecast_retrieved_at": (
                config.forecast_retrieved_at.isoformat()
                if config.forecast_retrieved_at
                else None
            ),
            "irrigation_applied_after_daily_rainfall_and_et_projection": True,
            "field_capacity_cap_applied": True,
            "decision_support_only": True,
        },
    }


def _target_minimum(parcel: Parcel, depletion_fraction: float) -> float:
    taw = max(parcel.field_capacity_mm - parcel.wilting_point_mm, 1.0)
    return round(parcel.field_capacity_mm - (taw * depletion_fraction), 2)


def _target_refill(parcel: Parcel, depletion_fraction: float) -> float:
    taw = max(parcel.field_capacity_mm - parcel.wilting_point_mm, 1.0)
    return round(parcel.field_capacity_mm - (taw * depletion_fraction), 2)


def _weather_template(readings: list[SensorReading], horizon_days: int) -> list[WeatherInput]:
    recent = readings[-min(len(readings), horizon_days):]
    return [
        WeatherInput(
            rainfall_mm=max(0.0, float(reading.rainfall_mm or 0.0)),
            et0_fao_mm=max(0.0, float(reading.evapotranspiration_mm or 0.0)),
            temperature_c=reading.temperature_c,
        )
        for reading in (recent[index % len(recent)] for index in range(horizon_days))
    ]