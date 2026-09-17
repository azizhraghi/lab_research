from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.digitaltwin.models import (
    CalibrationProfile,
    IrrigationEvent,
    Parcel,
    SensorReading,
)

from agents.digitaltwin.services.eligibility import FIELD_ORIGINS, is_reviewed_field_reading

FIELD_DATA_ORIGINS = FIELD_ORIGINS
CROP_COEFFICIENT_MULTIPLIERS = tuple(round(0.60 + step * 0.05, 2) for step in range(17))
FIELD_CAPACITY_MULTIPLIERS = (0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15)


async def create_calibration_candidate(
    db: AsyncSession,
    parcel: Parcel,
    start_date: dt.date | None,
    end_date: dt.date | None,
    min_observations: int,
) -> CalibrationProfile:
    """Fit a reviewable water-balance profile from daily field observations.

    This deliberately produces a candidate. It does not change live model
    parameters until a named lab reviewer applies it.
    """
    stmt = (
        select(SensorReading)
        .where(SensorReading.parcel_id == parcel.id)
        .order_by(SensorReading.recorded_at.asc())
    )
    result = await db.execute(stmt)
    all_readings = result.scalars().all()

    field_readings = [
        row
        for row in all_readings
        if is_reviewed_field_reading(row)
    ]
    if start_date:
        field_readings = [row for row in field_readings if row.recorded_at.date() >= start_date]
    if end_date:
        field_readings = [row for row in field_readings if row.recorded_at.date() <= end_date]

    if len(field_readings) < min_observations:
        raise ValueError(
            f"Calibration needs at least {min_observations} quality-checked field readings. "
            "Demo, unknown, and synthetic readings are intentionally excluded."
        )

    # One root-zone observation per calendar day; prefer the latest reading.
    by_day: dict[dt.date, SensorReading] = {}
    for reading in field_readings:
        current = by_day.get(reading.recorded_at.date())
        if current is None or reading.recorded_at > current.recorded_at:
            by_day[reading.recorded_at.date()] = reading

    dates = sorted(by_day)
    first_date, last_date = dates[0], dates[-1]
    expected_days = (last_date - first_date).days + 1
    if len(dates) < min_observations or len(dates) != expected_days:
        raise ValueError(
            "Calibration requires one quality-checked root-zone observation for every "
            "day in the selected period. Fill measurement gaps before calibration."
        )

    events_stmt = (
        select(IrrigationEvent)
        .where(
            IrrigationEvent.parcel_id == parcel.id,
            IrrigationEvent.occurred_at >= dt.datetime.combine(first_date, dt.time.min),
            IrrigationEvent.occurred_at <= dt.datetime.combine(last_date, dt.time.max),
        )
        .order_by(IrrigationEvent.occurred_at.asc())
    )
    events_result = await db.execute(events_stmt)
    irrigation_by_day: dict[dt.date, float] = defaultdict(float)
    irrigation_events = events_result.scalars().all()
    for event in irrigation_events:
        irrigation_by_day[event.occurred_at.date()] += float(event.amount_mm)

    base_kc = _default_crop_coefficient(parcel.crop_type)
    best: dict[str, Any] | None = None
    for kc_multiplier in CROP_COEFFICIENT_MULTIPLIERS:
        candidate_kc = base_kc * kc_multiplier
        for fc_multiplier in FIELD_CAPACITY_MULTIPLIERS:
            candidate_fc = max(
                parcel.wilting_point_mm + 1.0,
                parcel.field_capacity_mm * fc_multiplier,
            )
            metrics = _evaluate_candidate(
                observations=[by_day[item] for item in dates],
                irrigation_by_day=irrigation_by_day,
                crop_coefficient=candidate_kc,
                field_capacity_mm=candidate_fc,
            )
            if best is None or metrics["rmse_mm"] < best["metrics"]["rmse_mm"]:
                best = {
                    "crop_coefficient": candidate_kc,
                    "field_capacity_mm": candidate_fc,
                    "metrics": metrics,
                }

    assert best is not None
    data_quality = {
        "observation_count": len(dates),
        "calendar_days": expected_days,
        "coverage_pct": 100.0,
        "irrigation_event_count": len(irrigation_events),
        "measurement_requirement": (
            "soil_moisture_mm must be root-zone water storage in mm; "
            "single-depth volumetric sensor values must be converted before import."
        ),
        "accepted_data_origins": sorted(FIELD_DATA_ORIGINS),
        "weather_inputs": "rainfall_mm and evapotranspiration_mm attached to field readings",
        "status": "review_required",
        "evaluation_method": "in-sample fit; independent field validation not performed",
    }
    parameters = {
        "crop_coefficient": round(best["crop_coefficient"], 3),
        "field_capacity_mm": round(best["field_capacity_mm"], 2),
        "wilting_point_mm": parcel.wilting_point_mm,
        "base_crop_coefficient": base_kc,
        "calibration_method": "bounded grid search on multi-day water-balance RMSE",
        "irrigation_timing_assumption": "Applied within the calendar day before daily state comparison.",
    }

    profile = CalibrationProfile(
        parcel_id=parcel.id,
        source_start_date=first_date,
        source_end_date=last_date,
        status="candidate",
        parameters=parameters,
        metrics=best["metrics"],
        data_quality=data_quality,
    )
    db.add(profile)
    await db.flush()
    return profile


