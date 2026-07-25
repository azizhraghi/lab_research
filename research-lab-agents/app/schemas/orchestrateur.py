from __future__ import annotations
from datetime import datetime 
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel , Field 

NiveauAlerte = Literal["info","orange","rouge","critique"]

class Alerte(BaseModel):
     id: str = Field(default_factory=lambda: str(uuid4()))
     niveau : NiveauAlerte
     message: str
     source_evenement: str
     timestamp: datetime = Field(default_factory=datetime.utcnow)
     resolue: bool = False

class HistoriqueEvenement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type_evenement: str
    source_agent: str
    payload: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    traite: bool = True
    alertes_generees: list[str] = Field(default_factory=list)


class DecisionRoutageIA(BaseModel):
    type_evenement: str
    agent_ou_action_recommande: str
    niveau_urgence: NiveauAlerte
    justification: str
    necessite_intervention_humaine: bool