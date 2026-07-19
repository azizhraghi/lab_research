"""
Simulation engine — runs "what-if" scenarios on the digital twin.

Applies modification factors to sensor data, runs the irrigation model
on both baseline and modified inputs, then uses Mistral AI to generate
a natural-language comparative analysis.
"""
from __future__ import annotations

from agents.digitaltwin.services.irrigation import (
    IrrigationInput,
    IrrigationResult,
    CROP_COEFFICIENTS,
    calculate_irrigation_recommendation,
)
from shared.llm_client import llm_client


async def run_simulation(
    *,
    soil_moisture_mm: float,
    field_capacity_mm: float,
    wilting_point_mm: float,
    rainfall_mm: float,
    evapotranspiration_mm: float,
    crop_type: str,
    parcel_name: str,
    # Scenario modifiers
    rainfall_factor: float = 1.0,
    et_factor: float = 1.0,
    temperature_delta_c: float = 0.0,
    scenario_name: str = "Custom scenario",
) -> dict:
    """
    Run a baseline vs. modified scenario comparison.

    Returns a dict with baseline results, simulated results, and AI analysis.
    """
    kc = CROP_COEFFICIENTS.get(crop_type, 1.0)

    # ── Baseline (current conditions) ───────────────
    baseline_input = IrrigationInput(
        soil_moisture_mm=soil_moisture_mm,
        field_capacity_mm=field_capacity_mm,
        wilting_point_mm=wilting_point_mm,
        rainfall_mm=rainfall_mm,
        evapotranspiration_mm=evapotranspiration_mm,
        crop_coefficient=kc,
    )
    baseline: IrrigationResult = calculate_irrigation_recommendation(baseline_input)

    # ── Modified scenario ───────────────────────────
    modified_input = IrrigationInput(
        soil_moisture_mm=soil_moisture_mm,
        field_capacity_mm=field_capacity_mm,
        wilting_point_mm=wilting_point_mm,
        rainfall_mm=rainfall_mm * rainfall_factor,
        evapotranspiration_mm=evapotranspiration_mm * et_factor,
        crop_coefficient=kc,
    )
    simulated: IrrigationResult = calculate_irrigation_recommendation(modified_input)

    # ── AI-generated analysis ───────────────────────
    try:
        ai_analysis = await _generate_analysis(
            parcel_name=parcel_name,
            crop_type=crop_type,
            scenario_name=scenario_name,
            baseline=baseline,
            simulated=simulated,
            rainfall_factor=rainfall_factor,
            et_factor=et_factor,
            temperature_delta_c=temperature_delta_c,
        )
    except Exception as e:
        ai_analysis = f"AI analysis unavailable: {e}"

    return {
        "baseline_irrigation_mm": baseline.recommended_irrigation_mm,
        "baseline_balance_mm": baseline.water_balance_mm,
        "simulated_irrigation_mm": simulated.recommended_irrigation_mm,
        "simulated_balance_mm": simulated.water_balance_mm,
        "ai_analysis": ai_analysis,
    }


async def _generate_analysis(
    *,
    parcel_name: str,
    crop_type: str,
    scenario_name: str,
    baseline: IrrigationResult,
    simulated: IrrigationResult,
    rainfall_factor: float,
    et_factor: float,
    temperature_delta_c: float,
) -> str:
    """Use Mistral AI to generate a comparative analysis of the two scenarios."""

    delta_irrigation = simulated.recommended_irrigation_mm - baseline.recommended_irrigation_mm
    delta_balance = simulated.water_balance_mm - baseline.water_balance_mm

    prompt = f"""You are an agricultural water management expert at a Tunisian research laboratory.
Compare a baseline irrigation scenario with a "what-if" simulation for a {crop_type} parcel called "{parcel_name}".

## Scenario: {scenario_name}
- Rainfall factor: {rainfall_factor}x ({'+' if rainfall_factor >= 1 else ''}{(rainfall_factor - 1) * 100:.0f}%)
- Evapotranspiration factor: {et_factor}x ({'+' if et_factor >= 1 else ''}{(et_factor - 1) * 100:.0f}%)
- Temperature change: {temperature_delta_c:+.1f}°C

## Baseline Results
- Water balance: {baseline.water_balance_mm:+.1f} mm
- Recommended irrigation: {baseline.recommended_irrigation_mm:.1f} mm
- Confidence: {baseline.confidence:.0%}

## Simulated Results
- Water balance: {simulated.water_balance_mm:+.1f} mm  (Δ {delta_balance:+.1f} mm)
- Recommended irrigation: {simulated.recommended_irrigation_mm:.1f} mm  (Δ {delta_irrigation:+.1f} mm)
- Confidence: {simulated.confidence:.0%}

Write a concise 3-paragraph analysis in English:
1. What changed and why
2. Impact on the crop and water resources
3. Recommended action for the laboratory team

Keep it under 200 words. Be specific with numbers."""

    response = await llm_client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    return response.strip()
