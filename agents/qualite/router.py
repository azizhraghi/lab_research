# -*- coding: utf-8 -*-
"""Qualité Router – validation endpoints for all entity types."""
from __future__ import annotations
import json

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agents.qualite.schemas import RapportQualite, DemandeValidation
from agents.qualite.agent import qualite_agent
from agents.mis.models import (
    Projet as ProjetModel,
    Personnel as PersonnelModel,
    Equipement as EquipementModel,
    Budget as BudgetModel,
)
from shared.database import get_db

router = APIRouter(tags=["Qualité"])


@router.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)) -> dict:
    stats = await qualite_agent.get_stats(db)
    return {"agent": qualite_agent.name, "statut": "actif", **stats}


@router.get("/rapports", response_model=list[RapportQualite])
async def get_rapports(db: AsyncSession = Depends(get_db)) -> list[RapportQualite]:
    return await qualite_agent.get_rapports(db)


@router.get("/rapports/{entite_id}", response_model=list[RapportQualite])
async def get_rapport_entite(entite_id: str, db: AsyncSession = Depends(get_db)) -> list[RapportQualite]:
    rapports = await qualite_agent.get_rapport_par_entite(entite_id, db)
    if not rapports:
        raise HTTPException(status_code=404, detail="Aucun rapport pour cette entité")
    return rapports


@router.post("/valider/projet/{projet_id}", response_model=RapportQualite)
async def valider_projet(projet_id: str, db: AsyncSession = Depends(get_db)) -> RapportQualite:
    projet = await db.get(ProjetModel, projet_id)
    if projet is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    rapport = qualite_agent.valider_projet(projet_id, projet.__dict__)
    await qualite_agent._persist_rapport(rapport, db)
    return rapport


@router.post("/valider/personnel/{personnel_id}", response_model=RapportQualite)
async def valider_personnel(personnel_id: str, db: AsyncSession = Depends(get_db)) -> RapportQualite:
    personnel = await db.get(PersonnelModel, personnel_id)
    if personnel is None:
        raise HTTPException(status_code=404, detail="Personnel introuvable")
    data = personnel.__dict__.copy()
    data["competences"] = json.loads(data["competences"])
    rapport = qualite_agent.valider_personnel(personnel_id, data)
    await qualite_agent._persist_rapport(rapport, db)
    return rapport


@router.post("/valider/equipement/{equipement_id}", response_model=RapportQualite)
async def valider_equipement(equipement_id: str, db: AsyncSession = Depends(get_db)) -> RapportQualite:
    equipement = await db.get(EquipementModel, equipement_id)
    if equipement is None:
        raise HTTPException(status_code=404, detail="Équipement introuvable")
    rapport = qualite_agent.valider_equipement(equipement_id, equipement.__dict__)
    await qualite_agent._persist_rapport(rapport, db)
    return rapport


@router.post("/valider/budget/{budget_id}", response_model=RapportQualite)
async def valider_budget(budget_id: str, db: AsyncSession = Depends(get_db)) -> RapportQualite:
    budget = await db.get(BudgetModel, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    rapport = qualite_agent.valider_budget(budget_id, budget.__dict__)
    await qualite_agent._persist_rapport(rapport, db)
    return rapport
