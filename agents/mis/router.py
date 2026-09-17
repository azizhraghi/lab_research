# -*- coding: utf-8 -*-
"""MIS Router – CRUD endpoints for projects, personnel, equipment, budgets.

Adapted from Friend 1's router to use monorepo imports (shared.database).
"""
from __future__ import annotations
import json
from datetime import date, datetime, timedelta
from uuid import uuid4
from pydantic import ValidationError, BaseModel, Field, ConfigDict

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from agents.mis.schemas import (
    ProjetSchema, PersonnelSchema, EquipementSchema, BudgetSchema,
    BudgetEntryCreate, BudgetEntryResponse, BudgetSummary,
    DeliverableCreate, DeliverableResponse, DeliverableUpdate,
    MaintenanceCreate, MaintenanceResponse, MaintenanceUpdate,
    MilestoneCreate, MilestoneResponse, MilestoneUpdate,
    MonthlyProjectReport,
    OperationalAlert, ReservationCreate, ReservationResponse,
    RiskCreate, RiskResponse, RiskUpdate, WorkloadResponse,
)
from agents.mis.models import (
    Projet as ProjetModel,
    Personnel as PersonnelModel,
    Equipement as EquipementModel,
    Budget as BudgetModel,
    BudgetEntry,
    EquipmentMaintenance,
    EquipmentReservation,
    ProjectDeliverable,
    ProjectMilestone,
    ProjectRisk,
)
from shared.database import get_db
from shared.outbox import enqueue_event, outbox_dispatcher
from shared.security import User, require_roles
from shared.schemas import Event

router = APIRouter(tags=["MIS"])

# Reads (GET) are open to any authenticated user. Writes (POST/PUT/DELETE) are
# restricted to editor/admin roles — matches the guard pattern already used by
# the veille/biblio/twin routers.
_WRITE_GUARD = [Depends(require_roles("researcher", "reviewer", "administrator"))]


def _validated_update(schema, current: dict, changes: dict) -> dict:
    """Validate the merged record before touching ORM attributes or dates."""
    forbidden = set(changes) - (set(schema.model_fields) - {"id"})
    if forbidden:
        raise HTTPException(status_code=422, detail="Fields cannot be updated: " + ", ".join(sorted(forbidden)))
    try:
        validated = schema.model_validate({**current, **changes}).model_dump()
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=json.loads(exc.json(include_url=False))) from exc
    return {key: validated[key] for key in changes}


def _reject_null_fields(changes: dict, required: set[str]) -> None:
    if any(key in required and value is None for key, value in changes.items()):
        raise HTTPException(422, "Required fields cannot be null.")


# ── Projets CRUD ──────────────────────────────────────────────────────

@router.post("/projets/", response_model=ProjetSchema, dependencies=_WRITE_GUARD)
async def create_projet(projet: ProjetSchema, db: AsyncSession = Depends(get_db)) -> ProjetSchema:
    db_projet = ProjetModel(
        id=projet.id, nom=projet.nom, description=projet.description,
        statut=projet.statut, date_debut=projet.date_debut,
        date_fin_prevue=projet.date_fin_prevue,
        budget_alloue=projet.budget_alloue, responsable=projet.responsable,
    )
    db.add(db_projet)
    await db.flush()
    created = ProjetSchema.model_validate(db_projet.__dict__)

    # The project and its event now commit together. If the request succeeds,
    # the orchestrator will eventually see it even during a broker outage.
    from agents.mis.agent import mis_agent
    await enqueue_event(db, "events", Event(
        id=str(uuid4()),
        type="projet.created",
        source_agent=mis_agent.name,
        payload=created.model_dump(mode="json"),
    ))
    await db.commit()
    await db.refresh(db_projet)
    outbox_dispatcher.notify()
    return created


@router.get("/projets/", response_model=list[ProjetSchema])
async def list_projets(db: AsyncSession = Depends(get_db)) -> list[ProjetSchema]:
    result = await db.execute(select(ProjetModel))
    return [ProjetSchema.model_validate(p.__dict__) for p in result.scalars().all()]


@router.get("/projets/{projet_id}", response_model=ProjetSchema)
async def get_projet(projet_id: str, db: AsyncSession = Depends(get_db)) -> ProjetSchema:
    projet = await db.get(ProjetModel, projet_id)
    if projet is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return ProjetSchema.model_validate(projet.__dict__)


@router.put("/projets/{projet_id}", response_model=ProjetSchema, dependencies=_WRITE_GUARD)
async def update_projet(projet_id: str, data: dict, db: AsyncSession = Depends(get_db)) -> ProjetSchema:
    projet = await db.get(ProjetModel, projet_id)
    if projet is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    changes = _validated_update(ProjetSchema, projet.__dict__, data)
    for key, value in changes.items():
        setattr(projet, key, value)
    await enqueue_event(db, "events", Event(
        id=str(uuid4()), type="projet.updated", source_agent="mis",
        payload=ProjetSchema.model_validate(projet.__dict__).model_dump(mode="json"),
    ))
    await db.commit()
    await db.refresh(projet)
    outbox_dispatcher.notify()
    return ProjetSchema.model_validate(projet.__dict__)


