"""Internal project dossiers; private review annotations are never copied."""
from datetime import datetime
from html import escape
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from agents.mis.models import ProjectDossier, Projet
from agents.mis.router import completion_report
from agents.veille.research_router import owned
from shared.database import get_db
from shared.security import User, require_roles

router = APIRouter()
writer = Depends(require_roles("researcher", "reviewer", "administrator"))
TEXT_FIELDS = ("questions", "approach", "findings", "limitations")

class Narrative(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    revision: int = Field(ge=0)
    questions: str = Field(max_length=12000)
    approach: str = Field(max_length=12000)
    findings: str = Field(max_length=20000)
    limitations: str = Field(max_length=12000)

class ReferenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    revision: int = Field(ge=0)
    review_id: str = Field(min_length=1, max_length=100)
    item_id: str = Field(min_length=1, max_length=100)
    rationale: str = Field(min_length=3, max_length=3000)

async def read_dossier(project_id, db):
    if await db.get(Projet, project_id) is None:
        raise HTTPException(404, "Project not found")
    row = await db.get(ProjectDossier, project_id)
    if row is None:
        return dict(project_id=project_id, revision=0, references=[], claims=[], evaluations=[], updated_by=None,
                    updated_at=None, **{name: "" for name in TEXT_FIELDS})
    return {name: getattr(row, name) for name in ("project_id", "revision", "references", "claims", "evaluations", "updated_by", "updated_at", *TEXT_FIELDS)}

async def persist(project_id, revision, changes, user, db):
    current = await read_dossier(project_id, db)
    if current["revision"] != revision:
        raise HTTPException(409, "Dossier changed. Reload the latest version before saving; keep a copy of your edits.")
    values = dict(changes, revision=revision+1, updated_by=user.id, updated_at=datetime.utcnow())
    if revision == 0:
        current.update(values)
        db.add(ProjectDossier(**current))
    else:
        result = await db.execute(update(ProjectDossier).where(
            ProjectDossier.project_id == project_id, ProjectDossier.revision == revision
        ).values(**values).execution_options(synchronize_session=False))
        if result.rowcount != 1:
            await db.rollback()
            raise HTTPException(409, "Dossier changed. Reload before saving.")
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "Dossier changed. Reload before saving.") from exc
    db.expire_all()
    return await read_dossier(project_id, db)

@router.get("/projets/{project_id}/dossier")
async def get_dossier(project_id: str, db: AsyncSession = Depends(get_db)):
    return await read_dossier(project_id, db)

@router.put("/projets/{project_id}/dossier")
async def save_dossier(project_id: str, data: Narrative, user: User = writer, db: AsyncSession = Depends(get_db)):
    return await persist(project_id, data.revision, data.model_dump(exclude={"revision"}), user, db)

@router.post("/projets/{project_id}/dossier/references")
async def add_reference(project_id: str, data: ReferenceInput, user: User = writer, db: AsyncSession = Depends(get_db)):
    current = await read_dossier(project_id, db)
    review = await owned(db, data.review_id, user)
    item = next((item for item in review.items if item["id"] == data.item_id), None)
    if item is None:
        raise HTTPException(404, "Review item not found")
    if item["decision"] != "include":
        raise HTTPException(409, "Include the paper in your literature review before adding it to a project.")
    references = current["references"]
    if any((item.get("doi") and ref.get("doi") == item["doi"]) or ref["url"] == item["url"] for ref in references):
        raise HTTPException(409, "This paper is already in the dossier.")
    if len(references) >= 100:
        raise HTTPException(422, "A dossier supports at most 100 selected references.")
    snapshot = {key: item.get(key) for key in ("title", "authors", "doi", "url", "published_at", "evidence_basis", "evidence_excerpt")}
    snapshot.update(id=str(uuid4()), rationale=data.rationale, added_by=user.id,
                    captured_at=datetime.utcnow().isoformat())
    return await persist(project_id, data.revision, {"references": [*references, snapshot]}, user, db)

@router.delete("/projets/{project_id}/dossier/references/{reference_id}")
async def remove_reference(project_id: str, reference_id: str, revision: int = Query(ge=1),
                           user: User = writer, db: AsyncSession = Depends(get_db)):
    current = await read_dossier(project_id, db)
    remaining = [ref for ref in current["references"] if ref["id"] != reference_id]
    if any(reference_id in claim['reference_ids'] for claim in current['claims']):
        raise HTTPException(409, "Remove or revise the findings citing this reference first.")
    if len(remaining) == len(current["references"]):
        raise HTTPException(404, "Reference not found")
    return await persist(project_id, revision, {"references": remaining}, user, db)

