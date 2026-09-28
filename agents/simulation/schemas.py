from datetime import datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field


class SimulationRunRequest(BaseModel):
    mode: Literal["demonstration", "field"] = "field"
    scenario_name: str = "Drought stress scenario"
    horizon_days: int = Field(14, ge=3, le=16)
    rainfall_factor: float = Field(0.7, ge=0.0, le=3.0)
    et_factor: float = Field(1.15, ge=0.0, le=3.0)
    temperature_delta_c: float = Field(2.0, ge=-10.0, le=15.0)
    initial_moisture_mm: Optional[float] = Field(None, ge=0.0, allow_inf_nan=False)


class SimulationRunResponse(BaseModel):
    id: int
    parcel_id: int
    created_at: datetime
    scenario_name: str
    horizon_days: int
    rainfall_factor: float
    et_factor: float
    temperature_delta_c: float
    initial_moisture_mm: Optional[float]
    baseline_summary: Dict[str, Any]
    scenario_summary: Dict[str, Any]
    deltas: Dict[str, Any]
    time_series: List[Dict[str, Any]]
    assumptions: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)