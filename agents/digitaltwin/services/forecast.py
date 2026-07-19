from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.digitaltwin.models import Parcel, WeatherForecast

FORECAST_PROVIDER = "open-meteo"
FORECAST_MODEL = "best_match"
MAX_FORECAST_DAYS = 16
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass(frozen=True)
class WeatherInput:
    rainfall_mm: float
    et0_fao_mm: float
    temperature_c: float | None = None


@dataclass(frozen=True)
class ForecastCoverage:
    inputs: list[WeatherInput]
    start_date: dt.date
    end_date: dt.date
    retrieved_at: dt.datetime
    provider: str
    provider_model: str


async def refresh_parcel_forecast(
    db: AsyncSession,
    parcel: Parcel,
    forecast_days: int = MAX_FORECAST_DAYS,
) -> ForecastCoverage:
    """Fetch and append a traceable Open-Meteo daily forecast for one parcel."""
    if parcel.latitude is None or parcel.longitude is None:
        raise ValueError("Parcel latitude and longitude are required for weather forecasts")

    requested_days = min(max(forecast_days, 1), MAX_FORECAST_DAYS)
    params = {
        "latitude": parcel.latitude,
        "longitude": parcel.longitude,
        "daily": (
            "precipitation_sum,et0_fao_evapotranspiration,"
            "temperature_2m_mean,precipitation_probability_max"
        ),
        "timezone": "auto",
        "forecast_days": requested_days,
        "models": FORECAST_MODEL,
    }
    retrieved_at = dt.datetime.utcnow()

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(FORECAST_URL, params=params)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValueError(f"Forecast provider request failed: {exc}") from exc

    payload = response.json()
    daily = payload.get("daily")
    if not isinstance(daily, dict):
        raise ValueError("Forecast provider returned no daily forecast data")

    dates = daily.get("time") or []
    rain = daily.get("precipitation_sum") or []
    et0 = daily.get("et0_fao_evapotranspiration") or []
    temperatures = daily.get("temperature_2m_mean") or []
    probabilities = daily.get("precipitation_probability_max") or []
    length = min(len(dates), len(rain), len(et0))
    if length < 1:
        raise ValueError("Forecast provider returned incomplete rainfall or ET0 data")

    source_metadata = {
        "request_url": FORECAST_URL,
        "timezone": payload.get("timezone"),
        "provider_latitude": payload.get("latitude"),
        "provider_longitude": payload.get("longitude"),
        "provider_elevation_m": payload.get("elevation"),
        "provider_issue_time_available": False,
        "note": "Provider issue time is not exposed; retrieved_at is the system retrieval timestamp.",
    }

    inputs: list[WeatherInput] = []
    parsed_dates: list[dt.date] = []
    for index in range(length):
        try:
            forecast_date = dt.date.fromisoformat(dates[index])
        except (TypeError, ValueError) as exc:
            raise ValueError("Forecast provider returned an invalid forecast date") from exc

        precipitation = float(rain[index] or 0.0)
        reference_et0 = float(et0[index] or 0.0)
        temperature = None if index >= len(temperatures) or temperatures[index] is None else float(temperatures[index])
        probability = None if index >= len(probabilities) or probabilities[index] is None else float(probabilities[index])

        db.add(
            WeatherForecast(
                parcel_id=parcel.id,
                forecast_date=forecast_date,
                issued_at=retrieved_at,
                retrieved_at=retrieved_at,
                provider=FORECAST_PROVIDER,
                provider_model=FORECAST_MODEL,
                precipitation_mm=max(0.0, precipitation),
                et0_fao_mm=max(0.0, reference_et0),
                temperature_mean_c=temperature,
                precipitation_probability_pct=probability,
                source_metadata=source_metadata,
            )
        )
        parsed_dates.append(forecast_date)
        inputs.append(
            WeatherInput(
                rainfall_mm=max(0.0, precipitation),
                et0_fao_mm=max(0.0, reference_et0),
                temperature_c=temperature,
            )
        )

    await db.flush()
    return ForecastCoverage(
        inputs=inputs,
        start_date=parsed_dates[0],
        end_date=parsed_dates[-1],
        retrieved_at=retrieved_at,
        provider=FORECAST_PROVIDER,
        provider_model=FORECAST_MODEL,
    )