def render_report(dossier, operations, submitted=False):
    """Portable, printable HTML. All user/source text is escaped; no active content."""
    def e(value): return escape(str(value if value is not None else "Not recorded"), quote=True)
    def paragraph(value): return '<p class="prose">'+e(value or "Not recorded")+'</p>'
    project = operations["project"]
    sections = [f'<h1>{e(project["nom"])}</h1><p class="subtitle">Project research dossier · revision {dossier["revision"]}</p>',
        paragraph(f'Lead: {project["responsable"]} | Status: {project["statut"]}'),
        paragraph('Generated: '+operations['generated_at']+' UTC'),
        paragraph('Preserved submission. Review status is recorded above; research statements remain subject to scientific validation.' if submitted else 'Internal working report. Research statements are author-entered; this export is not supervisor approval or scientific validation.')]
    for key, title in zip(TEXT_FIELDS, ("Research questions", "Approach and methods", "Findings and conclusions", "Limitations and missing evidence")):
        sections.append('<h2>'+title+'</h2>'+paragraph(dossier[key]))
    sections.append('<h2>Selected literature</h2>')
    for number, ref in enumerate(dossier["references"], 1):
        sections.append('<article><h3>'+e(f'{number}. {ref["title"]}')+'</h3>'
            +paragraph(', '.join(ref.get('authors') or []))
            +paragraph('Source: '+str(ref['url'])+' | DOI: '+str(ref.get('doi') or 'not supplied'))
            +paragraph('Journal date (may be approximate): '+str(ref.get('published_at') or 'unknown'))
            +paragraph('Project relevance: '+ref['rationale'])
            +paragraph('Evidence basis: '+str(ref['evidence_basis']))
            +paragraph('Source excerpt: '+str(ref.get('evidence_excerpt') or 'No abstract available.'))
            +paragraph('Captured: '+ref['captured_at']+' UTC')+'</article>')
    if not dossier['references']: sections.append(paragraph('No literature selected.'))
    sections.append('<h2>Evidence-linked findings</h2>')
    refs = {ref['id']: ref['title'] for ref in dossier['references']}
    deliverables = {item['id']: item['title'] for item in operations['deliverables']}
    evaluations = {item['id']: item['name'] for item in dossier.get('evaluations', [])}
    for claim in dossier.get('claims', []):
        sections.append('<h3>'+e(claim['statement'])+'</h3>'+paragraph('Author assessment: '+claim['assessment'])
            +paragraph('Limitations: '+claim['limitations'])
            +paragraph('Literature: '+'; '.join(refs.get(key, 'Reference unavailable') for key in claim['reference_ids']))
            +paragraph('Deliverable evidence: '+'; '.join(deliverables.get(key, 'Unavailable: '+key) for key in claim['deliverable_ids']))
            +paragraph('Evaluation evidence: '+'; '.join(evaluations.get(key, 'Unavailable: '+key) for key in claim['evaluation_ids'])))
    sections.append('<h2>Evaluation records</h2>')
    for run in dossier.get('evaluations', []):
        sections.append('<h3>'+e(run['name'])+'</h3>'+paragraph(f"Origin: {run['origin']} | Split: {run['split']} | Unit: {run['unit']} | N: {len(run['rows'])}")
            +paragraph('Dataset provenance: '+run['provenance'])+paragraph('Protocol: '+run['protocol'])
            +paragraph('Model: '+str(run['model_metrics'])+' | Baseline: '+str(run['baseline_metrics']))
            +paragraph('These are errors on supplied paired values, not independent verification of provenance or scientific validity.'))
    sections.append('<h2>Outstanding project work</h2>')
    sections.extend(paragraph(item) for item in operations['outstanding'] or ['No outstanding work identified by the operational checks.'])
    for key in ('milestones', 'deliverables', 'risks'):
        sections.append('<h2>'+key.title()+'</h2>')
        sections.extend(paragraph(item['title']+' — '+item['status']) for item in operations[key])
        if not operations[key]: sections.append(paragraph('None recorded.'))
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(project['nom'])+' — research dossier</title><style>body{font:16px/1.6 system-ui,sans-serif;color:#183b35;max-width:850px;margin:40px auto;padding:0 24px}h1{font-size:30px}h2{border-bottom:1px solid #aac6bf;margin-top:32px}h3{font-size:18px}.subtitle{color:#526963}.prose{white-space:pre-wrap;overflow-wrap:anywhere}article{border-left:3px solid #aac6bf;padding-left:18px;margin:24px 0}@media print{body{margin:0;font-size:11pt}h2,h3{break-after:avoid}p{orphans:3;widows:3}}</style><body>'+''.join(sections)+'</body></html>'

@router.get("/projets/{project_id}/dossier/export")
async def export_dossier(project_id: str, db: AsyncSession = Depends(get_db)):
    dossier = await read_dossier(project_id, db)
    operations = await completion_report(project_id, db)
    return dict(filename=f"project-{project_id}-dossier.html", content=render_report(dossier, operations))
