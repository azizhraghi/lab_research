from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.schemas.events import Event
from app.state import orchestrator_agent
from app.schemas.orchestrateur import DecisionRoutageIA

router = APIRouter(prefix="/orchestrateur", tags=["Orchestrateur"])
@router.get("/status")
def get_status() -> dict:
    stats = orchestrator_agent.get_stats()
    return {
        "agent": orchestrator_agent.name,
        "statut": "actif",
        **stats,
    }
@router.get("/alertes")
def get_alertes(resolues: bool = False) -> list:
    return orchestrator_agent.get_alertes(resolues=resolues)


@router.get("/historique")
def get_historique() -> list:
    return orchestrator_agent.get_historique()


@router.get("/decisions-ia", response_model=list[DecisionRoutageIA])
def get_decisions_ia() -> list[DecisionRoutageIA]:
    return orchestrator_agent.get_decisions_ia()



@router.post("/trigger")
async def trigger_event(event: Event) -> dict:
    await orchestrator_agent.handle_event(event)
    return {"message": f"Événement '{event.type}' traité avec succès."}


@router.patch("/alertes/{alerte_id}/resoudre")
def resoudre_alerte(alerte_id: str) -> dict:
    success = orchestrator_agent.resoudre_alerte(alerte_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    return {"message": f"Alerte {alerte_id} résolue."}