from __future__ import annotations
from datetime import date, datetime
from uuid import uuid4
from sqlalchemy import String, Float, Boolean, DateTime, Integer, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from shared.database import Base


class Projet(Base):
    __tablename__ = "projets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    nom: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    statut: Mapped[str] = mapped_column(String, default="planifie", nullable=False)
    date_debut: Mapped[date] = mapped_column(nullable=False)
    date_fin_prevue: Mapped[date | None] = mapped_column(nullable=True)
    budget_alloue: Mapped[float] = mapped_column(Float, default=0.0)
    responsable: Mapped[str] = mapped_column(String, nullable=False)


class ProjectDossier(Base):
    __tablename__ = "mis_project_dossiers"
    project_id: Mapped[str] = mapped_column(ForeignKey("projets.id", ondelete="CASCADE"), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    questions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    approach: Mapped[str] = mapped_column(Text, nullable=False, default="")
    findings: Mapped[str] = mapped_column(Text, nullable=False, default="")
    limitations: Mapped[str] = mapped_column(Text, nullable=False, default="")
    references: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    claims: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    evaluations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    updated_by: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class DossierSubmission(Base):
    __tablename__ = "mis_dossier_submissions"
    __table_args__ = (UniqueConstraint("project_id", "revision", name="uq_submission_project_revision"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    digest: Mapped[str] = mapped_column(String, nullable=False)
    submitted_by: Mapped[str] = mapped_column(String, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    reviewed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)


class Personnel(Base):
    __tablename__ = "personnels"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    nom: Mapped[str] = mapped_column(String, nullable=False)
    prenom: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    competences: Mapped[str] = mapped_column(String, default="", nullable=False)
    disponible: Mapped[bool] = mapped_column(Boolean, default=True)
    projet_actuel_id: Mapped[str | None] = mapped_column(String, nullable=True)


class Equipement(Base):
    __tablename__ = "equipements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    nom: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    etat: Mapped[str] = mapped_column(String, nullable=False)
    localisation: Mapped[str] = mapped_column(String, nullable=False)
    responsable_id: Mapped[str | None] = mapped_column(String, nullable=True)
    date_acquisition: Mapped[date | None] = mapped_column(nullable=True)
    valeur_estimee: Mapped[float] = mapped_column(Float, default=0.0)


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    projet_id: Mapped[str] = mapped_column(String, nullable=False)
    montant_alloue: Mapped[float] = mapped_column(Float, nullable=False)
    montant_depense: Mapped[float] = mapped_column(Float, default=0.0)
    devise: Mapped[str] = mapped_column(String, default="EUR", nullable=False)
    date_debut: Mapped[date] = mapped_column(nullable=False)
    date_fin: Mapped[date | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)


class ProjectMilestone(Base):
    """A dated, accountable checkpoint for a laboratory project."""
    __tablename__ = "mis_project_milestones"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    due_date: Mapped[date] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending", index=True)
    owner_id: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ProjectDeliverable(Base):
    """A concrete project output: dataset, report, protocol, paper, etc."""
    __tablename__ = "mis_project_deliverables"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    deliverable_type: Mapped[str] = mapped_column(String, nullable=False, default="report")
    due_date: Mapped[date | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="planned", index=True)
    owner_id: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ProjectRisk(Base):
    """A human-owned risk register entry with explicit likelihood and impact."""
    __tablename__ = "mis_project_risks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    likelihood: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    impact: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open", index=True)
    owner_id: Mapped[str | None] = mapped_column(String, nullable=True)
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BudgetEntry(Base):
    """Budget line, commitment, or actual expense; records are append-only."""
    __tablename__ = "mis_budget_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    budget_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    entry_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String, nullable=False, default="general")
    description: Mapped[str] = mapped_column(String, nullable=False)
    vendor: Mapped[str | None] = mapped_column(String, nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False, default="EUR")
    occurred_at: Mapped[date] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class EquipmentReservation(Base):
    """A reviewer-approved reservation prevents double-booking a shared instrument."""
    __tablename__ = "mis_equipment_reservations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    equipment_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    project_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    requester_id: Mapped[str] = mapped_column(String, nullable=False)
    purpose: Mapped[str] = mapped_column(String, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="requested", index=True)
    approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class EquipmentMaintenance(Base):
    """Scheduled or corrective maintenance, kept separate from equipment state."""
    __tablename__ = "mis_equipment_maintenance"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    equipment_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    maintenance_type: Mapped[str] = mapped_column(String, nullable=False, default="calibration")
    due_date: Mapped[date] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="scheduled", index=True)
    performed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    performed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
