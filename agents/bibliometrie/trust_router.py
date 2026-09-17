"""Record human identity checks without representing them as metric validation."""
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from agents.bibliometrie.models import Researcher, IdentityReview, BiblioIndicator, Publication, ResearcherPublication
from shared.database import get_db
from shared.security import User, require_roles
router=APIRouter()


@router.get('/researchers/{researcher_id}/publication-audit')
async def publication_audit(researcher_id:int,db:AsyncSession=Depends(get_db)):
    from collections import Counter
    import re
    if await db.get(Researcher,researcher_id) is None: raise HTTPException(404,'Researcher not found')
    rows=list(await db.scalars(select(Publication).join(ResearcherPublication,
        ResearcherPublication.publication_id==Publication.id).where(ResearcherPublication.researcher_id==researcher_id)))
    def normalized(title): return re.sub(r'\W+', ' ', (title or '').casefold()).strip()
    counts=Counter(normalized(r.title) for r in rows if normalized(r.title))
    items=[]
    for row in rows:
        issues=[]
        if not (row.title or '').strip(): issues.append('Missing title')
        if not row.doi: issues.append('No DOI recorded; this is not necessarily an error')
        if not row.year: issues.append('Missing publication year')
        if not row.source: issues.append('Unknown import source')
        if normalized(row.title) and counts[normalized(row.title)]>1: issues.append('Repeated title; check whether these are distinct works')
        items.append(dict(id=row.id,title=row.title,doi=row.doi,year=row.year,source=row.source or 'unknown',issues=issues))
    return dict(researcher_id=researcher_id,total=len(items),needs_attention=sum(bool(i['issues']) for i in items),
        validation='Metadata checks only; authorship and citation counts are not independently verified.',publications=items)

def identifiers(row):
    return {key:getattr(row,key) for key in ('name','orcid_id','scholar_id','scopus_id')}

class IdentityCheck(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    identifiers: dict[str,str|None]
    rationale: str=Field(min_length=20,max_length=3000)

@router.get('/researchers/{researcher_id}/trust')
async def trust(researcher_id:int,db:AsyncSession=Depends(get_db)):
    row=await db.get(Researcher,researcher_id)
    if row is None: raise HTTPException(404,'Researcher not found')
    history=(await db.scalars(select(IdentityReview).where(IdentityReview.researcher_id==researcher_id).order_by(IdentityReview.reviewed_at.desc()))).all()
    metrics=(await db.scalars(select(BiblioIndicator).where(BiblioIndicator.researcher_id==researcher_id))).all()
    current=identifiers(row)
    return dict(identifiers=current,identity_status='manually_confirmed' if history and history[0].identifiers==current else 'needs_review',
        history=[dict(id=r.id,identifiers=r.identifiers,reviewer_id=r.reviewer_id,rationale=r.rationale,reviewed_at=r.reviewed_at) for r in history],
        metrics=[dict(name=m.metric_name,value=m.value,source=m.source or 'unknown (legacy record)',retrieved_at=m.computed_at,validation='not independently verified') for m in metrics])

@router.post('/researchers/{researcher_id}/trust')
async def confirm(researcher_id:int,data:IdentityCheck,user:User=Depends(require_roles('reviewer','administrator')),db:AsyncSession=Depends(get_db)):
    row=await db.scalar(select(Researcher).where(Researcher.id==researcher_id).with_for_update())
    if row is None: raise HTTPException(404,'Researcher not found')
    current=identifiers(row)
    if data.identifiers!=current: raise HTTPException(409,'Identifiers changed. Reload before confirming.')
    if not any(current[k] for k in ('orcid_id','scholar_id','scopus_id')): raise HTTPException(422,'Add an identifier before recording an identity check.')
    db.add(IdentityReview(id=str(uuid4()),researcher_id=researcher_id,identifiers=current,reviewer_id=user.id,rationale=data.rationale))
    await db.commit()
    return await trust(researcher_id,db)
