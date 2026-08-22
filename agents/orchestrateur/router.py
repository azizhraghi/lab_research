"""Orchestrator API: alerts, event audit history and reviewed planning."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.orchestrateur.agent import orchestrator_agent
from agents.orchestrateur.models import PlanningProposalDB, PlanningTaskDB
from agents.orchestrateur.planning import create_plan
from agents.orchestrateur.schemas import (
    PlanningProposalResponse,
    PlanningTaskCreate,
    PlanningTaskResponse,
    TaskStatusUpdate,
)
from shared.database import get_db
from shared.schemas import Event
from shared.security import User, require_roles


router = APIRouter(tags=["Orchestrateur"])
_PLANNING_WRITE = [Depends(require_roles("researcher", "reviewer", "administrator"))]


@router.get("/status")
async def get_status() -> dict:
    stats = await orchestrator_agent.get_stats()
    return {"agent": orchestrator_agent.name, "statut": "actif", **stats}


@router.get("/alertes")
async def get_alertes(resolues: bool = False) -> list:
    return await orchestrator_agent.get_alertes(resolues=resolues)


@router.get("/historique")
async def get_historique() -> list:
    return await orchestrator_agent.get_historique()


@router.post("/trigger")
async def trigger_event(event: dict) -> dict:
    """Manually route an event; useful for controlled demonstrations."""
    evt = Event(
        id=event.get("id", "manual"),
        type=event.get("type", "unknown"),
        source_agent=event.get("source_agent", "api"),
        payload=event.get("payload", {}),
    )
    await orchestrator_agent.handle_event(evt)
    return {"message": f"Event '{evt.type}' routed."}


@router.patch("/alertes/{alerte_id}/resoudre")
async def resoudre_alerte(alerte_id: str) -> dict:
    if not await orchestrator_agent.resoudre_alerte(alerte_id):
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": f"Alert {alerte_id} resolved."}


@router.get("/planning/tasks", response_model=list[PlanningTaskResponse])
async def list_planning_tasks(db: AsyncSession = Depends(get_db)) -> list[PlanningTaskDB]:
    result = await db.execute(select(PlanningTaskDB).order_by(PlanningTaskDB.created_at.desc()))
    return result.scalars().all()


@router.post("/planning/tasks", response_model=PlanningTaskResponse, dependencies=_PLANNING_WRITE)
async def create_planning_task(data: PlanningTaskCreate, db: AsyncSession = Depends(get_db)) -> PlanningTaskDB:
    task = PlanningTaskDB(id=str(uuid4()), **data.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    await orchestrator_agent.emit_event("events", Event(
        id=str(uuid4()), type="planning.task_created", source_agent="orchestrateur",
        payload={"task_id": task.id, "title": task.title, "priority": task.priority},
    ))
    return task


@router.patch("/planning/tasks/{task_id}/status", response_model=PlanningTaskResponse, dependencies=_PLANNING_WRITE)
async def update_task_status(task_id: str, data: TaskStatusUpdate, db: AsyncSession = Depends(get_db)) -> PlanningTaskDB:
    task = await db.get(PlanningTaskDB, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Planning task not found")
    task.status = data.status
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/planning/proposals", response_model=list[PlanningProposalResponse])
async def list_planning_proposals(db: AsyncSession = Depends(get_db)) -> list[PlanningProposalDB]:
    result = await db.execute(select(PlanningProposalDB).order_by(PlanningProposalDB.created_at.desc()))
    return result.scalars().all()


@router.post("/planning/proposals", response_model=PlanningProposalResponse, dependencies=_PLANNING_WRITE)
async def propose_plan(db: AsyncSession = Depends(get_db)) -> PlanningProposalDB:
    """Build a non-mutating proposal from current MIS resources and pending work."""
    assignments, conflicts = await create_plan(db)
    proposal = PlanningProposalDB(
        id=str(uuid4()), status="proposed",
        proposed_assignments=assignments, conflicts=conflicts,
    )
    db.add(proposal)
    await db.commit()
    await db.refresh(proposal)
    await orchestrator_agent.emit_event("events", Event(
        id=str(uuid4()), type="planning.proposal_created", source_agent="orchestrateur",
        payload={
            "proposal_id": proposal.id, "assignment_count": len(assignments),
            "conflict_count": len(conflicts), "human_approval_required": True,
        },
    ))
    return proposal


@router.patch("/planning/proposals/{proposal_id}/approve", response_model=PlanningProposalResponse)
async def approve_plan(
    proposal_id: str,
    user: User = Depends(require_roles("reviewer", "administrator")),
    db: AsyncSession = Depends(get_db),
) -> PlanningProposalDB:
    """Apply only the reviewed proposal's conflict-free task assignments."""
    proposal = await db.get(PlanningProposalDB, proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail="Planning proposal not found")
    if proposal.status != "proposed":
        raise HTTPException(status_code=409, detail="Planning proposal has already been decided")

    for assignment in proposal.proposed_assignments or []:
        task_id = assignment.get("task_id")
        task = await db.get(PlanningTaskDB, task_id) if isinstance(task_id, str) else None
        if task is None or task.status != "pending":
            continue
        task.assigned_personnel_id = assignment["personnel_id"]
        task.scheduled_start = datetime.fromisoformat(assignment["scheduled_start"])
        task.scheduled_end = datetime.fromisoformat(assignment["scheduled_end"])
        task.status = "planned"

    proposal.status = "approved"
    proposal.approved_at = datetime.utcnow()
    proposal.approved_by = user.email or user.id
    await db.commit()
    await db.refresh(proposal)
    await orchestrator_agent.emit_event("events", Event(
        id=str(uuid4()), type="planning.proposal_approved", source_agent="orchestrateur",
        payload={"proposal_id": proposal.id, "approved_by": proposal.approved_by},
    ))
    return proposal
