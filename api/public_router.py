"""Explicit, read-only public API plus authenticated publication controls."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.bibliometrie.models import Publication, Researcher
from agents.mis.models import Projet
from api.public_models import PublicDataset, PublicProjectSummary, PublicPublication, PublicResearcherProfile
from api.public_schemas import (
    CatalogStatusUpdate, PublicDatasetCreate, PublicDatasetResponse,
    PublicProjectCreate, PublicProjectResponse, PublicPublicationCreate,
    PublicPublicationResponse, PublicationStatusUpdate, PublicResearcherResponse,
    ResearcherPublicationSettings,
)
from shared.database import get_db
from shared.security import User, require_roles


router = APIRouter(tags=["public-portal"])
_EDITOR = Depends(require_roles("researcher", "reviewer", "administrator"))
_REVIEWER = Depends(require_roles("reviewer", "administrator"))


def _ensure_reviewer(user: User) -> None:
    if user.role not in {"reviewer", "administrator"}:
        raise HTTPException(status_code=403, detail="A reviewer must approve public publication.")


# ── Public read-only surface: no authentication and no internal identifiers ──

@router.get("/researchers", response_model=list[PublicResearcherResponse])
async def public_researchers(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Researcher, PublicResearcherProfile)
        .join(PublicResearcherProfile, PublicResearcherProfile.researcher_id == Researcher.id)
        .where(
            PublicResearcherProfile.visibility.in_(["summary", "full"]),
            PublicResearcherProfile.consent_confirmed.is_(True),
            PublicResearcherProfile.approved_at.is_not(None),
        )
        .order_by(Researcher.name)
    )).all()
    return [PublicResearcherResponse(
        id=researcher.id,
        name=researcher.name,
        department=researcher.department,
        role=researcher.role,
        visibility=profile.visibility,
        public_bio=profile.public_bio if profile.visibility == "full" else None,
    ) for researcher, profile in rows]


@router.get("/publications", response_model=list[PublicPublicationResponse])
async def public_publications(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(PublicPublication)
        .where(PublicPublication.status == "published")
        .order_by(PublicPublication.published_at.desc())
    )).scalars().all()
    return rows


@router.get("/projects", response_model=list[PublicProjectResponse])
async def public_projects(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(PublicProjectSummary)
        .where(PublicProjectSummary.status == "published")
        .order_by(PublicProjectSummary.published_at.desc())
    )).scalars().all()
    return rows


@router.get("/datasets", response_model=list[PublicDatasetResponse])
async def public_datasets(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(PublicDataset)
        .where(PublicDataset.status == "published")
        .order_by(PublicDataset.published_at.desc())
    )).scalars().all()
    return rows


# ── Authenticated curation surface ──────────────────────────────────────────

@router.get("/admin/publications", response_model=list[PublicPublicationResponse])
async def list_publication_submissions(user: User = _EDITOR, db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(PublicPublication).order_by(PublicPublication.updated_at.desc()))).scalars().all()


@router.get("/admin/projects", response_model=list[PublicProjectResponse])
async def list_project_submissions(user: User = _EDITOR, db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(PublicProjectSummary).order_by(PublicProjectSummary.updated_at.desc()))).scalars().all()


@router.get("/admin/datasets", response_model=list[PublicDatasetResponse])
async def list_dataset_submissions(user: User = _EDITOR, db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(PublicDataset).order_by(PublicDataset.updated_at.desc()))).scalars().all()

@router.put("/admin/researchers/{researcher_id}")
async def set_researcher_publication_settings(
    researcher_id: int,
    data: ResearcherPublicationSettings,
    user: User = _EDITOR,
    db: AsyncSession = Depends(get_db),
):
    if await db.get(Researcher, researcher_id) is None:
        raise HTTPException(status_code=404, detail="Researcher not found")
    if data.visibility != "hidden" and not data.consent_confirmed:
        raise HTTPException(status_code=422, detail="Recorded consent is required before a profile can be public.")
    profile = await db.scalar(select(PublicResearcherProfile).where(PublicResearcherProfile.researcher_id == researcher_id))
    if profile is None:
        profile = PublicResearcherProfile(researcher_id=researcher_id)
        db.add(profile)
    profile.visibility = data.visibility
    profile.consent_confirmed = data.consent_confirmed
    profile.consent_version = data.consent_version
    profile.public_bio = data.public_bio
    profile.consented_at = datetime.utcnow() if data.consent_confirmed else None
    # Any change needs a fresh reviewer decision; hidden is effective instantly.
    profile.approved_at = None
    profile.approved_by = None
    await db.commit()
    return {"researcher_id": researcher_id, "visibility": profile.visibility, "awaiting_review": profile.visibility != "hidden"}


@router.post("/admin/researchers/{researcher_id}/approve")
async def approve_researcher_publication(
    researcher_id: int, user: User = _REVIEWER, db: AsyncSession = Depends(get_db)
):
    profile = await db.scalar(select(PublicResearcherProfile).where(PublicResearcherProfile.researcher_id == researcher_id))
    if profile is None or profile.visibility == "hidden" or not profile.consent_confirmed:
        raise HTTPException(status_code=409, detail="A visible profile with recorded consent is required before approval.")
    profile.approved_at = datetime.utcnow()
    profile.approved_by = user.email or user.id
    await db.commit()
    return {"researcher_id": researcher_id, "approved": True}


@router.post("/admin/publications", response_model=PublicPublicationResponse)
async def submit_publication(
    data: PublicPublicationCreate, user: User = _EDITOR, db: AsyncSession = Depends(get_db)
):
    source = await db.get(Publication, data.source_publication_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Internal publication not found")
    item = await db.scalar(select(PublicPublication).where(PublicPublication.source_publication_id == source.id))
    if item is None:
        item = PublicPublication(source_publication_id=source.id)
        db.add(item)
    item.title, item.abstract, item.doi = source.title, source.abstract, source.doi
    item.journal, item.year, item.keywords = source.journal, source.year, data.keywords
    item.status = data.status
    if data.status == "published":
        _ensure_reviewer(user)
        item.approved_at = item.published_at = datetime.utcnow()
        item.approved_by = user.email or user.id
    elif data.status == "withdrawn":
        _ensure_reviewer(user)
        item.published_at = None
    else:
        item.approved_at = item.approved_by = item.published_at = None
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/admin/publications/{public_id}", response_model=PublicPublicationResponse)
async def set_publication_status(
    public_id: str, data: PublicationStatusUpdate, user: User = _REVIEWER, db: AsyncSession = Depends(get_db)
):
    item = await db.get(PublicPublication, public_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Public publication record not found")
    item.status = data.status
    if data.status == "published":
        item.approved_at = item.published_at = datetime.utcnow()
        item.approved_by = user.email or user.id
    elif data.status == "withdrawn":
        item.published_at = None
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/admin/projects", response_model=PublicProjectResponse)
async def submit_project_summary(
    data: PublicProjectCreate, user: User = _EDITOR, db: AsyncSession = Depends(get_db)
):
    project = await db.get(Projet, data.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Internal project not found")
    item = await db.scalar(select(PublicProjectSummary).where(PublicProjectSummary.project_id == project.id))
    if item is None:
        item = PublicProjectSummary(project_id=project.id, title=project.nom, summary=data.summary)
        db.add(item)
    item.title, item.summary, item.research_area, item.status = project.nom, data.summary, data.research_area, data.status
    item.start_date, item.end_date = project.date_debut, project.date_fin_prevue
    if data.status == "published":
        _ensure_reviewer(user)
        item.approved_at = item.published_at = datetime.utcnow()
        item.approved_by = user.email or user.id
    elif data.status == "withdrawn":
        _ensure_reviewer(user)
        item.published_at = None
    else:
        item.approved_at = item.approved_by = item.published_at = None
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/admin/projects/{public_id}", response_model=PublicProjectResponse)
async def set_project_status(
    public_id: str, data: CatalogStatusUpdate, user: User = _REVIEWER, db: AsyncSession = Depends(get_db)
):
    item = await db.get(PublicProjectSummary, public_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Public project record not found")
    item.status = data.status
    if data.status == "published":
        item.approved_at = item.published_at = datetime.utcnow()
        item.approved_by = user.email or user.id
    elif data.status == "withdrawn":
        item.published_at = None
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/admin/datasets", response_model=PublicDatasetResponse)
async def submit_dataset(
    data: PublicDatasetCreate, user: User = _EDITOR, db: AsyncSession = Depends(get_db)
):
    item = PublicDataset(
        title=data.title, description=data.description, version=data.version, license=data.license,
        access_url=str(data.access_url) if data.access_url else None, citation=data.citation,
        keywords=data.keywords, status=data.status,
    )
    if data.status == "published":
        _ensure_reviewer(user)
        item.approved_at = item.published_at = datetime.utcnow()
        item.approved_by = user.email or user.id
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/admin/datasets/{dataset_id}", response_model=PublicDatasetResponse)
async def set_dataset_status(
    dataset_id: str, data: CatalogStatusUpdate, user: User = _REVIEWER, db: AsyncSession = Depends(get_db)
):
    item = await db.get(PublicDataset, dataset_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Public dataset record not found")
    item.status = data.status
    if data.status == "published":
        item.approved_at = item.published_at = datetime.utcnow()
        item.approved_by = user.email or user.id
    elif data.status == "withdrawn":
        item.published_at = None
    await db.commit()
    await db.refresh(item)
    return item


from api.public_models import InstitutionalContent
from api.public_schemas import ContentKind, ContentWrite, ContentResponse
_ADMIN = Depends(require_roles("administrator"))

@router.get("/content", response_model=list[ContentResponse])
async def public_content(kind: ContentKind, db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(InstitutionalContent).where(
        InstitutionalContent.kind == kind, InstitutionalContent.status == "published"
    ).order_by(InstitutionalContent.published_at.desc(), InstitutionalContent.id))).scalars().all()

@router.get("/admin/content", response_model=list[ContentResponse])
async def managed_content(kind: ContentKind, user: User = _ADMIN, db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(InstitutionalContent).where(
        InstitutionalContent.kind == kind
    ).order_by(InstitutionalContent.updated_at.desc()))).scalars().all()

def _write_content(item: InstitutionalContent, data: ContentWrite):
    item.kind, item.title, item.body = data.kind, data.title, data.body
    item.details = data.model_dump(mode="json", exclude={"kind", "title", "body"}, exclude_none=True)
    item.status = "draft"
    item.published_at = item.approved_by = None

@router.post("/admin/content", response_model=ContentResponse)
async def create_content(data: ContentWrite, user: User = _ADMIN, db: AsyncSession = Depends(get_db)):
    item = InstitutionalContent()
    _write_content(item, data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

@router.put("/admin/content/{content_id}", response_model=ContentResponse)
async def edit_content(content_id: str, data: ContentWrite, user: User = _ADMIN, db: AsyncSession = Depends(get_db)):
    item = await db.get(InstitutionalContent, content_id)
    if item is None:
        raise HTTPException(404, "Content not found")
    if item.kind != data.kind:
        raise HTTPException(422, "Content type cannot be changed.")
    _write_content(item, data)
    await db.commit()
    await db.refresh(item)
    return item

@router.patch("/admin/content/{content_id}/status", response_model=ContentResponse)
async def publish_content(content_id: str, data: CatalogStatusUpdate, user: User = _ADMIN, db: AsyncSession = Depends(get_db)):
    item = await db.get(InstitutionalContent, content_id)
    if item is None:
        raise HTTPException(404, "Content not found")
    item.status = data.status
    item.published_at = datetime.utcnow() if data.status == "published" else None
    item.approved_by = user.id if data.status == "published" else None
    await db.commit()
    await db.refresh(item)
    return item
