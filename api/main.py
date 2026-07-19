from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.bibliometrie.router import router as biblio_router
from agents.digitaltwin.router import router as twin_router
from agents.optimisation.router import router as optimisation_router
from agents.simulation.router import router as simulation_router
from agents.veille.router import router as veille_router
from shared.config import settings
from shared.database import Base, engine
from shared.security import get_current_user

# Import all models so Base.metadata knows about them.
import agents.bibliometrie.models  # noqa: F401
import agents.digitaltwin.models  # noqa: F401
import agents.optimisation.models  # noqa: F401
import agents.simulation.models  # noqa: F401
import agents.veille.models  # noqa: F401

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API Gateway for Research Laboratory AI Agents Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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


protected = [Depends(get_current_user)]
app.include_router(veille_router, prefix="/api/veille", tags=["veille"], dependencies=protected)
app.include_router(biblio_router, prefix="/api/biblio", tags=["bibliometrie"], dependencies=protected)
app.include_router(twin_router, prefix="/api/twin", tags=["digital-twin"], dependencies=protected)
app.include_router(simulation_router, prefix="/api/simulation", tags=["simulation"], dependencies=protected)
app.include_router(optimisation_router, prefix="/api/optimisation", tags=["optimisation"], dependencies=protected)


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