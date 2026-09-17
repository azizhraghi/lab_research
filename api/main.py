from contextlib import asynccontextmanager
import logging

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from agents.bibliometrie.router import router as biblio_router
from agents.digitaltwin.router import router as twin_router
from agents.digitaltwin.gateway_router import router as gateway_router
from agents.optimisation.router import router as optimisation_router
from agents.simulation.router import router as simulation_router
from agents.veille.router import router as veille_router
from agents.veille.research_router import router as research_router
from agents.mis.router import router as mis_router
from agents.mis.dossier_router import router as dossier_router
from agents.mis.review_router import router as review_router
from agents.bibliometrie.trust_router import router as trust_router
from agents.orchestrateur.router import router as orch_router
from agents.qualite.router import router as qualite_router
from api.public_router import router as public_router
from shared.config import settings
from shared.database import Base, engine
from shared.event_bus import event_bus
from shared.observability import configure_logging
from shared.outbox import outbox_dispatcher
from shared.event_receipts import receipt_stats
from shared.security import get_current_user, require_roles


logger = logging.getLogger("lrste.api")
_managed_agents = []

# Import all models so Base.metadata knows about them.
import agents.bibliometrie.models  # noqa: F401
import api.public_models  # noqa: F401
import agents.digitaltwin.models  # noqa: F401
import agents.optimisation.models  # noqa: F401
import agents.simulation.models  # noqa: F401
import agents.veille.models  # noqa: F401
import agents.mis.models  # noqa: F401
import agents.orchestrateur.models  # noqa: F401
import agents.qualite.models  # noqa: F401
import shared.outbox  # noqa: F401
import shared.event_receipts  # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start agents visibly and stop them cleanly on shutdown."""
    configure_logging()
    if settings.CREATE_SCHEMA_ON_STARTUP:
        logger.warning("create_schema_on_startup_enabled", extra={"environment": settings.ENVIRONMENT})
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    await outbox_dispatcher.start()
    logger.info("outbox_dispatcher_started")

    # Start agents that subscribe to the event bus. Subscribing only registers
    # handlers — the InMemory bus dispatches via a background FIFO worker, so
    # slow handlers run off the request path. A bus failure must never prevent
    # the API from booting, so each start is individually guarded.
    from agents.veille.agent import veille_agent
    from agents.bibliometrie.agent import bibliometrie_agent
    from agents.mis.agent import mis_agent
    from agents.digitaltwin.agent import digital_twin_agent
    from agents.orchestrateur.agent import orchestrator_agent
    from agents.qualite.agent import qualite_agent
    # Subscription order remains significant for the in-memory bus: its single
    # dispatch worker calls handlers in subscription order, so qualite persists
    # the validation event before the twin reacts and emits its nested
    # recommendation event, preserving an honest audit trail.
    _managed_agents[:] = (
        veille_agent, bibliometrie_agent, mis_agent, orchestrator_agent,
        qualite_agent, digital_twin_agent,
    )
    failures = []
    for agent in _managed_agents:
        try:
            await agent.start()
            logger.info("agent_started", extra={"agent": agent.name})
        except Exception:
            failures.append(agent.name)
            logger.exception("agent_start_failed", extra={"agent": agent.name})

    if failures and (settings.is_production or settings.STRICT_AGENT_STARTUP):
        raise RuntimeError(f"Required agents failed to start: {', '.join(failures)}")
    if failures:
        logger.warning("api_started_degraded", extra={"failed_agents": failures})

    try:
        yield
    finally:
        await outbox_dispatcher.stop()
        logger.info("outbox_dispatcher_stopped")
        for agent in reversed(_managed_agents):
            try:
                await agent.stop()
                logger.info("agent_stopped", extra={"agent": agent.name})
            except Exception:
                logger.exception("agent_stop_failed", extra={"agent": agent.name})
        await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API Gateway for Research Laboratory AI Agents Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


protected = [Depends(get_current_user)]

