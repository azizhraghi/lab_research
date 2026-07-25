from __future__ import annotations
from datetime import date
from uuid import uuid4
from sqlalchemy import String, Float, Boolean, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


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