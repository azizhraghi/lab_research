from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from typing import List

from shared.database import get_db
from shared.security import require_roles
from agents.bibliometrie.models import Researcher, Publication, BiblioIndicator, CVProfile, ResearcherPublication
from agents.bibliometrie.schemas import (
    ResearcherCreate, ResearcherResponse, ResearcherUpdate, ResearcherDeleteResponse,
    PublicationResponse, CVProfileResponse, OrcidSyncResponse, ScholarSyncResponse
)
from agents.bibliometrie.services.orcid_sync import OrcidUnavailable
from agents.bibliometrie.services.scholar_sync import ScholarUnavailable
from agents.bibliometrie.services.publication_sync import (
    sync_orcid_publications,
    sync_scholar_publications,
)
from agents.bibliometrie.services.cv_generator import generate_cv_pdf, generate_cv
from agents.bibliometrie.agent import bibliometrie_agent
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

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


@router.put(
    "/researchers/{researcher_id}",
    response_model=ResearcherResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def update_researcher(
    researcher_id: int, data: ResearcherUpdate, db: AsyncSession = Depends(get_db)
):
    """Partial update; absent fields keep their current values.

    email/orcid_id/scholar_id/scopus_id are UNIQUE columns, so a value already
    claimed by another profile surfaces as a 409 naming the column rather than
    a bare 500 IntegrityError.
    """
    from sqlalchemy.exc import IntegrityError

    researcher = await db.get(Researcher, researcher_id)
    if researcher is None:
        raise HTTPException(status_code=404, detail=f"Researcher {researcher_id} not found")

    changes = data.model_dump(exclude_unset=True)
    if not changes:
        await db.refresh(researcher, ["indicators", "cv_profile"])
        return researcher

    for field, value in changes.items():
        setattr(researcher, field, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Another researcher already uses this "
                f"{', '.join(sorted(k for k in changes if k in ('email', 'orcid_id', 'scholar_id', 'scopus_id')))}."
            ),
        ) from exc
    await db.refresh(researcher, ["indicators", "cv_profile"])
    return researcher


