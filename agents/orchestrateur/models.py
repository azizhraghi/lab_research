"""Persistence for Orchestrateur agent state (alerts + event history).

Previously both lived in in-memory lists on OrchestratorAgent, so every server
restart lost all alerts and the entire routed-event history. These tables mirror
the Alerte / HistoriqueEvenement pydantic schemas (agents/orchestrateur/schemas.py).

History is appended newest-LAST (arrival-ordered); any "recent" view must
reverse before display — this matches the pre-existing frontend convention.
"""
from __future__ import annotations
import datetime

from sqlalchemy import Column, String, Boolean, DateTime, JSON
from shared.database import Base


class AlerteDB(Base):
    __tablename__ = "orch_alertes"

    id = Column(String, primary_key=True, index=True)  # uuid4, matches Alerte
    niveau = Column(String)  # info | orange | rouge | critique
    message = Column(String)
    source_evenement = Column(String, index=True)
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
