"""Shared eligibility checks for operational water calculations."""
from datetime import datetime, timedelta, timezone
import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.digitaltwin.models import Parcel, SensorReading
from shared.config import settings

FIELD_ORIGINS = {"field", "field_import", "gateway"}
ACCEPTED_REVIEWS = {"not_required", "accepted", "corrected"}


def is_reviewed_field_reading(reading: SensorReading) -> bool:
    return (reading.quality_flag == "ok"
            and reading.review_status in ACCEPTED_REVIEWS
            and reading.data_origin in FIELD_ORIGINS)


def validate_parcel_parameters(parcel: Parcel) -> None:
    values = (parcel.area_ha, parcel.latitude, parcel.longitude,
              parcel.field_capacity_mm, parcel.wilting_point_mm)
    if any(value is None or not math.isfinite(value) for value in values):
        raise ValueError("Parcel parameters must be finite numbers.")
    if (parcel.area_ha <= 0 or not -90 <= parcel.latitude <= 90
            or not -180 <= parcel.longitude <= 180
            or not 0 <= parcel.wilting_point_mm < parcel.field_capacity_mm):
        raise ValueError("Correct the parcel area, coordinates and soil-water range before modeling.")


async def operational_readings(db: AsyncSession, parcel: Parcel,
                               source_reading_id: int | None = None) -> list[SensorReading]:
    """Fail closed on the newest measurement; do not silently use older good data."""
    validate_parcel_parameters(parcel)
    rows = list((await db.execute(select(SensorReading).where(
        SensorReading.parcel_id == parcel.id,
    ).order_by(SensorReading.recorded_at.asc(), SensorReading.id.asc()))).scalars())
    if not rows:
        raise ValueError("Record a field measurement before requesting advice.")
    latest = rows[-1]
    if source_reading_id is not None and latest.id != source_reading_id:
        raise ValueError("A newer measurement exists. Review it and generate new advice.")
    if not is_reviewed_field_reading(latest):
        raise ValueError("The latest measurement must be quality-checked field data with no pending or rejected review. Demo/test data cannot drive operational advice.")
    if latest.recorded_at is None:
        raise ValueError("The latest measurement needs a timestamp.")
    observed = latest.recorded_at.replace(tzinfo=timezone.utc) if latest.recorded_at.tzinfo is None else latest.recorded_at.astimezone(timezone.utc)
    age = datetime.now(timezone.utc) - observed
    if age < -timedelta(minutes=5):
        raise ValueError("The latest measurement is dated in the future. Correct its timestamp.")
    if age > timedelta(hours=settings.SENSOR_STALE_AFTER_HOURS):
        raise ValueError(f"The latest measurement is older than {settings.SENSOR_STALE_AFTER_HOURS} hours. Record a current measurement.")
    return [row for row in rows if is_reviewed_field_reading(row)]
