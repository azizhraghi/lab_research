from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.security import User, require_roles
from agents.optimisation.models import OptimizationRun
from agents.optimisation.schemas import (
    CompleteScheduleTaskRequest,
    IrrigationScheduleTaskResponse,
    OptimizationRunRequest,
    OptimizationRunResponse,
)
from agents.digitaltwin.models import IrrigationEvent, IrrigationScheduleTask, Parcel
from agents.digitaltwin.services.eligibility import operational_readings
from shared.outbox import enqueue_event, outbox_dispatcher
from shared.schemas import Event

router = APIRouter()


@router.post("/parcels/{parcel_id}/runs", response_model=OptimizationRunResponse, dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))])
async def run_irrigation_optimisation(
    parcel_id: int,
    data: OptimizationRunRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        from agents.optimisation.agent import optimisation_agent
        run = await optimisation_agent.optimise_irrigation(db, parcel_id, data)
        await db.commit()
        await db.refresh(run)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parcels/{parcel_id}/runs", response_model=List[OptimizationRunResponse])
async def list_parcel_optimisations(
    parcel_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(OptimizationRun)
        .where(OptimizationRun.parcel_id == parcel_id)
        .order_by(OptimizationRun.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/runs/{run_id}", response_model=OptimizationRunResponse)
async def get_optimisation_run(run_id: int, db: AsyncSession = Depends(get_db)):
    run = await db.get(OptimizationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Optimisation run not found")
    return run


@router.post("/runs/{run_id}/approve", response_model=list[IrrigationScheduleTaskResponse])
async def approve_optimisation_run(
    run_id: int,
    user: User = Depends(require_roles("reviewer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    """Turn an explicitly reviewed irrigation schedule into technician tasks."""
    run = await db.get(OptimizationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Optimisation run not found")
    if (run.assumptions or {}).get("mode") == "demonstration":
        raise HTTPException(status_code=409, detail="Demonstration plans cannot be approved or create field tasks.")
    if run.is_approved:
        raise HTTPException(status_code=409, detail="This optimisation run has already been approved")

    source_id = (run.assumptions or {}).get("source_reading_id")
    parcel = await db.get(Parcel, run.parcel_id)
    if not isinstance(source_id, int) or parcel is None:
        raise HTTPException(status_code=409, detail="Regenerate this schedule from a traceable field measurement before approval.")
    try:
        await operational_readings(db, parcel, source_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    reviewer = user.email or user.id
    tasks: list[IrrigationScheduleTask] = []
    for row in run.schedule or []:
        amount = float(row.get("irrigation_mm") or 0)
        scheduled = row.get("date")
        if amount <= 0 or not isinstance(scheduled, str):
            continue
        task = IrrigationScheduleTask(
            optimization_run_id=run.id, parcel_id=run.parcel_id,
            scheduled_date=datetime.fromisoformat(scheduled).date(),
            planned_amount_mm=amount, approved_by=reviewer,
        )
        db.add(task)
        tasks.append(task)
    run.is_approved = True
    run.approved_by = reviewer
    run.approved_at = datetime.utcnow()
    await db.commit()
    for task in tasks:
        await db.refresh(task)
    return tasks


@router.get("/field-tasks", response_model=list[IrrigationScheduleTaskResponse])
async def list_field_tasks(
    status: str = "open",
    db: AsyncSession = Depends(get_db),
):
    query = select(IrrigationScheduleTask).order_by(IrrigationScheduleTask.scheduled_date, IrrigationScheduleTask.id)
    if status != "all":
        query = query.where(IrrigationScheduleTask.status == status)
    return (await db.execute(query)).scalars().all()


@router.post("/field-tasks/{task_id}/complete", response_model=IrrigationScheduleTaskResponse)
async def complete_field_task(
    task_id: int,
    data: CompleteScheduleTaskRequest,
    user: User = Depends(require_roles("researcher", "reviewer", "administrator")),
    db: AsyncSession = Depends(get_db),
):
    """Mobile-safe confirmation: record the actual field amount, never assume it."""
    task = await db.get(IrrigationScheduleTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Field task not found")
    if task.status != "open":
        raise HTTPException(status_code=409, detail="Field task has already been completed")
    operator = user.email or user.id
    irrigation = IrrigationEvent(
        parcel_id=task.parcel_id, occurred_at=data.occurred_at,
        amount_mm=data.actual_amount_mm, method="scheduled field task", source="schedule_task",
        notes=data.notes, recorded_by=operator,
    )
    db.add(irrigation)
    await db.flush()
    task.status = "completed"
    task.completed_by = operator
    task.completed_at = datetime.utcnow()
    task.actual_amount_mm = data.actual_amount_mm
    task.notes = data.notes
    task.irrigation_event_id = irrigation.id
    await enqueue_event(db, "events", Event(
        id=f"irrigation-task-{task.id}", type="irrigation.applied", source_agent="field_operations",
        payload={
            "parcel_id": task.parcel_id, "irrigation_event_id": irrigation.id,
            "amount_mm": irrigation.amount_mm, "schedule_task_id": task.id,
        },
    ))
    await db.commit()
    await db.refresh(task)
    outbox_dispatcher.notify()
    return task
