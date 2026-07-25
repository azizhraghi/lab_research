"""
Point d'entree de l'application FastAPI.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers.mis import router as mis_router
from app.routers.orchestrateur import router as orchestrateur_router
from app.routers.qualite import router as qualite_router
from app.schemas.events import AgentAction, Event
from app.state import mis_agent, orchestrator_agent, qualite_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mis_agent.start()
    await orchestrator_agent.start()
    await qualite_agent.start()
    yield
    await qualite_agent.stop()
    await orchestrator_agent.stop()
    await mis_agent.stop()


app = FastAPI(
    title="Research Lab - Agent Orchestration API",
    description="API du systeme multi-agents (MIS + Orchestrateur + Qualite)",
    version="0.3.0",
    lifespan=lifespan,
)

app.include_router(mis_router)
app.include_router(orchestrateur_router)
app.include_router(qualite_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "agent-orchestration-api"}


@app.get("/debug/mis-status")
def mis_status() -> dict[str, str]:
    return {"agent": mis_agent.name, "status": mis_agent.status}


@app.post("/debug/echo-event", response_model=Event)
def echo_event(event: Event) -> Event:
    return event


@app.post("/debug/echo-action", response_model=AgentAction)
def echo_action(action: AgentAction) -> AgentAction:
    return action