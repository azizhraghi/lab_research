from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


NiveauQualite = Literal["conforme", "avertissement", "non_conforme"]


class RapportQualite(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    entite_type: str
    entite_id: str
    niveau: NiveauQualite
    problemes: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    conforme_rgpd: bool = True


class DemandeValidation(BaseModel):
    entite_type: Literal["projet", "personnel", "equipement", "budget"]
    entite_id: str


class MeasurementReviewResponse(BaseModel):
    id: str
    reading_id: int
    parcel_id: int
    status: str
    quality_flag: str
    issues: list[str]
    annotation: str | None = None
    reviewer_id: str | None = None
    reviewed_at: datetime | None = None
    correction: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeasurementReviewDecision(BaseModel):
    action: str = Field(pattern="^(accept|reject|annotate|correct)$")
    annotation: str | None = Field(None, max_length=2000)
    correction: dict[str, Any] | None = None


class EvaluationIA(BaseModel):
    """AI-powered project evaluation result (from Friend 2's LLM integration)."""
    projet_id: str
    forces: list[str]
    faiblesses: list[str]
    risques: list[str]
    niveau_risque: Literal["faible", "modere", "eleve", "critique"]
    recommandation: str
    resume: str

    model_config = ConfigDict(from_attributes=True)
