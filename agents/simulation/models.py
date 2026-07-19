from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
import datetime

from shared.database import Base


class SimulationRun(Base):
    """Persisted multi-day water-balance simulation for an irrigated parcel."""
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey("twin_parcels.id"), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    scenario_name = Column(String, nullable=False)
    horizon_days = Column(Integer, nullable=False)

    rainfall_factor = Column(Float, default=1.0, nullable=False)
    et_factor = Column(Float, default=1.0, nullable=False)
    temperature_delta_c = Column(Float, default=0.0, nullable=False)
    initial_moisture_mm = Column(Float, nullable=True)

    baseline_summary = Column(JSON, nullable=False)
    scenario_summary = Column(JSON, nullable=False)
    deltas = Column(JSON, nullable=False)
    time_series = Column(JSON, nullable=False)
    assumptions = Column(JSON, nullable=False)

    parcel = relationship("Parcel")
