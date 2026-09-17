from __future__ import annotations
from datetime import date, datetime
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator

ProjetStatut = Literal["planifie", "en_cours", "termine", "suspendu"]


class ProjetSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    nom: str = Field(min_length=1, max_length=200)
    description: str | None = None
    statut: ProjetStatut = "planifie"
    date_debut: date
    date_fin_prevue: date | None = None
    budget_alloue: float = Field(0.0, ge=0, allow_inf_nan=False)
    responsable: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def date_order(self):
        if self.date_fin_prevue and self.date_fin_prevue < self.date_debut:
            raise ValueError("Planned end must be on or after the start date.")
        return self


RolePersonnel = Literal["chercheur", "ingenieur", "technicien", "administratif", "doctorant"]


class PersonnelSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    nom: str
    prenom: str
    email: str
    role: RolePersonnel
    competences: list[str] = Field(default_factory=list)
    disponible: bool = True
    projet_actuel_id: str | None = None


class EquipementSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    nom: str
    type: str
    etat: Literal["operationnel", "en_maintenance", "indisponible"]
    localisation: str
    responsable_id: str | None = None
    date_acquisition: date | None = None
    valeur_estimee: float = Field(0.0, ge=0, allow_inf_nan=False)


class BudgetSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    projet_id: str
    montant_alloue: float = Field(ge=0, allow_inf_nan=False)
    montant_depense: float = Field(0.0, ge=0, allow_inf_nan=False)
    devise: str = "EUR"
    date_debut: date
    date_fin: date | None = None
    description: str | None = None

    @model_validator(mode="after")
    def date_order(self):
        if self.date_fin and self.date_fin < self.date_debut:
            raise ValueError("Budget end must be on or after the start date.")
        return self


MilestoneStatus = Literal["pending", "at_risk", "completed"]
DeliverableStatus = Literal["planned", "draft", "submitted", "approved"]
RiskStatus = Literal["open", "mitigated", "closed"]
BudgetEntryType = Literal["line", "commitment", "expense"]
ReservationStatus = Literal["requested", "approved", "cancelled"]
MaintenanceStatus = Literal["scheduled", "in_progress", "completed", "cancelled"]


class MilestoneCreate(BaseModel):
    model_config = {"extra": "forbid", "str_strip_whitespace": True}
    title: str = Field(min_length=3, max_length=180)
    due_date: date
    owner_id: str | None = None
    notes: str | None = Field(None, max_length=2000)


class MilestoneUpdate(BaseModel):
    model_config = {"extra": "forbid", "str_strip_whitespace": True}
    title: str | None = Field(None, min_length=3, max_length=180)
    due_date: date | None = None
    status: MilestoneStatus | None = None
    owner_id: str | None = None
    notes: str | None = Field(None, max_length=2000)


class MilestoneResponse(MilestoneCreate):
    id: str
    project_id: str
    status: MilestoneStatus
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeliverableCreate(BaseModel):
    model_config = {"extra": "forbid", "str_strip_whitespace": True}
    title: str = Field(min_length=3, max_length=180)
    deliverable_type: str = Field(default="report", min_length=2, max_length=80)
    due_date: date | None = None
    owner_id: str | None = None
    url: str | None = Field(None, max_length=1000)
    notes: str | None = Field(None, max_length=2000)


class DeliverableUpdate(BaseModel):
    model_config = {"extra": "forbid", "str_strip_whitespace": True}
    title: str | None = Field(None, min_length=3, max_length=180)
    deliverable_type: str | None = Field(None, min_length=2, max_length=80)
    due_date: date | None = None
    status: DeliverableStatus | None = None
    owner_id: str | None = None
    url: str | None = Field(None, max_length=1000)
    notes: str | None = Field(None, max_length=2000)


class DeliverableResponse(DeliverableCreate):
    id: str
    project_id: str
    status: DeliverableStatus
    submitted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RiskCreate(BaseModel):
    model_config = {"extra": "forbid", "str_strip_whitespace": True}
    title: str = Field(min_length=3, max_length=180)
    description: str | None = Field(None, max_length=4000)
    likelihood: int = Field(default=3, ge=1, le=5)
    impact: int = Field(default=3, ge=1, le=5)
    owner_id: str | None = None
    mitigation: str | None = Field(None, max_length=4000)


class RiskUpdate(BaseModel):
    model_config = {"extra": "forbid", "str_strip_whitespace": True}
    title: str | None = Field(None, min_length=3, max_length=180)
    description: str | None = Field(None, max_length=4000)
    likelihood: int | None = Field(None, ge=1, le=5)
    impact: int | None = Field(None, ge=1, le=5)
    status: RiskStatus | None = None
    owner_id: str | None = None
    mitigation: str | None = Field(None, max_length=4000)


class RiskResponse(RiskCreate):
    id: str
    project_id: str
    status: RiskStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BudgetEntryCreate(BaseModel):
    budget_id: str
    entry_type: BudgetEntryType
    category: str = Field(default="general", min_length=2, max_length=100)
    description: str = Field(min_length=3, max_length=500)
    vendor: str | None = Field(None, max_length=160)
    amount: float = Field(gt=0, allow_inf_nan=False)
    occurred_at: date


class BudgetEntryResponse(BudgetEntryCreate):
    id: str
    project_id: str
    currency: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BudgetSummary(BaseModel):
    budget_id: str
    project_id: str
    currency: str
    allocated: float
    spent: float
    committed: float
    available_after_commitments: float


class ReservationCreate(BaseModel):
    equipment_id: str
    project_id: str | None = None
    purpose: str = Field(min_length=3, max_length=500)
    start_at: datetime
    end_at: datetime
    notes: str | None = Field(None, max_length=2000)


class ReservationResponse(ReservationCreate):
    id: str
    requester_id: str
    status: ReservationStatus
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MaintenanceCreate(BaseModel):
    equipment_id: str
    maintenance_type: str = Field(default="calibration", min_length=2, max_length=100)
    due_date: date
    notes: str | None = Field(None, max_length=2000)


class MaintenanceUpdate(BaseModel):
    status: MaintenanceStatus
    notes: str | None = Field(None, max_length=2000)


class MaintenanceResponse(MaintenanceCreate):
    id: str
    status: MaintenanceStatus
    performed_at: datetime | None = None
    performed_by: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkloadResponse(BaseModel):
    personnel_id: str
    personnel_name: str
    horizon_start: date
    horizon_end: date
    scheduled_hours: float
    unscheduled_assigned_hours: float
    task_count: int
    capacity_hours: float
    overloaded: bool


class OperationalAlert(BaseModel):
    level: Literal["info", "warning", "critical"]
    category: Literal["deadline", "budget", "risk", "maintenance", "workload"]
    message: str
    entity_type: str
    entity_id: str
    project_id: str | None = None


class MonthlyProjectReport(BaseModel):
    """A transparent, on-demand operational snapshot for a project month.

    Reports are deliberately calculated from the underlying audit records rather
    than generated by an LLM: a researcher can always trace each headline back
    to a milestone, financial entry, risk, or planning task.
    """

    project_id: str
    project_name: str
    month: str
    generated_at: datetime
    milestone_total: int
    milestones_completed: int
    deliverable_total: int
    deliverables_approved: int
    open_risk_count: int
    high_risk_count: int
    expense_total: float
    commitment_total: float
    planned_task_count: int
    planned_task_hours: float
    highlights: list[str]
