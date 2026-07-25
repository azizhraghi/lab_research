from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.qualite import RapportQualite, DemandeValidation
from app.schemas.events import Event
from app.models.mis import Projet as ProjetModel, Personnel as PersonnelModel
from app.models.mis import Equipement as EquipementModel, Budget as BudgetModel
from app.database import get_db
from app.state import qualite_agent

router = APIRouter(prefix="/qualite", tags=["Qualité"])


@router.get("/status")
def get_status() -> dict:
    stats = qualite_agent.get_stats()
    return {
        "agent": qualite_agent.name,
        "statut": "actif",
        **stats,
    }


@router.get("/rapports", response_model=list[RapportQualite])
def get_rapports() -> list[RapportQualite]:
    return qualite_agent.get_rapports()


@router.get("/rapports/{entite_id}", response_model=list[RapportQualite])
def get_rapport_entite(entite_id: str) -> list[RapportQualite]:
    rapports = qualite_agent.get_rapport_par_entite(entite_id)
    if not rapports:
        raise HTTPException(status_code=404, detail="Aucun rapport pour cette entité")
    return rapports


@router.post("/valider/projet/{projet_id}", response_model=RapportQualite)
async def valider_projet(projet_id: str, db: AsyncSession = Depends(get_db)) -> RapportQualite:
    projet = await db.get(ProjetModel, projet_id)
    if projet is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    rapport = qualite_agent.valider_projet(projet_id, projet.__dict__)
    qualite_agent._rapports.append(rapport)
    return rapport


@router.post("/valider/personnel/{personnel_id}", response_model=RapportQualite)
async def valider_personnel(personnel_id: str, db: AsyncSession = Depends(get_db)) -> RapportQualite:
    personnel = await db.get(PersonnelModel, personnel_id)
    if personnel is None:
        raise HTTPException(status_code=404, detail="Personnel introuvable")
    import json
    data = personnel.__dict__.copy()
    data["competences"] = json.loads(data["competences"])
    rapport = qualite_agent.valider_personnel(personnel_id, data)
    qualite_agent._rapports.append(rapport)
    return rapport


@router.post("/valider/equipement/{equipement_id}", response_model=RapportQualite)
async def valider_equipement(equipement_id: str, db: AsyncSession = Depends(get_db)) -> RapportQualite:
    equipement = await db.get(EquipementModel, equipement_id)
    if equipement is None:
        raise HTTPException(status_code=404, detail="Équipement introuvable")
    rapport = qualite_agent.valider_equipement(equipement_id, equipement.__dict__)
    qualite_agent._rapports.append(rapport)
    return rapport


@router.post("/valider/budget/{budget_id}", response_model=RapportQualite)
async def valider_budget(budget_id: str, db: AsyncSession = Depends(get_db)) -> RapportQualite:
    budget = await db.get(BudgetModel, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    rapport = qualite_agent.valider_budget(budget_id, budget.__dict__)
    qualite_agent._rapports.append(rapport)
    return rapport


@router.post("/valider", response_model=RapportQualite)
async def valider_via_event(demande: DemandeValidation) -> RapportQualite:
    await qualite_agent.event_bus.publish(Event(
        type="qualite.validation_demandee",
        source_agent="api",
        payload={
            "entite_type": demande.entite_type,
            "entite_id": demande.entite_id,
        }
    ))
    rapports = qualite_agent.get_rapport_par_entite(demande.entite_id)
    if not rapports:
        raise HTTPException(status_code=404, detail="Entité introuvable ou validation échouée")
    return rapports[-1]