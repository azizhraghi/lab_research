"""
Physics-based irrigation recommendation engine.

Ported from the internship project's Django service (services.py).
Uses a simplified water-balance model to compute deficit and recommendation.
"""
from __future__ import annotations

from dataclasses import dataclass


# ── Crop coefficients (Kc) ──────────────────────────
# Standard FAO-56 values for typical growth stages.
CROP_COEFFICIENTS: dict[str, float] = {
    "wheat": 0.95,
    "olive": 0.65,
    "citrus": 0.85,
    "vegetable": 1.05,
    "forage": 1.10,
}


@dataclass(frozen=True)
class IrrigationInput:
    soil_moisture_mm: float
    field_capacity_mm: float
    wilting_point_mm: float
    rainfall_mm: float = 0.0
    evapotranspiration_mm: float = 0.0
    crop_coefficient: float = 1.0


@dataclass(frozen=True)
class IrrigationResult:
    water_balance_mm: float
    recommended_irrigation_mm: float
    confidence: float
    rationale: str


def calculate_irrigation_recommendation(inp: IrrigationInput) -> IrrigationResult:
    """
    Compute an irrigation recommendation using a simplified water-balance model.

    Steps:
      1. available_water = current soil moisture − wilting point (>= 0)
      2. target_water = field capacity − wilting point
      3. recent_balance = rainfall − (ET × crop_coefficient)
      4. projected_available = available_water + recent_balance
      5. deficit = target − projected (>= 0)
      6. recommendation = min(deficit, 35% of field_capacity) — safety cap
      7. confidence = 0.65 + stress_ratio × 0.25
    """
    available_water = max(inp.soil_moisture_mm - inp.wilting_point_mm, 0.0)
    target_water = inp.field_capacity_mm - inp.wilting_point_mm

    recent_balance = inp.rainfall_mm - (inp.evapotranspiration_mm * inp.crop_coefficient)
    projected_available = available_water + recent_balance

    deficit = max(target_water - projected_available, 0.0)
    recommendation = round(min(deficit, inp.field_capacity_mm * 0.35), 2)
    water_balance = round(projected_available - target_water, 2)

    # Confidence: higher when stress is low
    stress_ratio = max(0.0, min(1.0, projected_available / target_water)) if target_water > 0 else 1.0
    confidence = round(0.65 + stress_ratio * 0.25, 2)

    if recommendation == 0:
        rationale = (
            "Soil water reserve is within the target range; "
            "no irrigation is recommended for the next cycle."
        )
    else:
        rationale = (
            f"Projected water reserve is {abs(water_balance):.1f} mm below the target range. "
            f"Apply {recommendation:.1f} mm while monitoring rainfall and sensor quality."
        )

    return IrrigationResult(
        water_balance_mm=water_balance,
        recommended_irrigation_mm=recommendation,
        confidence=confidence,
        rationale=rationale,
    )
