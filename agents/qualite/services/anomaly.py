"""Physical-plausibility checks for field sensor readings.

`quality_flag` was stored on every reading since the beginning and never
computed from anything — a sensor reporting 200% soil moisture or -5mm of rain
entered the pipeline as trustworthy data. This module turns the flag into a
real verdict using two families of checks:

**Physical ranges** — values a functioning sensor in this climate cannot
produce. Negative rainfall is impossible; soil moisture above ~1.5× the
parcel's field capacity is above saturation; ET above 20mm/day exceeds the
most extreme evaporative demand recorded in arid zones. Thresholds are
deliberately generous: the goal is to catch broken sensors and typos, not to
second-guess unusual weather.

**Rate of change** — soil moisture can only rise as fast as water arrives.
A jump larger than the rainfall on the new reading plus same-day irrigation
plus a small margin is physically unexplainable without an unlogged event.
This is the FAO-56 water balance run as a sanity check, not as a model.

Verdicts:
  - "ok"      — passed everything; eligible to drive automatic advice.
  - "suspect" — physically possible but extreme; needs human eyes before it
                drives anything (blocked from auto-recommendation and
                calibration, exactly like an error, but distinguishable).
  - "error"   — physically impossible; the reading is broken, not interesting.

Every check returns a human-readable message with the offending numbers, so
the rejection event and the UI can say *why* without a lookup table.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

# Range thresholds. Generous by design — see module docstring.
RAINFALL_MAX_MM = 200.0          # extreme-storm ceiling for one reading window
ET_MAX_MM = 20.0                 # extreme evaporative demand per day
TEMPERATURE_RANGE_C = (-30.0, 55.0)
SOIL_MOISTURE_HARD_MAX_MM = 400.0  # beyond any root zone, regardless of parcel
SATURATION_MARGIN = 1.5            # × field capacity ≈ saturation ceiling
RATE_MARGIN_MM = 10.0              # tolerance for unlogged small applications


@dataclass(frozen=True)
class ReadingVerdict:
    flag: str                      # "ok" | "suspect" | "error"
    errors: list[str]
    suspects: list[str]

    @property
    def issues(self) -> list[str]:
        return [f"[error] {m}" for m in self.errors] + [f"[suspect] {m}" for m in self.suspects]


def _number(value: Any) -> Optional[float]:
    """Coerce to float, treating None/empty/NaN as absent."""
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result:  # NaN
        return None
    return result


def check_physical_ranges(
    reading: dict[str, Any],
    field_capacity_mm: Optional[float],
) -> tuple[list[str], list[str]]:
    """Impossible → errors; extreme-but-possible → suspects."""
    errors: list[str] = []
    suspects: list[str] = []

    moisture = _number(reading.get("soil_moisture_mm"))
    if moisture is not None:
        if moisture < 0:
            errors.append(f"soil moisture {moisture:g} mm is negative")
        elif moisture > SOIL_MOISTURE_HARD_MAX_MM:
            errors.append(
                f"soil moisture {moisture:g} mm exceeds {SOIL_MOISTURE_HARD_MAX_MM:g} mm — "
                "no root zone holds that much water"
            )
        elif field_capacity_mm and moisture > field_capacity_mm * SATURATION_MARGIN:
            suspects.append(
                f"soil moisture {moisture:g} mm is above "
                f"{field_capacity_mm * SATURATION_MARGIN:g} mm (saturation ceiling for a "
                f"field capacity of {field_capacity_mm:g} mm)"
            )

    rainfall = _number(reading.get("rainfall_mm"))
    if rainfall is not None:
        if rainfall < 0:
            errors.append(f"rainfall {rainfall:g} mm is negative")
        elif rainfall > RAINFALL_MAX_MM:
            suspects.append(
                f"rainfall {rainfall:g} mm exceeds the {RAINFALL_MAX_MM:g} mm extreme-storm "
                "ceiling — verify the sensor window"
            )

    et = _number(reading.get("evapotranspiration_mm"))
    if et is not None:
        if et < 0:
            errors.append(f"evapotranspiration {et:g} mm is negative")
        elif et > ET_MAX_MM:
            suspects.append(
                f"evapotranspiration {et:g} mm exceeds the {ET_MAX_MM:g} mm/day physical ceiling"
            )

    temperature = _number(reading.get("temperature_c"))
    if temperature is not None:
        low, high = TEMPERATURE_RANGE_C
        if temperature < low or temperature > high:
            errors.append(
                f"temperature {temperature:g}°C is outside the plausible "
                f"[{low:g}, {high:g}]°C range"
            )

    return errors, suspects


def check_rate_of_change(
    reading: dict[str, Any],
    previous: Optional[dict[str, Any]],
    irrigation_same_day_mm: float = 0.0,
) -> list[str]:
    """Soil moisture cannot rise faster than water arrives.

    Plausible rise = rainfall on the new reading + logged irrigation that day
    + a small margin for unlogged applications. Applies to rises only: a fast
    *fall* (drainage, extraction) has no equivalent hard ceiling, and the
    saturation check above already bounds the absolute value.
    """
    if previous is None:
        return []
    moisture = _number(reading.get("soil_moisture_mm"))
    previous_moisture = _number(previous.get("soil_moisture_mm"))
    if moisture is None or previous_moisture is None:
        return []

    jump = moisture - previous_moisture
    if jump <= 0:
        return []

    rainfall = _number(reading.get("rainfall_mm")) or 0.0
    plausible_rise = rainfall + max(0.0, irrigation_same_day_mm) + RATE_MARGIN_MM
    if jump > plausible_rise:
        return [
            f"soil moisture rose {jump:g} mm since the previous reading but only "
            f"{plausible_rise:g} mm of water arrived (rain {rainfall:g} mm + irrigation "
            f"{max(0.0, irrigation_same_day_mm):g} mm + {RATE_MARGIN_MM:g} mm margin) — "
            "an application was likely not logged"
        ]
    return []


def verdict_for(
    reading: dict[str, Any],
    field_capacity_mm: Optional[float] = None,
    previous: Optional[dict[str, Any]] = None,
    irrigation_same_day_mm: float = 0.0,
) -> ReadingVerdict:
    """Full check → one verdict. Structurally invalid timestamps stay errors."""
    errors, suspects = check_physical_ranges(reading, field_capacity_mm)
    suspects.extend(check_rate_of_change(reading, previous, irrigation_same_day_mm))

    recorded_at = reading.get("recorded_at")
    try:
        if isinstance(recorded_at, str):
            if datetime.fromisoformat(recorded_at) > datetime.utcnow():
                errors.append("reading timestamp is in the future")
    except ValueError:
        errors.append("reading timestamp is invalid")

    flag = "error" if errors else ("suspect" if suspects else "ok")
    return ReadingVerdict(flag=flag, errors=errors, suspects=suspects)
