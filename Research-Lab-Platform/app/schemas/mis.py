from __future__ import annotations
from datetime import date
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, Field

ProjetStatut= Literal["planifie", "en_cours", "termine", "suspendu"]

class Projet(BaseModel):
    id:str =Field(default_factory = lambda: str(uuid4()))
    nom:str
    description: str | None = None
    statut: ProjetStatut = "planifie"
    date_debut: date
    date_fin_prevue: date | None = None
    budget_alloue:float=0.0
    responsable : str

RolePersonnel=Literal["chercheur","ingenieur","technicien","administratif","doctorant"]

class Personnel(BaseModel):
    id: str=Field(default_factory=lambda: str(uuid4()))
    nom: str
    prenom:str
    email: str
    role: RolePersonnel
    competences:list[str]=Field(default_factory=list)
    disponible: bool =True
    projet_actuel_id : str |None =None

class Equipement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    nom: str
    type: str
    etat: Literal["operationnel", "en_maintenance", "indisponible"]
    localisation: str
    responsable_id: str | None = None
    date_acquisition: date | None = None
    valeur_estimee: float = 0.0
class Budget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    projet_id: str
    montant_alloue: float
    montant_depense: float = 0.0
    devise: str = "EUR"
    date_debut: date
    date_fin: date | None = None
    description: str | None = None
