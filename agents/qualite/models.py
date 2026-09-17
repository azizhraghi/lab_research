"""Persistence for Qualité agent reports.

Previously reports lived only in an in-memory list on QualiteAgent, so every
server restart lost them. These tables mirror the RapportQualite pydantic schema
(agents/qualite/schemas.py) and are written by both the validation router and
the event handler.
"""
from __future__ import annotations
import datetime

from sqlalchemy import Column, String, Boolean, DateTime, JSON
from shared.database import Base


class RapportQualiteDB(Base):
    __tablename__ = "qualite_rapports"

    # Same str id as the pydantic RapportQualite (uuid4).
    id = Column(String, primary_key=True, index=True)
    entite_type = Column(String, index=True)
    entite_id = Column(String, index=True)
    niveau = Column(String)  # conforme | avertissement | non_conforme
    problemes = Column(JSON, default=list)  # list[str]
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    conforme_rgpd = Column(Boolean, default=True)


class MeasurementReviewDB(Base):
    """Human decision record for a suspect or rejected field measurement."""
    __tablename__ = "qualite_measurement_reviews"

    id = Column(String, primary_key=True, index=True)
    reading_id = Column(String, unique=True, index=True, nullable=False)
    parcel_id = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False, default="pending", index=True)
    quality_flag = Column(String, nullable=False)
    issues = Column(JSON, nullable=False, default=list)
    annotation = Column(String, nullable=True)
    reviewer_id = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    correction = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
