from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from shared.database import get_db
from shared.security import require_roles
from agents.bibliometrie.models import Researcher, Publication, BiblioIndicator, CVProfile, ResearcherPublication
from agents.bibliometrie.schemas import (
    ResearcherCreate, ResearcherResponse, 
    PublicationResponse, CVProfileResponse
)
from agents.bibliometrie.services.cv_generator import generate_cv_pdf, generate_cv
from agents.bibliometrie.agent import bibliometrie_agent
from fastapi.responses import FileResponse

router = APIRouter()

@router.post("/researchers", response_model=ResearcherResponse, dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))])
async def create_researcher(data: ResearcherCreate, db: AsyncSession = Depends(get_db)):
    """Create a researcher profile. No auth required for dev testing."""
    db_researcher = Researcher(**data.model_dump())
    db.add(db_researcher)
    await db.commit()
    await db.refresh(db_researcher, ["indicators", "cv_profile"])
    return db_researcher

@router.get("/researchers", response_model=List[ResearcherResponse])
async def list_researchers(db: AsyncSession = Depends(get_db)):
    stmt = select(Researcher).options(
        selectinload(Researcher.indicators),
        selectinload(Researcher.cv_profile)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/researchers/{researcher_id}/sync", dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))])
async def trigger_sync(researcher_id: int, db: AsyncSession = Depends(get_db)):
    """Sync a researcher's publications from Scholar. Runs synchronously."""
    try:
        from agents.bibliometrie.agent import bibliometrie_agent
        await bibliometrie_agent.run_sync_for_researcher(db, researcher_id)
        return {"status": "Sync completed successfully"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/researchers/{researcher_id}/cv/pdf")
async def download_cv_pdf(researcher_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Researcher).where(Researcher.id == researcher_id)
    result = await db.execute(stmt)
    researcher = result.scalar_one_or_none()
    
    if not researcher:
        raise HTTPException(status_code=404, detail="Researcher not found")
        
    # Publications via the association table
    pub_stmt = select(Publication).join(ResearcherPublication).where(ResearcherPublication.researcher_id == researcher_id)
    pub_res = await db.execute(pub_stmt)
    publications = pub_res.scalars().all()
    
    # Indicators
    ind_stmt = select(BiblioIndicator).where(BiblioIndicator.researcher_id == researcher_id)
    ind_res = await db.execute(ind_stmt)
    indicators = ind_res.scalars().all()
    
    data = {
        "name": researcher.name,
        "role": researcher.role,
        "department": researcher.department,
        "email": researcher.email,
        "indicators": [{"metric_name": i.metric_name, "value": i.value} for i in indicators],
        "publications": [{
            "title": p.title, 
            "year": p.year, 
            "journal": p.journal, 
            "citation_count": p.citation_count
        } for p in publications]
    }
    
    import os
    output_path = f"tmp_cv_{researcher_id}.pdf"
    
    try:
        await generate_cv_pdf(data, output_path)
        return FileResponse(
            output_path, 
            media_type="application/pdf", 
            filename=f"CV_{researcher.name.replace(' ', '_')}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Friend 1 endpoints (JSON-backed researcher profiles) ─────────────

@router.post("/profiles/add")
async def add_researcher_profile(name: str, email: str = None, orcid: str = None, google_scholar_id: str = None):
    """Add a researcher to the JSON-backed profile store (Friend 1 feature)."""
    researcher = bibliometrie_agent.add_researcher(name, email, orcid, google_scholar_id)
    return researcher.model_dump(mode="json")


@router.get("/profiles")
async def list_researcher_profiles():
    """List all researchers from JSON-backed store (Friend 1 feature)."""
    return [r.model_dump(mode="json") for r in bibliometrie_agent.list_researchers()]


@router.get("/profiles/{name}")
async def get_researcher_profile(name: str):
    """Get a specific researcher profile from JSON store."""
    researcher = bibliometrie_agent.get_researcher(name)
    if researcher is None:
        raise HTTPException(status_code=404, detail=f"Researcher '{name}' not found")
    return researcher.model_dump(mode="json")


@router.post("/profiles/{name}/scholar-sync")
async def sync_scholar_metrics(name: str):
    """Fetch Google Scholar metrics for a researcher (Friend 1 feature)."""
    researcher = bibliometrie_agent.get_researcher(name)
    if researcher is None:
        raise HTTPException(status_code=404, detail=f"Researcher '{name}' not found")
    updated = bibliometrie_agent.fetch_scholar_metrics(researcher)
    bibliometrie_agent._save_researchers()
    return updated.model_dump(mode="json")


@router.post("/profiles/update-all-metrics")
async def update_all_scholar_metrics():
    """Update Scholar metrics for ALL researchers (Friend 1 feature)."""
    bibliometrie_agent.update_all_metrics()
    return {"status": "All metrics updated", "count": len(bibliometrie_agent.list_researchers())}


@router.post("/profiles/{name}/generate-cv")
async def generate_researcher_cv(name: str):
    """Generate a PDF CV for a researcher (Friend 1 feature)."""
    researcher = bibliometrie_agent.get_researcher(name)
    if researcher is None:
        raise HTTPException(status_code=404, detail=f"Researcher '{name}' not found")
    bibliometrie_agent._regenerate_cv(researcher)
    filename = researcher.name.replace(" ", "_").lower()
    return {"status": "CV generated", "path": f"cvs/{filename}_cv.pdf"}