@router.delete("/projets/{projet_id}", dependencies=_WRITE_GUARD)
async def delete_projet(projet_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    projet = await db.get(ProjetModel, projet_id)
    if projet is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    dependent_records = await db.scalar(select(func.count()).select_from(ProjectMilestone).where(ProjectMilestone.project_id == projet_id)) or 0
    dependent_records += await db.scalar(select(func.count()).select_from(ProjectDeliverable).where(ProjectDeliverable.project_id == projet_id)) or 0
    dependent_records += await db.scalar(select(func.count()).select_from(ProjectRisk).where(ProjectRisk.project_id == projet_id)) or 0
    dependent_records += await db.scalar(select(func.count()).select_from(BudgetModel).where(BudgetModel.projet_id == projet_id)) or 0
    dependent_records += await db.scalar(select(func.count()).select_from(EquipmentReservation).where(EquipmentReservation.project_id == projet_id)) or 0
    if dependent_records:
        raise HTTPException(
            status_code=409,
            detail="This project has operational records. Archive or reassign them before deleting the project.",
        )
    await db.delete(projet)
    await db.commit()
    return {"message": f"Projet {projet_id} supprime avec succes"}


# ── Personnel CRUD ────────────────────────────────────────────────────

class StaffAssignment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    personnel_id: str = Field(min_length=1, max_length=100)


@router.post('/projets/{project_id}/assign-staff', dependencies=_WRITE_GUARD)
async def assign_available_staff(project_id: str, data: StaffAssignment, db: AsyncSession = Depends(get_db)):
    if await db.get(ProjetModel, project_id) is None:
        raise HTTPException(404, 'Project not found')
    result = await db.execute(update(PersonnelModel).where(
        PersonnelModel.id == data.personnel_id, PersonnelModel.projet_actuel_id.is_(None),
        PersonnelModel.disponible.is_(True),
    ).values(projet_actuel_id=project_id))
    if result.rowcount != 1:
        raise HTTPException(409, 'This staff member is no longer available and unassigned. Reload the team list.')
    await _enqueue_mis_event(db, 'mis.staff_assigned', dict(project_id=project_id, personnel_id=data.personnel_id))
    await db.commit()
    outbox_dispatcher.notify()
    return dict(project_id=project_id, personnel_id=data.personnel_id)

@router.post("/personnels/", response_model=PersonnelSchema, dependencies=_WRITE_GUARD)
async def create_personnel(personnel: PersonnelSchema, db: AsyncSession = Depends(get_db)) -> PersonnelSchema:
    db_personnel = PersonnelModel(
        id=personnel.id, nom=personnel.nom, prenom=personnel.prenom,
        email=personnel.email, role=personnel.role,
        competences=json.dumps(personnel.competences),
        disponible=personnel.disponible,
        projet_actuel_id=personnel.projet_actuel_id,
    )
    db.add(db_personnel)
    await db.commit()
    await db.refresh(db_personnel)
    data = db_personnel.__dict__.copy()
    data["competences"] = json.loads(data["competences"])
    return PersonnelSchema.model_validate(data)


@router.get("/personnels/", response_model=list[PersonnelSchema])
async def list_personnels(db: AsyncSession = Depends(get_db)) -> list[PersonnelSchema]:
    result = await db.execute(select(PersonnelModel))
    out = []
    for p in result.scalars().all():
        data = p.__dict__.copy()
        data["competences"] = json.loads(data["competences"])
        out.append(PersonnelSchema.model_validate(data))
    return out


@router.get("/personnels/{personnel_id}", response_model=PersonnelSchema)
async def get_personnel(personnel_id: str, db: AsyncSession = Depends(get_db)) -> PersonnelSchema:
    personnel = await db.get(PersonnelModel, personnel_id)
    if personnel is None:
        raise HTTPException(status_code=404, detail="Personnel introuvable")
    data = personnel.__dict__.copy()
    data["competences"] = json.loads(data["competences"])
    return PersonnelSchema.model_validate(data)


@router.put("/personnels/{personnel_id}", response_model=PersonnelSchema, dependencies=_WRITE_GUARD)
async def update_personnel(personnel_id: str, data: dict, db: AsyncSession = Depends(get_db)) -> PersonnelSchema:
    personnel = await db.get(PersonnelModel, personnel_id)
    if personnel is None:
        raise HTTPException(status_code=404, detail="Personnel introuvable")
    current = {**personnel.__dict__, "competences": json.loads(personnel.competences)}
    changes = _validated_update(PersonnelSchema, current, data)
    if "competences" in changes:
        changes["competences"] = json.dumps(changes["competences"])
    for key, value in changes.items():
        setattr(personnel, key, value)
    await db.commit()
    await db.refresh(personnel)
    out = personnel.__dict__.copy()
    out["competences"] = json.loads(out["competences"])
    return PersonnelSchema.model_validate(out)


@router.delete("/personnels/{personnel_id}", dependencies=_WRITE_GUARD)
async def delete_personnel(personnel_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    personnel = await db.get(PersonnelModel, personnel_id)
    if personnel is None:
        raise HTTPException(status_code=404, detail="Personnel introuvable")
    await db.delete(personnel)
    await db.commit()
    return {"message": f"Personnel {personnel_id} supprime avec succes"}


# ── Équipements CRUD ──────────────────────────────────────────────────

@router.post("/equipements/", response_model=EquipementSchema, dependencies=_WRITE_GUARD)
async def create_equipement(equipement: EquipementSchema, db: AsyncSession = Depends(get_db)) -> EquipementSchema:
    db_equipement = EquipementModel(
        id=equipement.id, nom=equipement.nom, type=equipement.type,
        etat=equipement.etat, localisation=equipement.localisation,
        responsable_id=equipement.responsable_id,
        date_acquisition=equipement.date_acquisition,
        valeur_estimee=equipement.valeur_estimee,
    )
    db.add(db_equipement)
    await db.commit()
    await db.refresh(db_equipement)
    return EquipementSchema.model_validate(db_equipement.__dict__)


@router.get("/equipements/", response_model=list[EquipementSchema])
async def list_equipements(db: AsyncSession = Depends(get_db)) -> list[EquipementSchema]:
    result = await db.execute(select(EquipementModel))
    return [EquipementSchema.model_validate(e.__dict__) for e in result.scalars().all()]


@router.get("/equipements/{equipement_id}", response_model=EquipementSchema)
async def get_equipement(equipement_id: str, db: AsyncSession = Depends(get_db)) -> EquipementSchema:
    equipement = await db.get(EquipementModel, equipement_id)
    if equipement is None:
        raise HTTPException(status_code=404, detail="Equipement introuvable")
    return EquipementSchema.model_validate(equipement.__dict__)


@router.put("/equipements/{equipement_id}", response_model=EquipementSchema, dependencies=_WRITE_GUARD)
async def update_equipement(equipement_id: str, data: dict, db: AsyncSession = Depends(get_db)) -> EquipementSchema:
    equipement = await db.get(EquipementModel, equipement_id)
    if equipement is None:
        raise HTTPException(status_code=404, detail="Equipement introuvable")
    for key, value in _validated_update(EquipementSchema, equipement.__dict__, data).items():
        setattr(equipement, key, value)
    await db.commit()
    await db.refresh(equipement)
    return EquipementSchema.model_validate(equipement.__dict__)


@router.delete("/equipements/{equipement_id}", dependencies=_WRITE_GUARD)
async def delete_equipement(equipement_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    equipement = await db.get(EquipementModel, equipement_id)
    if equipement is None:
        raise HTTPException(status_code=404, detail="Equipement introuvable")
    has_history = await db.scalar(select(func.count()).select_from(EquipmentReservation).where(
        EquipmentReservation.equipment_id == equipement_id,
    )) or await db.scalar(select(func.count()).select_from(EquipmentMaintenance).where(
        EquipmentMaintenance.equipment_id == equipement_id,
    ))
    if has_history:
        raise HTTPException(
            status_code=409,
            detail="This equipment has reservation or maintenance history and cannot be deleted.",
        )
    await db.delete(equipement)
    await db.commit()
    return {"message": f"Equipement {equipement_id} supprime avec succes"}


# ── Budgets CRUD ──────────────────────────────────────────────────────

@router.post("/budgets/", response_model=BudgetSchema, dependencies=_WRITE_GUARD)
async def create_budget(budget: BudgetSchema, db: AsyncSession = Depends(get_db)) -> BudgetSchema:
    db_budget = BudgetModel(
        id=budget.id, projet_id=budget.projet_id,
        montant_alloue=budget.montant_alloue,
        montant_depense=budget.montant_depense, devise=budget.devise,
        date_debut=budget.date_debut, date_fin=budget.date_fin,
        description=budget.description,
    )
    db.add(db_budget)
    await db.commit()
    await db.refresh(db_budget)
    return BudgetSchema.model_validate(db_budget.__dict__)


@router.get("/budgets/", response_model=list[BudgetSchema])
async def list_budgets(db: AsyncSession = Depends(get_db)) -> list[BudgetSchema]:
    result = await db.execute(select(BudgetModel))
    return [BudgetSchema.model_validate(b.__dict__) for b in result.scalars().all()]


@router.get("/budgets/{budget_id}", response_model=BudgetSchema)
async def get_budget(budget_id: str, db: AsyncSession = Depends(get_db)) -> BudgetSchema:
    budget = await db.get(BudgetModel, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    return BudgetSchema.model_validate(budget.__dict__)


@router.put("/budgets/{budget_id}", response_model=BudgetSchema, dependencies=_WRITE_GUARD)
async def update_budget(budget_id: str, data: dict, db: AsyncSession = Depends(get_db)) -> BudgetSchema:
    budget = await db.get(BudgetModel, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    for key, value in _validated_update(BudgetSchema, budget.__dict__, data).items():
        setattr(budget, key, value)
    await db.commit()
    await db.refresh(budget)
    return BudgetSchema.model_validate(budget.__dict__)


@router.delete("/budgets/{budget_id}", dependencies=_WRITE_GUARD)
async def delete_budget(budget_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    budget = await db.get(BudgetModel, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    entry_count = await db.scalar(select(func.count()).select_from(BudgetEntry).where(BudgetEntry.budget_id == budget_id)) or 0
    if entry_count:
        raise HTTPException(
            status_code=409,
            detail="This budget has financial entries and cannot be deleted. Preserve the audit trail instead.",
        )
    await db.delete(budget)
    await db.commit()
    return {"message": f"Budget {budget_id} supprime avec succes"}


# ── Operational project lifecycle ────────────────────────────────────

async def _project_or_404(db: AsyncSession, project_id: str) -> ProjetModel:
    project = await db.get(ProjetModel, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return project


async def _enqueue_mis_event(db: AsyncSession, event_type: str, payload: dict) -> None:
    from agents.mis.agent import mis_agent
    await enqueue_event(db, "events", Event(
        id=str(uuid4()), type=event_type, source_agent=mis_agent.name, payload=payload,
    ))


@router.get("/projets/{project_id}/milestones", response_model=list[MilestoneResponse])
async def list_milestones(project_id: str, db: AsyncSession = Depends(get_db)):
    await _project_or_404(db, project_id)
    return (await db.execute(
        select(ProjectMilestone).where(ProjectMilestone.project_id == project_id).order_by(ProjectMilestone.due_date)
    )).scalars().all()


@router.post("/projets/{project_id}/milestones", response_model=MilestoneResponse, dependencies=_WRITE_GUARD)
async def create_milestone(project_id: str, data: MilestoneCreate, db: AsyncSession = Depends(get_db)):
    await _project_or_404(db, project_id)
    milestone = ProjectMilestone(project_id=project_id, **data.model_dump())
    db.add(milestone)
    await db.flush()
    await _enqueue_mis_event(db, "mis.milestone_created", {"project_id": project_id, "milestone_id": milestone.id, "title": milestone.title, "due_date": milestone.due_date.isoformat()})
    await db.commit()
    await db.refresh(milestone)
    outbox_dispatcher.notify()
    return milestone


@router.patch("/milestones/{milestone_id}", response_model=MilestoneResponse, dependencies=_WRITE_GUARD)
async def update_milestone(milestone_id: str, data: MilestoneUpdate, db: AsyncSession = Depends(get_db)):
    milestone = await db.get(ProjectMilestone, milestone_id)
    if milestone is None:
        raise HTTPException(status_code=404, detail="Milestone introuvable")
    changes = data.model_dump(exclude_unset=True)
    _reject_null_fields(changes, {"title", "due_date", "status"})
    for key, value in changes.items():
        setattr(milestone, key, value)
    if data.status == "completed" and milestone.completed_at is None:
        milestone.completed_at = datetime.utcnow()
    if data.status and data.status != "completed":
        milestone.completed_at = None
    await _enqueue_mis_event(db, "mis.milestone_updated", {"project_id": milestone.project_id, "milestone_id": milestone.id, "status": milestone.status})
    await db.commit()
    await db.refresh(milestone)
    outbox_dispatcher.notify()
    return milestone


@router.get("/projets/{project_id}/deliverables", response_model=list[DeliverableResponse])
async def list_deliverables(project_id: str, db: AsyncSession = Depends(get_db)):
    await _project_or_404(db, project_id)
    return (await db.execute(
        select(ProjectDeliverable).where(ProjectDeliverable.project_id == project_id).order_by(ProjectDeliverable.due_date)
    )).scalars().all()


@router.post("/projets/{project_id}/deliverables", response_model=DeliverableResponse, dependencies=_WRITE_GUARD)
async def create_deliverable(project_id: str, data: DeliverableCreate, db: AsyncSession = Depends(get_db)):
    await _project_or_404(db, project_id)
    deliverable = ProjectDeliverable(project_id=project_id, **data.model_dump())
    db.add(deliverable)
    await db.flush()
    await _enqueue_mis_event(db, "mis.deliverable_created", {"project_id": project_id, "deliverable_id": deliverable.id, "title": deliverable.title})
    await db.commit()
    await db.refresh(deliverable)
    outbox_dispatcher.notify()
    return deliverable


@router.patch("/deliverables/{deliverable_id}", response_model=DeliverableResponse, dependencies=_WRITE_GUARD)
async def update_deliverable(deliverable_id: str, data: DeliverableUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("researcher", "reviewer", "administrator"))):
    deliverable = await db.get(ProjectDeliverable, deliverable_id)
    if deliverable is None:
        raise HTTPException(status_code=404, detail="Deliverable introuvable")
    if data.status == "approved":
        if user.role not in {"reviewer", "administrator"}:
            raise HTTPException(403, "A reviewer must approve deliverables.")
        if deliverable.status not in {"submitted", "approved"}:
            raise HTTPException(409, "Submit the deliverable before approval.")
    changes = data.model_dump(exclude_unset=True)
    if deliverable.status == "approved" and any(key != "status" for key in changes):
        changes["status"] = "draft"
    _reject_null_fields(changes, {"title", "deliverable_type", "status"})
    for key, value in changes.items():
        setattr(deliverable, key, value)
    if deliverable.status in {"planned", "draft"}:
        deliverable.submitted_at = None
    if deliverable.status in {"submitted", "approved"} and deliverable.submitted_at is None:
        deliverable.submitted_at = datetime.utcnow()
    await _enqueue_mis_event(db, "mis.deliverable_updated", {"project_id": deliverable.project_id, "deliverable_id": deliverable.id, "status": deliverable.status})
    await db.commit()
    await db.refresh(deliverable)
    outbox_dispatcher.notify()
    return deliverable


@router.get("/projets/{project_id}/risks", response_model=list[RiskResponse])
async def list_risks(project_id: str, db: AsyncSession = Depends(get_db)):
    await _project_or_404(db, project_id)
    return (await db.execute(
        select(ProjectRisk).where(ProjectRisk.project_id == project_id).order_by(ProjectRisk.impact.desc(), ProjectRisk.likelihood.desc())
    )).scalars().all()


@router.post("/projets/{project_id}/risks", response_model=RiskResponse, dependencies=_WRITE_GUARD)
async def create_risk(project_id: str, data: RiskCreate, db: AsyncSession = Depends(get_db)):
    await _project_or_404(db, project_id)
    risk = ProjectRisk(project_id=project_id, **data.model_dump())
    db.add(risk)
    await db.flush()
    await _enqueue_mis_event(db, "mis.risk_registered", {"project_id": project_id, "risk_id": risk.id, "title": risk.title, "score": risk.likelihood * risk.impact})
    await db.commit()
    await db.refresh(risk)
    outbox_dispatcher.notify()
    return risk


@router.patch("/risks/{risk_id}", response_model=RiskResponse, dependencies=_WRITE_GUARD)
async def update_risk(risk_id: str, data: RiskUpdate, db: AsyncSession = Depends(get_db)):
    risk = await db.get(ProjectRisk, risk_id)
    if risk is None:
        raise HTTPException(status_code=404, detail="Risque introuvable")
    changes = data.model_dump(exclude_unset=True)
    _reject_null_fields(changes, {"title", "likelihood", "impact", "status"})
    for key, value in changes.items():
        setattr(risk, key, value)
    await _enqueue_mis_event(db, "mis.risk_updated", {"project_id": risk.project_id, "risk_id": risk.id, "status": risk.status, "score": risk.likelihood * risk.impact})
    await db.commit()
    await db.refresh(risk)
    outbox_dispatcher.notify()
    return risk


async def _budget_summary(db: AsyncSession, budget: BudgetModel) -> BudgetSummary:
    commitments = await db.scalar(select(func.coalesce(func.sum(BudgetEntry.amount), 0.0)).where(
        BudgetEntry.budget_id == budget.id, BudgetEntry.entry_type == "commitment",
    ))
    spent = float(budget.montant_depense or 0.0)
    committed = float(commitments or 0.0)
    return BudgetSummary(
        budget_id=budget.id, project_id=budget.projet_id, currency=budget.devise,
        allocated=float(budget.montant_alloue), spent=spent, committed=committed,
        available_after_commitments=float(budget.montant_alloue) - spent - committed,
    )


@router.get("/budgets/{budget_id}/entries", response_model=list[BudgetEntryResponse])
async def list_budget_entries(budget_id: str, db: AsyncSession = Depends(get_db)):
    if await db.get(BudgetModel, budget_id) is None:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    return (await db.execute(
        select(BudgetEntry).where(BudgetEntry.budget_id == budget_id).order_by(BudgetEntry.occurred_at.desc(), BudgetEntry.created_at.desc())
    )).scalars().all()


@router.post("/budgets/entries", response_model=BudgetEntryResponse, dependencies=_WRITE_GUARD)
async def create_budget_entry(data: BudgetEntryCreate, db: AsyncSession = Depends(get_db)):
    budget = await db.get(BudgetModel, data.budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    entry = BudgetEntry(project_id=budget.projet_id, currency=budget.devise, **data.model_dump())
    db.add(entry)
    if data.entry_type == "expense":
        await db.execute(update(BudgetModel).where(BudgetModel.id == budget.id).values(
            montant_depense=BudgetModel.montant_depense + data.amount
        ).execution_options(synchronize_session=False))
        await db.refresh(budget)
    await db.flush()
    summary = await _budget_summary(db, budget)
    await _enqueue_mis_event(db, "budget.depense" if data.entry_type == "expense" else "mis.budget_commitment", {
        **summary.model_dump(mode="json"), "entry_id": entry.id, "entry_type": entry.entry_type,
    })
    await db.commit()
    await db.refresh(entry)
    outbox_dispatcher.notify()
    return entry


@router.get("/budgets/{budget_id}/summary", response_model=BudgetSummary)
async def get_budget_summary(budget_id: str, db: AsyncSession = Depends(get_db)):
    budget = await db.get(BudgetModel, budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget introuvable")
    return await _budget_summary(db, budget)


@router.get("/reservations", response_model=list[ReservationResponse])
async def list_reservations(equipment_id: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(EquipmentReservation).order_by(EquipmentReservation.start_at)
    if equipment_id:
        query = query.where(EquipmentReservation.equipment_id == equipment_id)
    return (await db.execute(query)).scalars().all()


@router.post("/reservations", response_model=ReservationResponse, dependencies=_WRITE_GUARD)
async def create_reservation(
    data: ReservationCreate, user: User = Depends(require_roles("researcher", "reviewer", "administrator")), db: AsyncSession = Depends(get_db),
):
    if data.end_at <= data.start_at:
        raise HTTPException(status_code=422, detail="Reservation end must be after its start")
    equipment = await db.get(EquipementModel, data.equipment_id)
    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipement introuvable")
    if equipment.etat != "operationnel":
        raise HTTPException(status_code=409, detail="Equipment is not operational and cannot be reserved")
    if data.project_id:
        await _project_or_404(db, data.project_id)
    conflict = await db.scalar(select(EquipmentReservation.id).where(
        EquipmentReservation.equipment_id == data.equipment_id,
        EquipmentReservation.status == "approved",
        EquipmentReservation.start_at < data.end_at,
        EquipmentReservation.end_at > data.start_at,
    ))
    if conflict:
        raise HTTPException(status_code=409, detail="This equipment is already approved for an overlapping reservation")
    reservation = EquipmentReservation(requester_id=user.email or user.id, **data.model_dump())
    db.add(reservation)
    await db.flush()
    await _enqueue_mis_event(db, "mis.reservation_requested", {"reservation_id": reservation.id, "equipment_id": reservation.equipment_id, "project_id": reservation.project_id})
    await db.commit()
    await db.refresh(reservation)
    outbox_dispatcher.notify()
    return reservation


@router.post("/reservations/{reservation_id}/approve", response_model=ReservationResponse)
async def approve_reservation(
    reservation_id: str, user: User = Depends(require_roles("reviewer", "administrator")), db: AsyncSession = Depends(get_db),
):
    reservation = await db.get(EquipmentReservation, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation introuvable")
    if reservation.status != "requested":
        raise HTTPException(status_code=409, detail="Reservation has already been decided")
    conflict = await db.scalar(select(EquipmentReservation.id).where(
        EquipmentReservation.equipment_id == reservation.equipment_id,
        EquipmentReservation.status == "approved",
        EquipmentReservation.start_at < reservation.end_at,
        EquipmentReservation.end_at > reservation.start_at,
    ))
    if conflict:
        raise HTTPException(status_code=409, detail="Another reservation was approved for this time window")
    reservation.status = "approved"
    reservation.approved_by = user.email or user.id
    reservation.approved_at = datetime.utcnow()
    await _enqueue_mis_event(db, "mis.reservation_approved", {"reservation_id": reservation.id, "equipment_id": reservation.equipment_id, "project_id": reservation.project_id})
    await db.commit()
    await db.refresh(reservation)
    outbox_dispatcher.notify()
    return reservation


@router.get("/maintenance", response_model=list[MaintenanceResponse])
async def list_maintenance(equipment_id: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(EquipmentMaintenance).order_by(EquipmentMaintenance.due_date)
    if equipment_id:
        query = query.where(EquipmentMaintenance.equipment_id == equipment_id)
    return (await db.execute(query)).scalars().all()


@router.post("/maintenance", response_model=MaintenanceResponse, dependencies=_WRITE_GUARD)
async def create_maintenance(data: MaintenanceCreate, db: AsyncSession = Depends(get_db)):
    if await db.get(EquipementModel, data.equipment_id) is None:
        raise HTTPException(status_code=404, detail="Equipement introuvable")
    maintenance = EquipmentMaintenance(**data.model_dump())
    db.add(maintenance)
    await db.flush()
    await _enqueue_mis_event(db, "mis.maintenance_scheduled", {"maintenance_id": maintenance.id, "equipment_id": maintenance.equipment_id, "due_date": maintenance.due_date.isoformat()})
    await db.commit()
    await db.refresh(maintenance)
    outbox_dispatcher.notify()
    return maintenance


@router.patch("/maintenance/{maintenance_id}", response_model=MaintenanceResponse, dependencies=_WRITE_GUARD)
async def update_maintenance(
    maintenance_id: str, data: MaintenanceUpdate,
    user: User = Depends(require_roles("researcher", "reviewer", "administrator")), db: AsyncSession = Depends(get_db),
):
    maintenance = await db.get(EquipmentMaintenance, maintenance_id)
    if maintenance is None:
        raise HTTPException(status_code=404, detail="Maintenance introuvable")
    maintenance.status = data.status
    if data.notes is not None:
        maintenance.notes = data.notes
    if data.status == "completed":
        maintenance.performed_at = datetime.utcnow()
        maintenance.performed_by = user.email or user.id
    await _enqueue_mis_event(db, "mis.maintenance_updated", {"maintenance_id": maintenance.id, "equipment_id": maintenance.equipment_id, "status": maintenance.status})
    await db.commit()
    await db.refresh(maintenance)
    outbox_dispatcher.notify()
    return maintenance


async def _workload_rows(db: AsyncSession, days: int, weekly_capacity_hours: float) -> list[WorkloadResponse]:
    from agents.orchestrateur.models import PlanningTaskDB
    start = date.today()
    end = start + timedelta(days=days)
    capacity = weekly_capacity_hours * (days / 7)
    personnel = (await db.execute(select(PersonnelModel))).scalars().all()
    tasks = (await db.execute(select(PlanningTaskDB).where(PlanningTaskDB.status != "completed"))).scalars().all()
    rows: list[WorkloadResponse] = []
    for person in personnel:
        assigned = [task for task in tasks if task.assigned_personnel_id == person.id]
        planned = [task for task in assigned if task.scheduled_start and start <= task.scheduled_start.date() <= end]
        unscheduled = [task for task in assigned if task.scheduled_start is None]
        scheduled_hours = round(sum(task.duration_hours for task in planned), 2)
        unscheduled_hours = round(sum(task.duration_hours for task in unscheduled), 2)
        rows.append(WorkloadResponse(
            personnel_id=person.id, personnel_name=f"{person.prenom} {person.nom}",
            horizon_start=start, horizon_end=end, scheduled_hours=scheduled_hours,
            unscheduled_assigned_hours=unscheduled_hours, task_count=len(assigned),
            capacity_hours=round(capacity, 2), overloaded=scheduled_hours > capacity,
        ))
    return rows


@router.get("/workload", response_model=list[WorkloadResponse])
async def get_workload(days: int = 7, weekly_capacity_hours: float = 40.0, db: AsyncSession = Depends(get_db)):
    if days < 1 or days > 90 or weekly_capacity_hours <= 0 or weekly_capacity_hours > 168:
        raise HTTPException(status_code=422, detail="days must be 1..90 and weekly capacity 0..168")
    return await _workload_rows(db, days, weekly_capacity_hours)


@router.get("/operational-alerts", response_model=list[OperationalAlert])
async def get_operational_alerts(db: AsyncSession = Depends(get_db)):
    """Derive current, explainable lab warnings from persisted operational data."""
    today = date.today()
    soon = today + timedelta(days=7)
    alerts: list[OperationalAlert] = []
    milestones = (await db.execute(select(ProjectMilestone).where(ProjectMilestone.status != "completed"))).scalars().all()
    for milestone in milestones:
        if milestone.due_date < today:
            alerts.append(OperationalAlert(level="critical", category="deadline", entity_type="milestone", entity_id=milestone.id, project_id=milestone.project_id, message=f"Milestone '{milestone.title}' is overdue since {milestone.due_date}."))
        elif milestone.due_date <= soon:
            alerts.append(OperationalAlert(level="warning", category="deadline", entity_type="milestone", entity_id=milestone.id, project_id=milestone.project_id, message=f"Milestone '{milestone.title}' is due on {milestone.due_date}."))
    deliverables = (await db.execute(select(ProjectDeliverable).where(ProjectDeliverable.status != "approved"))).scalars().all()
    for deliverable in deliverables:
        if deliverable.due_date and deliverable.due_date < today:
            alerts.append(OperationalAlert(level="critical", category="deadline", entity_type="deliverable", entity_id=deliverable.id, project_id=deliverable.project_id, message=f"Deliverable '{deliverable.title}' is overdue since {deliverable.due_date}."))
    risks = (await db.execute(select(ProjectRisk).where(ProjectRisk.status == "open"))).scalars().all()
    for risk in risks:
        score = risk.likelihood * risk.impact
        if score >= 15:
            alerts.append(OperationalAlert(level="critical" if score >= 20 else "warning", category="risk", entity_type="risk", entity_id=risk.id, project_id=risk.project_id, message=f"Open risk '{risk.title}' scores {score}/25 (likelihood {risk.likelihood} × impact {risk.impact})."))
    budgets = (await db.execute(select(BudgetModel))).scalars().all()
    for budget in budgets:
        summary = await _budget_summary(db, budget)
        ratio = (summary.spent + summary.committed) / summary.allocated if summary.allocated else 0
        if summary.allocated and ratio >= 0.8:
            alerts.append(OperationalAlert(level="critical" if ratio >= 1 else "warning", category="budget", entity_type="budget", entity_id=budget.id, project_id=budget.projet_id, message=f"Budget pressure is {ratio * 100:.0f}% including commitments ({summary.spent:.2f} spent + {summary.committed:.2f} committed of {summary.allocated:.2f} {summary.currency})."))
    maintenance = (await db.execute(
        select(EquipmentMaintenance).where(EquipmentMaintenance.status.not_in(["completed", "cancelled"]))
    )).scalars().all()
    for item in maintenance:
        if item.due_date <= soon:
            alerts.append(OperationalAlert(level="critical" if item.due_date < today else "warning", category="maintenance", entity_type="maintenance", entity_id=item.id, message=f"{item.maintenance_type.title()} for equipment {item.equipment_id} is {'overdue' if item.due_date < today else 'due'} on {item.due_date}."))
    for workload in await _workload_rows(db, 7, 40):
        if workload.overloaded:
            alerts.append(OperationalAlert(level="warning", category="workload", entity_type="personnel", entity_id=workload.personnel_id, message=f"{workload.personnel_name} has {workload.scheduled_hours:.1f} planned hours this week, above the {workload.capacity_hours:.1f}-hour capacity."))
    order = {"critical": 0, "warning": 1, "info": 2}
    return sorted(alerts, key=lambda alert: (order[alert.level], alert.category, alert.message))


@router.get("/projets/{project_id}/monthly-report", response_model=MonthlyProjectReport)
async def get_monthly_project_report(project_id: str, month: str | None = None, db: AsyncSession = Depends(get_db)):
    """Return an auditable month snapshot; no hidden scoring or fabricated narrative."""
    project = await _project_or_404(db, project_id)
    if month is None:
        report_month = date.today().replace(day=1)
    else:
        try:
            report_month = datetime.strptime(month, "%Y-%m").date().replace(day=1)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="month must use YYYY-MM") from exc
    next_month = (report_month.replace(day=28) + timedelta(days=4)).replace(day=1)

    milestones = (await db.execute(select(ProjectMilestone).where(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.due_date >= report_month,
        ProjectMilestone.due_date < next_month,
    ))).scalars().all()
    deliverables = (await db.execute(select(ProjectDeliverable).where(
        ProjectDeliverable.project_id == project_id,
        ProjectDeliverable.due_date >= report_month,
        ProjectDeliverable.due_date < next_month,
    ))).scalars().all()
    risks = (await db.execute(select(ProjectRisk).where(
        ProjectRisk.project_id == project_id,
        ProjectRisk.status == "open",
    ))).scalars().all()
    expenses = await db.scalar(select(func.coalesce(func.sum(BudgetEntry.amount), 0.0)).where(
        BudgetEntry.project_id == project_id,
        BudgetEntry.entry_type == "expense",
        BudgetEntry.occurred_at >= report_month,
        BudgetEntry.occurred_at < next_month,
    ))
    commitments = await db.scalar(select(func.coalesce(func.sum(BudgetEntry.amount), 0.0)).where(
        BudgetEntry.project_id == project_id,
        BudgetEntry.entry_type == "commitment",
        BudgetEntry.occurred_at >= report_month,
        BudgetEntry.occurred_at < next_month,
    ))
    from agents.orchestrateur.models import PlanningTaskDB
    tasks = (await db.execute(select(PlanningTaskDB).where(
        PlanningTaskDB.project_id == project_id,
        PlanningTaskDB.scheduled_start >= datetime.combine(report_month, datetime.min.time()),
        PlanningTaskDB.scheduled_start < datetime.combine(next_month, datetime.min.time()),
    ))).scalars().all()
    high_risks = [risk for risk in risks if risk.likelihood * risk.impact >= 15]
    highlights: list[str] = []
    if high_risks:
        highlights.append(f"{len(high_risks)} open high-priority risk(s) require review.")
    if expenses or commitments:
        highlights.append(f"{float(expenses or 0):.2f} expenses and {float(commitments or 0):.2f} commitments recorded this month.")
    if not highlights:
        highlights.append("No financial activity or high-priority risks were recorded for this month.")
    return MonthlyProjectReport(
        project_id=project.id,
        project_name=project.nom,
        month=report_month.strftime("%Y-%m"),
        generated_at=datetime.utcnow(),
        milestone_total=len(milestones),
        milestones_completed=sum(item.status == "completed" for item in milestones),
        deliverable_total=len(deliverables),
        deliverables_approved=sum(item.status == "approved" for item in deliverables),
        open_risk_count=len(risks),
        high_risk_count=len(high_risks),
        expense_total=float(expenses or 0),
        commitment_total=float(commitments or 0),
        planned_task_count=len(tasks),
        planned_task_hours=round(sum(float(task.duration_hours or 0) for task in tasks), 2),
        highlights=highlights,
    )


@router.get("/projets/{project_id}/completion-report")
async def completion_report(project_id: str, db: AsyncSession = Depends(get_db)):
    """Current project-wide evidence, not a frozen historical approval."""
    project = await _project_or_404(db, project_id)
    milestones = await list_milestones(project_id, db)
    deliverables = await list_deliverables(project_id, db)
    risks = await list_risks(project_id, db)
    budgets = (await db.execute(select(BudgetModel).where(BudgetModel.projet_id == project_id))).scalars().all()
    staff = (await db.execute(select(PersonnelModel).where(PersonnelModel.projet_actuel_id == project_id))).scalars().all()
    entries = (await db.execute(select(BudgetEntry).where(BudgetEntry.project_id == project_id).order_by(BudgetEntry.occurred_at))).scalars().all()
    outstanding = []
    if not milestones: outstanding.append("No milestones recorded.")
    if not deliverables: outstanding.append("No deliverables recorded.")
    if any(item.status != "completed" for item in milestones): outstanding.append("Some milestones are incomplete.")
    if any(item.status != "approved" for item in deliverables): outstanding.append("Some deliverables are not approved.")
    if any(item.status == "open" for item in risks): outstanding.append("Open risks need review.")
    finance = []
    for budget in budgets:
        committed = sum(item.amount for item in entries if item.budget_id == budget.id and item.entry_type == "commitment")
        finance.append(dict(budget_id=budget.id, currency=budget.devise, allocated=budget.montant_alloue,
                            spent=budget.montant_depense, committed=committed,
                            available=budget.montant_alloue-budget.montant_depense-committed))
    if any(item["available"] < 0 for item in finance): outstanding.append("A budget exceeds its allocation after commitments.")
    return dict(project=ProjetSchema.model_validate(project.__dict__).model_dump(mode="json"),
                generated_at=datetime.utcnow().isoformat(), report_type="current project-wide snapshot",
                outstanding=outstanding,
                milestones=[MilestoneResponse.model_validate(item).model_dump(mode="json") for item in milestones],
                deliverables=[DeliverableResponse.model_validate(item).model_dump(mode="json") for item in deliverables],
                risks=[RiskResponse.model_validate(item).model_dump(mode="json") for item in risks],
                staff=[dict(id=item.id, name=f"{item.prenom} {item.nom}", role=item.role) for item in staff],
                budgets=finance,
                entries=[BudgetEntryResponse.model_validate(item).model_dump(mode="json") for item in entries])
