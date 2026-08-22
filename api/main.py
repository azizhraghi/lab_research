from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.bibliometrie.router import router as biblio_router
from agents.digitaltwin.router import router as twin_router
from agents.optimisation.router import router as optimisation_router
from agents.simulation.router import router as simulation_router
from agents.veille.router import router as veille_router
from agents.mis.router import router as mis_router
from agents.orchestrateur.router import router as orch_router
from agents.qualite.router import router as qualite_router
from shared.config import settings
from shared.database import Base, engine
from shared.security import get_current_user

# Import all models so Base.metadata knows about them.
import agents.bibliometrie.models  # noqa: F401
import agents.digitaltwin.models  # noqa: F401
import agents.optimisation.models  # noqa: F401
import agents.simulation.models  # noqa: F401
import agents.veille.models  # noqa: F401
import agents.mis.models  # noqa: F401
import agents.orchestrateur.models  # noqa: F401
import agents.qualite.models  # noqa: F401

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API Gateway for Research Laboratory AI Agents Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Create a local schema only when explicitly requested for development."""
    if settings.CREATE_SCHEMA_ON_STARTUP:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Start agents that subscribe to the event bus. The InMemory bus dispatches
    # synchronously (handlers run inside the publisher's coroutine), so this
    # just registers the handlers — it does not block. A bus failure must never
    # prevent the API from booting, so each start is individually guarded.
    from agents.veille.agent import veille_agent
    from agents.bibliometrie.agent import bibliometrie_agent
    from agents.mis.agent import mis_agent
    from agents.digitaltwin.agent import digital_twin_agent
    from agents.orchestrateur.agent import orchestrator_agent
    from agents.qualite.agent import qualite_agent
    # Subscription order is significant for the synchronous in-memory bus used
    # in development: persist the validation event before the twin reacts and
    # emits its nested recommendation event, preserving an honest audit trail.
    for agent in (veille_agent, bibliometrie_agent, mis_agent, orchestrator_agent, qualite_agent, digital_twin_agent):
        try:
            await agent.start()
        except Exception as e:
            print(f"[startup] Agent {agent.name} start failed (non-fatal): {e}")


protected = [Depends(get_current_user)]

# ── Original Agents ──────────────────────────────────────────────────
app.include_router(veille_router, prefix="/api/veille", tags=["veille"], dependencies=protected)
app.include_router(biblio_router, prefix="/api/biblio", tags=["bibliometrie"], dependencies=protected)
app.include_router(twin_router, prefix="/api/twin", tags=["digital-twin"], dependencies=protected)
app.include_router(simulation_router, prefix="/api/simulation", tags=["simulation"], dependencies=protected)
app.include_router(optimisation_router, prefix="/api/optimisation", tags=["optimisation"], dependencies=protected)

# ── New Agents (from Friends) ────────────────────────────────────────
app.include_router(mis_router, prefix="/api/mis", tags=["mis"], dependencies=protected)
app.include_router(orch_router, prefix="/api/orchestrateur", tags=["orchestrateur"], dependencies=protected)
app.include_router(qualite_router, prefix="/api/qualite", tags=["qualite"], dependencies=protected)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
