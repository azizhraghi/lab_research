from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean, JSON
)
from sqlalchemy.orm import relationship
from shared.database import Base
import datetime


class Parcel(Base):
    """An irrigated parcel — the core entity of the digital twin."""
    __tablename__ = "twin_parcels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True, index=True)
    crop_type = Column(String)
    area_ha = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    soil_type = Column(String)
    field_capacity_mm = Column(Float, default=120.0)
    wilting_point_mm = Column(Float, default=45.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    sensor_readings = relationship(
        "SensorReading", back_populates="parcel",
        order_by="SensorReading.recorded_at.desc()",
    )
    recommendations = relationship(
        "IrrigationRecommendation", back_populates="parcel",
        order_by="IrrigationRecommendation.generated_at.desc()",
    )
    simulations = relationship(
        "SimulationScenario", back_populates="parcel",
        order_by="SimulationScenario.created_at.desc()",
    )
    weather_forecasts = relationship(
        "WeatherForecast", back_populates="parcel",
        order_by="WeatherForecast.forecast_date.asc()",
    )
    irrigation_events = relationship(
        "IrrigationEvent", back_populates="parcel",
        order_by="IrrigationEvent.occurred_at.desc()",
    )
    calibration_profiles = relationship(
        "CalibrationProfile", back_populates="parcel",
        order_by="CalibrationProfile.created_at.desc()",
    )

    def __repr__(self):
        return f"<Parcel {self.code}: {self.name}>"


class SensorReading(Base):
    """Root-zone soil-water observations and associated measured weather inputs."""
    __tablename__ = "twin_sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey("twin_parcels.id"), index=True)
    recorded_at = Column(DateTime, index=True)
    soil_moisture_mm = Column(Float)
    rainfall_mm = Column(Float, default=0.0)
    evapotranspiration_mm = Column(Float, default=0.0)
    temperature_c = Column(Float, nullable=True)
    sensor_code = Column(String, default="")
    quality_flag = Column(String, default="ok")
    data_origin = Column(String, default="unknown", nullable=False)

    parcel = relationship("Parcel", back_populates="sensor_readings")

    def __repr__(self):
        return f"<SensorReading parcel={self.parcel_id} at={self.recorded_at}>"


class WeatherForecast(Base):
    """One issued weather forecast value for a parcel and forecast date.

    Forecast rows are append-only. The latest retrieval for a date is the active
    value, while prior issues remain available for forecast-performance auditing.
    """
    __tablename__ = "twin_weather_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey("twin_parcels.id"), index=True, nullable=False)
    forecast_date = Column(Date, index=True, nullable=False)
    issued_at = Column(DateTime, nullable=False)
    retrieved_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    provider = Column(String, nullable=False, default="open-meteo")
    provider_model = Column(String, nullable=False, default="best_match")
    precipitation_mm = Column(Float, nullable=False)
    et0_fao_mm = Column(Float, nullable=False)
    temperature_mean_c = Column(Float, nullable=True)
    precipitation_probability_pct = Column(Float, nullable=True)
    source_metadata = Column(JSON, nullable=False, default=dict)

    parcel = relationship("Parcel", back_populates="weather_forecasts")


class IrrigationEvent(Base):
    """A recorded, human-confirmed irrigation application used for calibration."""
    __tablename__ = "twin_irrigation_events"

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey("twin_parcels.id"), index=True, nullable=False)
    occurred_at = Column(DateTime, index=True, nullable=False)
    amount_mm = Column(Float, nullable=False)
    method = Column(String, default="", nullable=False)
    source = Column(String, default="field_log", nullable=False)
    notes = Column(Text, nullable=True)
    recorded_by = Column(String, default="", nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    parcel = relationship("Parcel", back_populates="irrigation_events")


class CalibrationProfile(Base):
    """Versioned calibration candidate or human-applied field profile."""
    __tablename__ = "twin_calibration_profiles"

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey("twin_parcels.id"), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    source_start_date = Column(Date, nullable=False)
    source_end_date = Column(Date, nullable=False)
    status = Column(String, default="candidate", nullable=False)
    parameters = Column(JSON, nullable=False)
    metrics = Column(JSON, nullable=False)
    data_quality = Column(JSON, nullable=False)
    reviewed_by = Column(String, nullable=True)
    applied_at = Column(DateTime, nullable=True)

    parcel = relationship("Parcel", back_populates="calibration_profiles")


class IrrigationRecommendation(Base):
    """Irrigation advice based on sensor data and the water-balance model."""
    __tablename__ = "twin_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey("twin_parcels.id"), index=True)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)
    water_balance_mm = Column(Float)
    recommended_irrigation_mm = Column(Float)
    confidence = Column(Float, default=0.75)
    rationale = Column(Text)
    is_validated = Column(Boolean, default=False)
    validated_by = Column(String, nullable=True)

    parcel = relationship("Parcel", back_populates="recommendations")

    def __repr__(self):
        return f"<Recommendation parcel={self.parcel_id} irrigation={self.recommended_irrigation_mm}mm>"


class SimulationScenario(Base):
    """Legacy one-step what-if scenario, retained for compatibility."""
    __tablename__ = "twin_simulations"

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey("twin_parcels.id"), index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    scenario_name = Column(String)
    rainfall_factor = Column(Float, default=1.0)
    et_factor = Column(Float, default=1.0)
    temperature_delta_c = Column(Float, default=0.0)
    baseline_irrigation_mm = Column(Float, nullable=True)
    simulated_irrigation_mm = Column(Float, nullable=True)
    baseline_balance_mm = Column(Float, nullable=True)
    simulated_balance_mm = Column(Float, nullable=True)
    ai_analysis = Column(Text, nullable=True)

    parcel = relationship("Parcel", back_populates="simulations")

    def __repr__(self):
        return f"<Simulation '{self.scenario_name}' parcel={self.parcel_id}>"