# -*- coding: utf-8 -*-
"""Orchestrator Router – status, alerts, history, and event trigger endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from agents.orchestrateur.agent import orchestrator_agent
from agents.orchestrateur.schemas import Alerte, HistoriqueEvenement

router = APIRouter(tags=["Orchestrateur"])


@router.get("/status")
async def get_status() -> dict:
    stats = await orchestrator_agent.get_stats()
    return {
        "agent": orchestrator_agent.name,
        "statut": "actif",
        **stats,
    }


@router.get("/alertes")
async def get_alertes(resolues: bool = False) -> list:
    return await orchestrator_agent.get_alertes(resolues=resolues)


@router.get("/historique")
async def get_historique() -> list:
    return await orchestrator_agent.get_historique()


@router.post("/trigger")
async def trigger_event(event: dict) -> dict:
    """Manually trigger an event through the orchestrator."""
    from shared.schemas import Event
    evt = Event(
        id=event.get("id", "manual"),
        type=event.get("type", "unknown"),
        source_agent=event.get("source_agent", "api"),
        payload=event.get("payload", {}),
    )
    await orchestrator_agent.handle_event(evt)
    return {"message": f"Événement '{evt.type}' traité avec succès."}


@router.patch("/alertes/{alerte_id}/resoudre")
async def resoudre_alerte(alerte_id: str) -> dict:
    success = await orchestrator_agent.resoudre_alerte(alerte_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    return {"message": f"Alerte {alerte_id} résolue."}
