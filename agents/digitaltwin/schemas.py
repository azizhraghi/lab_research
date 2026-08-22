from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ParcelCreate(BaseModel):
    project_id: Optional[str] = None
    name: str
    code: str
    crop_type: str = "wheat"
    area_ha: float
    latitude: float
    longitude: float
    soil_type: str = "clay loam"
    field_capacity_mm: float = 120.0
    wilting_point_mm: float = 45.0


class SensorReadingInline(BaseModel):
    id: int
    recorded_at: datetime
    soil_moisture_mm: float
    rainfall_mm: float
    evapotranspiration_mm: float
    temperature_c: Optional[float] = None
    quality_flag: str = "ok"
    data_origin: str = "unknown"

    model_config = ConfigDict(from_attributes=True)


class RecommendationInline(BaseModel):
    id: int
    source_reading_id: Optional[int] = None
    generation_mode: str = "manual"
    generated_at: datetime
    recommended_irrigation_mm: float
    water_balance_mm: float
    confidence: float
    rationale: str
    is_validated: bool

    model_config = ConfigDict(from_attributes=True)


class ParcelResponse(BaseModel):
    id: int
    project_id: Optional[str]
    name: str
    code: str
    crop_type: str
    area_ha: float
    latitude: float
    longitude: float
    soil_type: str
    field_capacity_mm: float
    wilting_point_mm: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ParcelDetailResponse(ParcelResponse):
    latest_readings: List[SensorReadingInline] = []
    latest_recommendations: List[RecommendationInline] = []


class SensorReadingCreate(BaseModel):
    recorded_at: datetime
    soil_moisture_mm: float = Field(ge=0.0)
    rainfall_mm: float = Field(0.0, ge=0.0)
    evapotranspiration_mm: float = Field(0.0, ge=0.0)
    temperature_c: Optional[float] = None
    sensor_code: str = ""
    quality_flag: str = "ok"
    data_origin: str = "field"


class SensorReadingResponse(SensorReadingInline):
    parcel_id: int
    sensor_code: str

    model_config = ConfigDict(from_attributes=True)


class WeatherForecastResponse(BaseModel):
    id: int
    parcel_id: int
    forecast_date: date
    issued_at: datetime
    retrieved_at: datetime
    provider: str
    provider_model: str
    precipitation_mm: float
    et0_fao_mm: float
    temperature_mean_c: Optional[float]
    precipitation_probability_pct: Optional[float]
    source_metadata: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class ForecastRefreshResponse(BaseModel):
    parcel_id: int
    provider: str
    provider_model: str
    retrieved_at: datetime
    forecast_days: int
    coverage_start: date
    coverage_end: date
    source_metadata: Dict[str, Any]


class IrrigationEventCreate(BaseModel):
    recommendation_id: Optional[int] = None
    occurred_at: datetime
    amount_mm: float = Field(gt=0.0, le=500.0)
    method: str = ""
    source: str = "field_log"
    notes: Optional[str] = None
    recorded_by: str = Field(min_length=2, max_length=100)


class IrrigationEventResponse(BaseModel):
    id: int
    parcel_id: int
    recommendation_id: Optional[int]
    occurred_at: datetime
    amount_mm: float
    method: str
    source: str
    notes: Optional[str]
    recorded_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalibrationRunRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_observations: int = Field(14, ge=7, le=365)


class CalibrationReviewRequest(BaseModel):
    reviewed_by: str = Field(min_length=2, max_length=100)


class CalibrationProfileResponse(BaseModel):
    id: int
    parcel_id: int
    created_at: datetime
    source_start_date: date
    source_end_date: date
    status: str
    parameters: Dict[str, Any]
    metrics: Dict[str, Any]
    data_quality: Dict[str, Any]
    reviewed_by: Optional[str]
    applied_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class IrrigationRecommendationResponse(BaseModel):
    id: int
    parcel_id: int
    source_reading_id: Optional[int]
    generation_mode: str
    generated_at: datetime
    water_balance_mm: float
    recommended_irrigation_mm: float
    confidence: float
    rationale: str
    is_validated: bool
    validated_by: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class SimulationRequest(BaseModel):
    scenario_name: str = "Custom scenario"
    rainfall_factor: float = Field(1.0, ge=0.0, le=3.0)
    et_factor: float = Field(1.0, ge=0.0, le=3.0)
    temperature_delta_c: float = Field(0.0, ge=-10.0, le=15.0)


class SimulationResponse(BaseModel):
    id: int
    parcel_id: int
    scenario_name: str
    created_at: datetime
    rainfall_factor: float
    et_factor: float
    temperature_delta_c: float
    baseline_irrigation_mm: Optional[float]
    simulated_irrigation_mm: Optional[float]
    baseline_balance_mm: Optional[float]
    simulated_balance_mm: Optional[float]
    ai_analysis: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class SensorReadingImportResponse(BaseModel):
    parcel_id: int
    created: int
    updated: int
    rejected: int
    errors: List[str] = []


class ParcelDeleteResponse(BaseModel):
    """Outcome of removing a parcel.

    Only returned when the parcel had no dependent rows. A parcel with children
    is refused with 409 and the same per-table counts in the error detail, so the
    caller learns what blocks the delete rather than just that it failed.
    """

    deleted_id: int
    code: str
    name: str


class SensorReadingDeleteResponse(BaseModel):
    """Outcome of removing one sensor reading.

    `was_latest` matters: /recommend reads only the newest row by recorded_at, so
    deleting that row changes the next recommendation while any already-stored
    IrrigationRecommendation keeps the old figure (there is no foreign key from a
    recommendation back to the reading it used). `remaining` is 0 when the parcel
    can no longer produce a recommendation at all.
    """

    parcel_id: int
    deleted_id: int
    recorded_at: datetime
    was_latest: bool
    remaining: int
