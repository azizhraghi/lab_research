from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Iterable

from agents.digitaltwin.models import Parcel, SensorReading
from agents.digitaltwin.services.forecast import WeatherInput
from agents.digitaltwin.services.irrigation import CROP_COEFFICIENTS

TEMP_ET_SENSITIVITY_PER_C = 0.04
DEFAULT_MANAGEMENT_ALLOWED_DEPLETION = 0.45
DEFAULT_REFILL_DEPLETION = 0.15


@dataclass(frozen=True)
class ProjectionConfig:
    scenario_name: str
    horizon_days: int
    rainfall_factor: float = 1.0
    et_factor: float = 1.0
    temperature_delta_c: float = 0.0
    initial_moisture_mm: float | None = None
    management_allowed_depletion: float = DEFAULT_MANAGEMENT_ALLOWED_DEPLETION
    refill_depletion: float = DEFAULT_REFILL_DEPLETION
    crop_coefficient: float | None = None
    weather_source: str = "historical readings"
    forecast_retrieved_at: dt.datetime | None = None
    start_date: dt.date | None = None


def run_water_balance_projection(
    parcel: Parcel,
    readings: Iterable[SensorReading],
    config: ProjectionConfig,
    weather_inputs: Iterable[WeatherInput] | None = None,
) -> dict[str, Any]:
    """Run baseline and modified parcel projections with explicit input provenance."""
    ordered = sorted(readings, key=lambda item: item.recorded_at)
    if not ordered and config.initial_moisture_mm is None:
        raise ValueError("Provide an initial soil-moisture value when no field reading is available")

    latest = ordered[-1] if ordered else None
    initial = (
        float(config.initial_moisture_mm)
        if config.initial_moisture_mm is not None
        else float(latest.soil_moisture_mm)
    )
    crop_coefficient = (
        float(config.crop_coefficient)
        if config.crop_coefficient is not None
        else CROP_COEFFICIENTS.get(parcel.crop_type, 1.0)
    )
    target_min = _target_minimum(parcel, config.management_allowed_depletion)
    target_refill = _target_refill(parcel, config.refill_depletion)

    template = list(weather_inputs) if weather_inputs is not None else _weather_template(ordered, config.horizon_days)
    if len(template) != config.horizon_days:
        raise ValueError(
            f"Expected {config.horizon_days} daily weather inputs, received {len(template)}"
        )
    start_date = config.start_date or (latest.recorded_at.date() + dt.timedelta(days=1))

    baseline_series = _simulate_series(
        parcel=parcel,
        template=template,
        start_date=start_date,
        initial_moisture=initial,
        crop_coefficient=crop_coefficient,
        target_min=target_min,
        target_refill=target_refill,
        rainfall_factor=1.0,
        et_factor=1.0,
        temperature_delta_c=0.0,
    )
    scenario_series = _simulate_series(
        parcel=parcel,
        template=template,
        start_date=start_date,
        initial_moisture=initial,
        crop_coefficient=crop_coefficient,
        target_min=target_min,
        target_refill=target_refill,
        rainfall_factor=config.rainfall_factor,
        et_factor=config.et_factor,
        temperature_delta_c=config.temperature_delta_c,
    )

    baseline_summary = _summarize_series(baseline_series, initial, target_min, target_refill)
    scenario_summary = _summarize_series(scenario_series, initial, target_min, target_refill)

    return {
        "baseline_summary": baseline_summary,
        "scenario_summary": scenario_summary,
        "deltas": _compute_deltas(baseline_summary, scenario_summary),
        "time_series": _merge_series(baseline_series, scenario_series),
        "assumptions": {
            "model": "single-zone soil water-balance bucket",
            "crop_coefficient": crop_coefficient,
            "temperature_et_sensitivity_per_c": TEMP_ET_SENSITIVITY_PER_C,
            "management_allowed_depletion_fraction": config.management_allowed_depletion,
            "refill_depletion_fraction": config.refill_depletion,
            "weather_source": config.weather_source,
            "forecast_retrieved_at": (
                config.forecast_retrieved_at.isoformat()
                if config.forecast_retrieved_at
                else None
            ),
            "projection_applies_no_irrigation": True,
            "irrigation_need_is_water_required_to_refill_target_when_stressed": True,
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


def _simulate_series(
    *,
    parcel: Parcel,
    template: list[WeatherInput],
    start_date: dt.date,
    initial_moisture: float,
    crop_coefficient: float,
    target_min: float,
    target_refill: float,
    rainfall_factor: float,
    et_factor: float,
    temperature_delta_c: float,
) -> list[dict[str, Any]]:
    moisture = min(max(initial_moisture, 0.0), parcel.field_capacity_mm)
    rows: list[dict[str, Any]] = []
    temp_multiplier = max(0.55, 1.0 + (temperature_delta_c * TEMP_ET_SENSITIVITY_PER_C))

    for index, weather in enumerate(template, start=1):
        rainfall = max(0.0, weather.rainfall_mm * rainfall_factor)
        et0 = max(0.0, weather.et0_fao_mm * et_factor * temp_multiplier)
        crop_et = et0 * crop_coefficient
        temperature = (
            None
            if weather.temperature_c is None
            else float(weather.temperature_c) + temperature_delta_c
        )
        start_moisture = moisture
        moisture = min(parcel.field_capacity_mm, max(0.0, moisture + rainfall - crop_et))
        deficit_to_refill = max(target_refill - moisture, 0.0)
        stress = moisture < target_min
        irrigation_need = deficit_to_refill if stress else 0.0

        rows.append({
            "day": index,
            "date": (start_date + dt.timedelta(days=index - 1)).isoformat(),
            "soil_moisture_start_mm": round(start_moisture, 2),
            "soil_moisture_end_mm": round(moisture, 2),
            "rainfall_mm": round(rainfall, 2),
            "reference_et_mm": round(et0, 2),
            "crop_et_mm": round(crop_et, 2),
            "temperature_c": None if temperature is None else round(temperature, 1),
            "stress": stress,
            "deficit_to_refill_mm": round(deficit_to_refill, 2),
            "irrigation_need_mm": round(irrigation_need, 2),
        })

    return rows


def _summarize_series(
    rows: list[dict[str, Any]],
    initial_moisture: float,
    target_min: float,
    target_refill: float,
) -> dict[str, Any]:
    final = rows[-1]["soil_moisture_end_mm"] if rows else initial_moisture
    min_moisture = min((row["soil_moisture_end_mm"] for row in rows), default=initial_moisture)
    stress_days = sum(1 for row in rows if row["stress"])
    total_need = sum(row["irrigation_need_mm"] for row in rows)
    max_deficit = max((row["deficit_to_refill_mm"] for row in rows), default=0.0)
    risk_score = min(
        100.0,
        (stress_days / max(len(rows), 1)) * 70.0
        + (max_deficit / max(target_refill, 1.0)) * 30.0,
    )

    return {
        "initial_moisture_mm": round(initial_moisture, 2),
        "final_moisture_mm": round(final, 2),
        "min_moisture_mm": round(min_moisture, 2),
        "target_minimum_mm": round(target_min, 2),
        "target_refill_mm": round(target_refill, 2),
        "total_rainfall_mm": round(sum(row["rainfall_mm"] for row in rows), 2),
        "total_crop_et_mm": round(sum(row["crop_et_mm"] for row in rows), 2),
        "total_irrigation_need_mm": round(total_need, 2),
        "stress_days": stress_days,
        "max_deficit_mm": round(max_deficit, 2),
        "risk_score": round(risk_score, 1),
    }


def _compute_deltas(baseline: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "final_moisture_mm",
        "min_moisture_mm",
        "total_rainfall_mm",
        "total_crop_et_mm",
        "total_irrigation_need_mm",
        "stress_days",
        "max_deficit_mm",
        "risk_score",
    ]
    return {key: round(float(scenario[key]) - float(baseline[key]), 2) for key in keys}


def _merge_series(
    baseline: list[dict[str, Any]],
    scenario: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "day": base["day"],
            "date": base["date"],
            "baseline": base,
            "scenario": scenario_row,
            "delta_moisture_mm": round(
                scenario_row["soil_moisture_end_mm"] - base["soil_moisture_end_mm"],
                2,
            ),
            "delta_irrigation_need_mm": round(
                scenario_row["irrigation_need_mm"] - base["irrigation_need_mm"],
                2,
            ),
        }
        for base, scenario_row in zip(baseline, scenario)
    ]
