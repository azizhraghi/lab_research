from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.security import require_roles
from agents.optimisation.models import OptimizationRun
from agents.optimisation.schemas import OptimizationRunRequest, OptimizationRunResponse

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
