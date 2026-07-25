from __future__ import annotations
from datetime import datetime
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, Field
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

    
class EvaluationIA(BaseModel):
    projet_id: str
    forces: list[str]
    faiblesses: list[str]
    risques: list[str]
    niveau_risque: Literal["faible", "modere", "eleve", "critique"]
    recommandation: str
    resume: str