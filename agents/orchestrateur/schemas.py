from __future__ import annotations
from datetime import date, datetime
from typing import Any, Literal
from uuid import uuid4
from pydantic import BaseModel, Field

NiveauAlerte = Literal["info", "orange", "rouge", "critique"]


class Alerte(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    niveau: NiveauAlerte
    message: str
    source_evenement: str
    context: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolue: bool = False


class HistoriqueEvenement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type_evenement: str
    source_agent: str
    payload: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    traite: bool = True
    alertes_generees: list[str] = Field(default_factory=list)


class DecisionRoutageIA(BaseModel):
    """AI-powered routing decision for unmatched events (from Friend 2)."""
    type_evenement: str
    agent_ou_action_recommande: str
    niveau_urgence: NiveauAlerte
    justification: str
    necessite_intervention_humaine: bool


TaskPriority = Literal["low", "normal", "high", "critical"]
TaskStatus = Literal["pending", "planned", "in_progress", "completed"]
ProposalStatus = Literal["proposed", "approved", "discarded"]


class PlanningTaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    project_id: str | None = None
    priority: TaskPriority = "normal"
    due_date: date | None = None
    duration_hours: float = Field(default=1.0, gt=0, le=80)
    required_skills: list[str] = Field(default_factory=list)
    required_equipment_ids: list[str] = Field(default_factory=list)


class PlanningTaskResponse(PlanningTaskCreate):
    id: str
    status: TaskStatus
    assigned_personnel_id: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class PlanningProposalResponse(BaseModel):
    id: str
    status: ProposalStatus
    proposed_assignments: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]
    created_at: datetime
    approved_at: datetime | None = None
    approved_by: str | None = None

    model_config = {"from_attributes": True}
