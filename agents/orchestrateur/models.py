"""Persistence for Orchestrateur agent state (alerts + event history).

Previously both lived in in-memory lists on OrchestratorAgent, so every server
restart lost all alerts and the entire routed-event history. These tables mirror
the Alerte / HistoriqueEvenement pydantic schemas (agents/orchestrateur/schemas.py).

History is appended newest-LAST (arrival-ordered); any "recent" view must
reverse before display — this matches the pre-existing frontend convention.
"""
from __future__ import annotations
import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Date, Float, JSON
from shared.database import Base


class AlerteDB(Base):
    __tablename__ = "orch_alertes"

    id = Column(String, primary_key=True, index=True)  # uuid4, matches Alerte
    niveau = Column(String)  # info | orange | rouge | critique
    message = Column(String)
    source_evenement = Column(String, index=True)
    context = Column(JSON, default=dict, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    resolue = Column(Boolean, default=False, index=True)


class HistoriqueEvenementDB(Base):
    __tablename__ = "orch_historique"

    id = Column(String, primary_key=True, index=True)  # uuid4
    type_evenement = Column(String, index=True)
    source_agent = Column(String, index=True)
    payload = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    traite = Column(Boolean, default=True)
    alertes_generees = Column(JSON, default=list)  # list[str] of Alerte ids


class PlanningTaskDB(Base):
    """A lab work item whose assignment is proposed, never auto-applied."""
    __tablename__ = "orch_planning_tasks"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    project_id = Column(String, index=True, nullable=True)
    priority = Column(String, nullable=False, default="normal")
    status = Column(String, nullable=False, default="pending", index=True)
    due_date = Column(Date, nullable=True)
    duration_hours = Column(Float, nullable=False, default=1.0)
    required_skills = Column(JSON, nullable=False, default=list)
    required_equipment_ids = Column(JSON, nullable=False, default=list)
    assigned_personnel_id = Column(String, nullable=True, index=True)
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)


class PlanningProposalDB(Base):
    """Immutable planner output; approval is a separate, auditable decision."""
    __tablename__ = "orch_planning_proposals"

    id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False, default="proposed", index=True)
    proposed_assignments = Column(JSON, nullable=False, default=list)
    conflicts = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)
