from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
import datetime

from shared.database import Base


class OptimizationRun(Base):
    """Persisted constrained irrigation optimisation result."""
    __tablename__ = "optimisation_runs"

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey("twin_parcels.id"), index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    run_name = Column(String, nullable=False)
    horizon_days = Column(Integer, nullable=False)
    max_irrigation_mm_per_day = Column(Float, nullable=False)
    water_quota_mm = Column(Float, nullable=True)
    rainfall_factor = Column(Float, default=1.0, nullable=False)
    et_factor = Column(Float, default=1.0, nullable=False)
    temperature_delta_c = Column(Float, default=0.0, nullable=False)
    constraints = Column(JSON, nullable=False)
    summary = Column(JSON, nullable=False)
    schedule = Column(JSON, nullable=False)
    assumptions = Column(JSON, nullable=False)
    is_approved = Column(Boolean, nullable=False, default=False, index=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)

    parcel = relationship("Parcel")
