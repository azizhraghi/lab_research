"""Evidence records and immutable-at-API submission snapshots."""
from datetime import datetime, date
import hashlib
import json
import math
from typing import Literal
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from agents.mis.models import DossierSubmission, ProjectDossier, Projet, ProjectDeliverable, ProjectRisk
from agents.mis.dossier_router import read_dossier, persist, render_report, writer
from agents.mis.router import completion_report
from shared.database import get_db
from shared.security import User, get_current_user, require_roles

router = APIRouter()

class Version(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, allow_inf_nan=False)
    revision: int = Field(ge=1)

class Finding(Version):
    statement: str = Field(min_length=5,max_length=3000)
    assessment: Literal['proposed','supported_with_limits']
    limitations: str = Field(min_length=5,max_length=3000)
    reference_ids: list[str] = Field(default_factory=list,max_length=100)
    deliverable_ids: list[str] = Field(default_factory=list,max_length=100)
    evaluation_ids: list[str] = Field(default_factory=list,max_length=100)

class PairedRow(BaseModel):
    model_config = ConfigDict(extra='forbid',allow_inf_nan=False)
    observed: float = Field(ge=-1e12,le=1e12)
    predicted: float = Field(ge=-1e12,le=1e12)
    baseline: float = Field(ge=-1e12,le=1e12)

class Evaluation(Version):
    name: str = Field(min_length=3,max_length=200)
    origin: Literal['synthetic','field']
    split: Literal['development','held_out']
    unit: str = Field(min_length=1,max_length=80)
    provenance: str = Field(min_length=10,max_length=3000)
    protocol: str = Field(min_length=10,max_length=3000)
    rows: list[PairedRow] = Field(min_length=2,max_length=1000)

class Decision(BaseModel):
    model_config = ConfigDict(extra='forbid',str_strip_whitespace=True)
    status: Literal['approved','changes_requested']
    feedback: str = Field(min_length=10,max_length=10000)

def metrics(rows, column):
    errors=[row[column]-row['observed'] for row in rows]
    return dict(mae=sum(abs(e) for e in errors)/len(errors),rmse=math.sqrt(sum(e*e for e in errors)/len(errors)),bias=sum(errors)/len(errors))

@router.post('/projets/{project_id}/dossier/findings')
async def add_finding(project_id: str, data: Finding, user: User=writer, db: AsyncSession=Depends(get_db)):
    dossier=await read_dossier(project_id,db)
    operations=await completion_report(project_id,db)
    for supplied,valid in ((data.reference_ids,{r['id'] for r in dossier['references']}),
        (data.deliverable_ids,{r['id'] for r in operations['deliverables']}),
        (data.evaluation_ids,{r['id'] for r in dossier['evaluations']})):
        if not set(supplied)<=valid: raise HTTPException(422,'Evidence must belong to this project dossier.')
    if data.assessment=='supported_with_limits' and not (data.reference_ids or data.deliverable_ids or data.evaluation_ids):
        raise HTTPException(422,'A supported finding needs at least one evidence link.')
    if len(dossier['claims'])>=100: raise HTTPException(422,'Maximum 100 findings per dossier.')
    claim=dict(data.model_dump(exclude={'revision'}),id=str(uuid4()),created_by=user.id,created_at=datetime.utcnow().isoformat())
    return await persist(project_id,data.revision,{'claims':[*dossier['claims'],claim]},user,db)

@router.delete('/projets/{project_id}/dossier/findings/{finding_id}')
async def remove_finding(project_id: str,finding_id: str,revision:int,user:User=writer,db:AsyncSession=Depends(get_db)):
    dossier=await read_dossier(project_id,db)
    remaining=[r for r in dossier['claims'] if r['id']!=finding_id]
    if len(remaining)==len(dossier['claims']): raise HTTPException(404,'Finding not found')
    return await persist(project_id,revision,{'claims':remaining},user,db)

@router.post('/projets/{project_id}/dossier/evaluations')
async def evaluate(project_id:str,data:Evaluation,user:User=writer,db:AsyncSession=Depends(get_db)):
    dossier=await read_dossier(project_id,db)
    if len(dossier['evaluations'])>=30: raise HTTPException(422,'Maximum 30 evaluations per dossier.')
    run=data.model_dump(exclude={'revision'})
    run.update(id=str(uuid4()),created_by=user.id,created_at=datetime.utcnow().isoformat(),
        model_metrics=metrics(run['rows'],'predicted'),baseline_metrics=metrics(run['rows'],'baseline'))
    return await persist(project_id,data.revision,{'evaluations':[*dossier['evaluations'],run]},user,db)

def submission_summary(row):
    return {name:getattr(row,name) for name in ('id','project_id','revision','digest','submitted_by','submitted_at','status','reviewed_by','reviewed_at','feedback')}