# ── Original Agents ──────────────────────────────────────────────────
app.include_router(research_router, prefix="/api/veille/research", tags=["literature-review"], dependencies=protected)
app.include_router(veille_router, prefix="/api/veille", tags=["veille"], dependencies=protected)
app.include_router(biblio_router, prefix="/api/biblio", tags=["bibliometrie"], dependencies=protected)
app.include_router(twin_router, prefix="/api/twin", tags=["digital-twin"], dependencies=protected)
# Field hardware has a separate device-key authentication boundary. It is not a
# public route: gateway_router verifies X-Sensor-Code/X-Sensor-Token itself.
app.include_router(gateway_router, prefix="/api/gateway", tags=["field-gateway"])
app.include_router(simulation_router, prefix="/api/simulation", tags=["simulation"], dependencies=protected)
app.include_router(optimisation_router, prefix="/api/optimisation", tags=["optimisation"], dependencies=protected)

# ── New Agents (from Friends) ────────────────────────────────────────
app.include_router(mis_router, prefix="/api/mis", tags=["mis"], dependencies=protected)
app.include_router(dossier_router, prefix="/api/mis", tags=["project-dossier"], dependencies=protected)
app.include_router(review_router, prefix="/api/mis", tags=["research-review"], dependencies=protected)
app.include_router(trust_router, prefix="/api/biblio", tags=["bibliographic-trust"], dependencies=protected)
app.include_router(orch_router, prefix="/api/orchestrateur", tags=["orchestrateur"], dependencies=protected)
app.include_router(qualite_router, prefix="/api/qualite", tags=["qualite"], dependencies=protected)

# Public content is a deliberately curated snapshot.  Do not add a global
# authentication dependency here: only its GET endpoints are anonymous; each
# /admin publishing endpoint owns its role guard.
app.include_router(public_router, prefix="/api/public", tags=["public-portal"])


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get("/ready")
async def readiness_check():
    """Prove the database and every required agent are operational."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("readiness_database_failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from exc

    try:
        bus = await event_bus.check_health()
    except Exception as exc:
        logger.exception("readiness_event_bus_failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Event bus is unavailable.",
        ) from exc

    outbox = await outbox_dispatcher.stats()
    if outbox["failed"]:
        logger.error("readiness_outbox_failed", extra={"outbox": outbox})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "One or more agent events require operator retry.", "outbox": outbox},
        )

    inactive = [agent.name for agent in _managed_agents if not agent.running]
    if inactive:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"message": "One or more required agents are inactive.", "agents": inactive},
        )
    return {
        "status": "ready",
        "environment": settings.ENVIRONMENT,
        "event_bus": bus,
        "outbox": outbox,
        "agents": [agent.name for agent in _managed_agents],
    }


@app.get("/operations/outbox")
async def outbox_operations(_: object = Depends(require_roles("administrator"))):
    """Expose event-delivery failures to the lab operator; never hide them."""
    failed = await outbox_dispatcher.list_failed()
    from sqlalchemy import select
    from shared.database import AsyncSessionLocal
    from shared.outbox import OutboxEvent
    from shared.event_receipts import EventReceipt
    async with AsyncSessionLocal() as db:
        recent = (await db.scalars(select(OutboxEvent).order_by(OutboxEvent.created_at.desc()).limit(30))).all()
        receipts = (await db.scalars(select(EventReceipt).where(EventReceipt.event_id.in_([row.id for row in recent])))).all() if recent else []
        history = [dict(id=row.id,type=row.event.get('type'),source_agent=row.event.get('source_agent'),status=row.status,
            created_at=row.created_at,delivered_at=row.delivered_at,attempts=row.attempts,
            consumers=[dict(agent=r.agent_name,status=r.status,attempts=r.attempts,error=r.last_error,processed_at=r.processed_at) for r in receipts if r.event_id==row.id]) for row in recent]
    return {
        "recent_events": history,
        "summary": await outbox_dispatcher.stats(),
        "consumer_receipts": await receipt_stats(),
        "failed_events": [
            {
                "id": row.id,
                "type": row.event.get("type"),
                "source_agent": row.event.get("source_agent"),
                "stream": row.stream,
                "attempts": row.attempts,
                "last_error": row.last_error,
                "created_at": row.created_at,
            }
            for row in failed
        ],
    }


@app.post("/operations/outbox/{event_id}/retry")
async def retry_outbox_event(event_id: str, _: object = Depends(require_roles("administrator"))):
    """Manually re-queue an exhausted event after the dependency is repaired."""
    if not await outbox_dispatcher.retry(event_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed outbox event not found.")
    return {"status": "queued", "event_id": event_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
