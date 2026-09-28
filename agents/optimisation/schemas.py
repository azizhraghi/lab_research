from datetime import date, datetime
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field


class OptimizationRunRequest(BaseModel):
    mode: Literal["demonstration", "field"] = "field"
    initial_moisture_mm: Optional[float] = Field(None, ge=0.0, allow_inf_nan=False)
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
    is_approved: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class IrrigationScheduleTaskResponse(BaseModel):
    id: int
    optimization_run_id: int
    parcel_id: int
    scheduled_date: date
    planned_amount_mm: float
    status: str
    assigned_to: Optional[str] = None
    approved_by: str
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    actual_amount_mm: Optional[float] = None
    notes: Optional[str] = None
    irrigation_event_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompleteScheduleTaskRequest(BaseModel):
    actual_amount_mm: float = Field(gt=0.0, le=500.0)
    occurred_at: datetime
    notes: Optional[str] = Field(None, max_length=2000)
