from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OptimizationRunRequest(BaseModel):
    run_name: str = "Constrained irrigation schedule"
    horizon_days: int = Field(14, ge=3, le=16)
    max_irrigation_mm_per_day: float = Field(25.0, ge=1.0, le=80.0)
    water_quota_mm: Optional[float] = Field(
        None,
        ge=0.0,
        description="Total available irrigation water over the forecast horizon",
    )
    rainfall_factor: float = Field(1.0, ge=0.0, le=3.0)
    et_factor: float = Field(1.0, ge=0.0, le=3.0)
    temperature_delta_c: float = Field(0.0, ge=-10.0, le=15.0)
    trigger_depletion_fraction: float = Field(0.45, ge=0.05, le=0.9)
    refill_depletion_fraction: float = Field(0.15, ge=0.0, le=0.8)


class OptimizationRunResponse(BaseModel):
    id: int
    parcel_id: int
    created_at: datetime
    run_name: str
    horizon_days: int
    max_irrigation_mm_per_day: float
    water_quota_mm: Optional[float]
    rainfall_factor: float
    et_factor: float
    temperature_delta_c: float
    constraints: Dict[str, Any]
    summary: Dict[str, Any]
    schedule: List[Dict[str, Any]]
    assumptions: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)