@router.delete(
    "/researchers/{researcher_id}",
    response_model=ResearcherDeleteResponse,
    dependencies=[Depends(require_roles("reviewer", "administrator"))],
)
async def delete_researcher(researcher_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a researcher, but only while no publications are linked.

    Publication links are the lab's bibliographic record — shared rows another
    co-author may also point at — so this refuses with 409 rather than
    unlinking them. Indicators and the CV profile are per-researcher and
    regenerable by a sync, so they go with the profile.
    """
    researcher = await db.get(Researcher, researcher_id)
    if researcher is None:
        raise HTTPException(status_code=404, detail=f"Researcher {researcher_id} not found")

    link_count = (
        await db.execute(
            select(func.count()).select_from(ResearcherPublication).where(
                ResearcherPublication.researcher_id == researcher_id
            )
        )
    ).scalar_one()
    if link_count:
        raise HTTPException(
            status_code=409,
            detail=(
                f"{researcher.name} still has {link_count} linked publications. "
                "This refuses rather than unlinking the lab's bibliographic "
                "record — remove the links first if deletion is intended."
            ),
        )

    name = researcher.name
    # Per-researcher children with no cascade; both are regenerable.
    await db.execute(
        delete(BiblioIndicator).where(BiblioIndicator.researcher_id == researcher_id)
    )
    cv = await db.execute(select(CVProfile).where(CVProfile.researcher_id == researcher_id))
    cv_row = cv.scalar_one_or_none()
    if cv_row is not None:
        await db.delete(cv_row)
    await db.delete(researcher)
    await db.commit()
    return ResearcherDeleteResponse(deleted_id=researcher_id, name=name)

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

@router.get("/researchers/{researcher_id}/publications", response_model=List[PublicationResponse])
async def list_researcher_publications(researcher_id: int, db: AsyncSession = Depends(get_db)):
    """The publications linked to one researcher, newest first.

    404s when the researcher does not exist rather than returning `[]`, so an
    empty list means "no publications on file" and nothing else. (The digital-twin
    list routes still conflate the two — see HANDOFF Pending.)
    """
    if await db.get(Researcher, researcher_id) is None:
        raise HTTPException(status_code=404, detail=f"Researcher {researcher_id} not found")

    stmt = (
        select(Publication)
        .join(ResearcherPublication)
        .where(ResearcherPublication.researcher_id == researcher_id)
        .order_by(Publication.year.desc().nullslast(), Publication.title)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "/researchers/{researcher_id}/publications/sync",
    response_model=OrcidSyncResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def sync_researcher_publications(researcher_id: int, db: AsyncSession = Depends(get_db)):
    """Import a researcher's works from their public ORCID record.

    Roles mirror the metrics sync: whoever maintains a profile can refresh its
    publication list. Idempotent — re-running matches on DOI (or title+year for
    works without one) and only adds what is new.

    A missing or unreachable ORCID iD is a 400 carrying ORCID's own reason, not a
    500: the request was well-formed, the upstream record just is not usable. The
    message is written to be shown to the user verbatim.
    """
    researcher = await db.get(Researcher, researcher_id)
    if researcher is None:
        raise HTTPException(status_code=404, detail=f"Researcher {researcher_id} not found")
    if not researcher.orcid_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"{researcher.name} has no ORCID iD on file. Add one to the profile "
                "before syncing publications."
            ),
        )

    try:
        result = await sync_orcid_publications(db, researcher)
    except OrcidUnavailable as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return OrcidSyncResponse(orcid_id=researcher.orcid_id, **result)


@router.post(
    "/researchers/{researcher_id}/publications/sync/scholar",
    response_model=ScholarSyncResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def sync_researcher_scholar_publications(researcher_id: int, db: AsyncSession = Depends(get_db)):
    """Import a researcher's works from their public Google Scholar profile.

    Same idempotency contract as the ORCID route (DOI then title+year match).
    Scholar additionally refreshes citation counts on every row it matches —
    unlike ORCID, counts are the point. Scholar blocks unproxied automation
    aggressively; the agent configures ScraperAPI at startup when a key exists,
    and a block surfaces here as a 400 with the reason, not an empty success.
    """
    researcher = await db.get(Researcher, researcher_id)
    if researcher is None:
        raise HTTPException(status_code=404, detail=f"Researcher {researcher_id} not found")
    if not researcher.scholar_id:
        raise HTTPException(
            status_code=400,
            detail=(
                f"{researcher.name} has no Google Scholar ID on file. Add one to "
                "the profile before syncing publications."
            ),
        )

    try:
        result = await sync_scholar_publications(db, researcher)
    except ScholarUnavailable as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ScholarSyncResponse(scholar_id=researcher.scholar_id, **result)


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
        # Identifiers were collected but never passed through, so every CV
        # printed a bare name even for researchers with an ORCID on file.
        "orcid_id": researcher.orcid_id,
        "scholar_id": researcher.scholar_id,
        "indicators": [{"metric_name": i.metric_name, "value": i.value} for i in indicators],
        "publications": [{
            "title": p.title,
            "year": p.year,
            "journal": p.journal,
            "doi": p.doi,
            "source": p.source,
            "citation_count": p.citation_count
        } for p in publications]
    }
    
    # Write to the OS temp dir and delete after the response is sent — the
    # repo-root tmp_cv_{id}.pdf files this replaced were never cleaned up.
    import os
    import tempfile
    fd, output_path = tempfile.mkstemp(suffix=".pdf", prefix=f"lrste_cv_{researcher_id}_")
    os.close(fd)

    try:
        await generate_cv_pdf(data, output_path)
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=f"CV_{researcher.name.replace(' ', '_')}.pdf",
            background=BackgroundTask(os.remove, output_path),
        )
    except Exception as e:
        try:
            os.remove(output_path)
        except OSError:
            pass
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