async def apply_calibration_profile(
    db: AsyncSession,
    profile_id: int,
    reviewed_by: str,
) -> CalibrationProfile:
    """Apply a reviewed candidate and supersede the prior active profile."""
    profile = await db.get(CalibrationProfile, profile_id)
    if not profile:
        raise ValueError("Calibration profile not found")
    if profile.status != "candidate":
        raise ValueError("Only a candidate calibration profile can be applied")

    parcel = await db.get(Parcel, profile.parcel_id)
    if not parcel:
        raise ValueError("Parcel not found")

    prior_stmt = select(CalibrationProfile).where(
        CalibrationProfile.parcel_id == profile.parcel_id,
        CalibrationProfile.status == "applied",
    )
    prior_result = await db.execute(prior_stmt)
    for prior in prior_result.scalars().all():
        prior.status = "superseded"

    proposed_fc = profile.parameters.get("field_capacity_mm")
    if proposed_fc is not None:
        parcel.field_capacity_mm = float(proposed_fc)

    profile.status = "applied"
    profile.reviewed_by = reviewed_by.strip()
    profile.applied_at = dt.datetime.utcnow()
    await db.flush()
    return profile


def _evaluate_candidate(
    *,
    observations: list[SensorReading],
    irrigation_by_day: dict[dt.date, float],
    crop_coefficient: float,
    field_capacity_mm: float,
) -> dict[str, float]:
    predicted = min(max(float(observations[0].soil_moisture_mm), 0.0), field_capacity_mm)
    errors: list[float] = []

    for observation in observations[1:]:
        rainfall = max(0.0, float(observation.rainfall_mm or 0.0))
        et0 = max(0.0, float(observation.evapotranspiration_mm or 0.0))
        irrigation = max(0.0, irrigation_by_day.get(observation.recorded_at.date(), 0.0))
        predicted = min(
            field_capacity_mm,
            max(0.0, predicted + rainfall + irrigation - (et0 * crop_coefficient)),
        )
        errors.append(predicted - float(observation.soil_moisture_mm))

    if not errors:
        raise ValueError("Calibration needs at least two daily observations")

    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = math.sqrt(sum(error * error for error in errors) / len(errors))
    bias = sum(errors) / len(errors)
    return {
        "mae_mm": round(mae, 2),
        "rmse_mm": round(rmse, 2),
        "bias_mm": round(bias, 2),
        "validation_observations": len(errors),  # Legacy response compatibility.
        "fit_observations": len(errors),
    }


def _default_crop_coefficient(crop_type: str) -> float:
    from agents.digitaltwin.services.irrigation import CROP_COEFFICIENTS

    return float(CROP_COEFFICIENTS.get(crop_type, 1.0))
