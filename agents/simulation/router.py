from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.security import require_roles
from agents.simulation.models import SimulationRun
from agents.simulation.schemas import SimulationRunRequest, SimulationRunResponse

router = APIRouter()


@router.post("/parcels/{parcel_id}/runs", response_model=SimulationRunResponse, dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))])
async def run_parcel_simulation(
    parcel_id: int,
    data: SimulationRunRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        from agents.simulation.agent import simulation_agent
        run = await simulation_agent.run_parcel_projection(db, parcel_id, data)
        await db.commit()
        await db.refresh(run)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parcels/{parcel_id}/runs", response_model=List[SimulationRunResponse])
async def list_parcel_simulations(
    parcel_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(SimulationRun)
        .where(SimulationRun.parcel_id == parcel_id)
        .order_by(SimulationRun.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/runs/{run_id}", response_model=SimulationRunResponse)
async def get_simulation_run(run_id: int, db: AsyncSession = Depends(get_db)):
    run = await db.get(SimulationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return run