@router.post('/projets/{project_id}/dossier/submissions')
async def submit(project_id:str,data:Version,user:User=writer,db:AsyncSession=Depends(get_db)):
    dossier=await read_dossier(project_id,db)
    if dossier['revision']!=data.revision: raise HTTPException(409,'Dossier changed. Reload before submitting.')
    if not all(dossier[key].strip() for key in ('questions','approach','limitations')) or not dossier['claims']:
        raise HTTPException(422,'Record questions, approach, limitations and at least one evidence-linked or proposed finding before submission.')
    # A no-op conditional UPDATE holds a row lock until the snapshot is committed.
    locked=await db.execute(update(ProjectDossier).where(ProjectDossier.project_id==project_id,
        ProjectDossier.revision==data.revision).values(revision=data.revision))
    if locked.rowcount!=1: raise HTTPException(409,'Dossier changed. Reload before submitting.')
    snapshot=jsonable_encoder(dict(dossier=dossier,operations=await completion_report(project_id,db)))
    digest=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    row=DossierSubmission(id=str(uuid4()),project_id=project_id,revision=data.revision,snapshot=snapshot,digest=digest,
        submitted_by=user.id,submitted_at=datetime.utcnow(),status='pending')
    db.add(row)
    try: await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409,'This revision was already submitted. Save a revised dossier before resubmitting.') from exc
    return submission_summary(row)

@router.get('/projets/{project_id}/dossier/submissions')
async def submissions(project_id:str,db:AsyncSession=Depends(get_db)):
    await read_dossier(project_id,db)
    rows=(await db.scalars(select(DossierSubmission).where(DossierSubmission.project_id==project_id).order_by(DossierSubmission.submitted_at.desc()))).all()
    return [submission_summary(row) for row in rows]

@router.get('/dossier-submissions/{submission_id}')
async def inspect_submission(submission_id:str,db:AsyncSession=Depends(get_db)):
    row=await db.get(DossierSubmission,submission_id)
    if row is None: raise HTTPException(404,'Submission not found')
    return dict(**submission_summary(row),snapshot=row.snapshot)

@router.post('/dossier-submissions/{submission_id}/decision')
async def decide(submission_id:str,data:Decision,user:User=Depends(require_roles('reviewer','administrator')),db:AsyncSession=Depends(get_db)):
    row=await db.get(DossierSubmission,submission_id)
    if row is None: raise HTTPException(404,'Submission not found')
    if row.submitted_by==user.id: raise HTTPException(403,'A different reviewer must assess this submission.')
    result=await db.execute(update(DossierSubmission).where(DossierSubmission.id==submission_id,DossierSubmission.status=='pending').values(
        status=data.status,feedback=data.feedback,reviewed_by=user.id,reviewed_at=datetime.utcnow()).execution_options(synchronize_session=False))
    if result.rowcount!=1: raise HTTPException(409,'This submission already has a decision.')
    await db.commit()
    await db.refresh(row)
    return submission_summary(row)

@router.get('/dossier-submissions/{submission_id}/export')
async def export_submission(submission_id:str,db:AsyncSession=Depends(get_db)):
    from html import escape
    row=await db.get(DossierSubmission,submission_id)
    if row is None: raise HTTPException(404,'Submission not found')
    header='<h2>Submission review record</h2><p>'+escape(f'Status: {row.status} | Submitted by: {row.submitted_by} at {row.submitted_at} UTC | Reviewed by: {row.reviewed_by or "pending"} at {row.reviewed_at or "pending"}')+'</p><p>'+escape(row.feedback or 'No decision yet.')+'</p><p>Snapshot SHA-256: '+row.digest+'</p><p>Approval applies to this submission only; it does not establish scientific validity.</p>'
    html=render_report(row.snapshot['dossier'],row.snapshot['operations'], submitted=True).replace('<body>','<body>'+header,1)
    return dict(filename=f'submission-{row.id}.html',content=html)

@router.get('/dossier-submissions/{submission_id}/comparison')
async def compare_submission(submission_id:str, against:str, db:AsyncSession=Depends(get_db)):
    from agents.mis.submission_diff import compare_snapshots
    current=await db.get(DossierSubmission,submission_id)
    previous=await db.get(DossierSubmission,against)
    if current is None or previous is None: raise HTTPException(404,'Submission not found')
    if current.project_id != previous.project_id: raise HTTPException(422,'Compare submissions from the same project.')
    return dict(before_revision=previous.revision,after_revision=current.revision,
        changes=compare_snapshots(previous.snapshot,current.snapshot))

@router.get('/attention')
async def attention(user:User=Depends(get_current_user),db:AsyncSession=Depends(get_db)):
    projects={p.id:p.nom for p in (await db.scalars(select(Projet))).all()}
    result=[]
    pending=(await db.scalars(select(DossierSubmission).where(DossierSubmission.status=='pending'))).all()
    for row in pending:
        result.append(dict(kind='review',project_id=row.project_id,title=f"{projects.get(row.project_id,'Archived project')} · revision {row.revision}",
            detail='Awaiting another reviewer' if row.submitted_by==user.id else 'Submission awaiting review',submission_id=row.id))
    overdue=(await db.scalars(select(ProjectDeliverable).where(ProjectDeliverable.due_date<date.today(),ProjectDeliverable.status!='approved'))).all()
    result.extend(dict(kind='deliverable',project_id=r.project_id,title=r.title,detail='Overdue deliverable') for r in overdue)
    risks=(await db.scalars(select(ProjectRisk).where(ProjectRisk.status=='open'))).all()
    result.extend(dict(kind='risk',project_id=r.project_id,title=r.title,detail='Open project risk') for r in risks)
    return result