async def get_current_forecast_coverage(
    db: AsyncSession,
    parcel_id: int,
    horizon_days: int,
    start_date: dt.date,
) -> ForecastCoverage:
    """Return the newest stored forecast issue for every required future date."""
    if horizon_days > MAX_FORECAST_DAYS:
        raise ValueError(
            f"Forecast-backed runs support up to {MAX_FORECAST_DAYS} days; "
            f"requested {horizon_days}."
        )

    end_date = start_date + dt.timedelta(days=horizon_days - 1)
    stmt = (
        select(WeatherForecast)
        .where(
            WeatherForecast.parcel_id == parcel_id,
            WeatherForecast.forecast_date >= start_date,
            WeatherForecast.forecast_date <= end_date,
        )
        .order_by(WeatherForecast.forecast_date.asc(), WeatherForecast.retrieved_at.desc())
    )
    result = await db.execute(stmt)

    newest_by_date: dict[dt.date, WeatherForecast] = {}
    for row in result.scalars().all():
        newest_by_date.setdefault(row.forecast_date, row)

    expected_dates = [start_date + dt.timedelta(days=index) for index in range(horizon_days)]
    missing = [item.isoformat() for item in expected_dates if item not in newest_by_date]
    if missing:
        raise ValueError(
            "Forecast coverage is incomplete. Refresh the parcel forecast and run "
            f"within its available range. Missing dates: {', '.join(missing[:3])}"
        )

    rows = [newest_by_date[item] for item in expected_dates]
    providers = {row.provider for row in rows}
    models = {row.provider_model for row in rows}
    return ForecastCoverage(
        inputs=[
            WeatherInput(
                rainfall_mm=row.precipitation_mm,
                et0_fao_mm=row.et0_fao_mm,
                temperature_c=row.temperature_mean_c,
            )
            for row in rows
        ],
        start_date=start_date,
        end_date=end_date,
        retrieved_at=max(row.retrieved_at for row in rows),
        provider=", ".join(sorted(providers)),
        provider_model=", ".join(sorted(models)),
    )


async def list_current_forecasts(
    db: AsyncSession,
    parcel_id: int,
    days: int = MAX_FORECAST_DAYS,
) -> list[WeatherForecast]:
    """Return one latest forecast value per date for the upcoming window."""
    start_date = dt.date.today()
    end_date = start_date + dt.timedelta(days=min(max(days, 1), MAX_FORECAST_DAYS) - 1)
    stmt = (
        select(WeatherForecast)
        .where(
            WeatherForecast.parcel_id == parcel_id,
            WeatherForecast.forecast_date >= start_date,
            WeatherForecast.forecast_date <= end_date,
        )
        .order_by(WeatherForecast.forecast_date.asc(), WeatherForecast.retrieved_at.desc())
    )
    result = await db.execute(stmt)

    newest_by_date: dict[dt.date, WeatherForecast] = {}
    for row in result.scalars().all():
        newest_by_date.setdefault(row.forecast_date, row)
    return [newest_by_date[key] for key in sorted(newest_by_date)]


async def get_active_crop_coefficient(
    db: AsyncSession,
    parcel_id: int,
    fallback: float,
) -> tuple[float, dict[str, Any]]:
    """Use only a human-applied calibration profile; candidates never affect runs."""
    from agents.digitaltwin.models import CalibrationProfile

    stmt = (
        select(CalibrationProfile)
        .where(
            CalibrationProfile.parcel_id == parcel_id,
            CalibrationProfile.status == "applied",
        )
        .order_by(CalibrationProfile.applied_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        return fallback, {
            "calibration_status": "not_applied",
            "calibration_profile_id": None,
        }

    coefficient = profile.parameters.get("crop_coefficient")
    if coefficient is None:
        return fallback, {
            "calibration_status": "applied_without_crop_coefficient",
            "calibration_profile_id": profile.id,
        }
    return float(coefficient), {
        "calibration_status": "applied",
        "calibration_profile_id": profile.id,
        "calibration_applied_at": profile.applied_at.isoformat() if profile.applied_at else None,
    }