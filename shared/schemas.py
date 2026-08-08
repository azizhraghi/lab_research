from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, Optional, List
from enum import Enum

class EventType(str, Enum):
    # Veille
    ARTICLE_COLLECTED = "veille.article_collected"
    ARTICLE_TROUVE = "veille.article_trouve"
    RESUME_GENERE = "veille.resume_genere"
    # Bibliométrie
    PUBLICATION_SYNCED = "biblio.publication_synced"
    PROFIL_MIS_A_JOUR = "bibliometrie.profil_mis_a_jour"
    CV_GENERE = "bibliometrie.cv_genere"
    # Simulation
    SIMULATION_COMPLETED = "sim.completed"
    SIMULATION_TERMINEE = "simulation.terminee"
    SIMULATION_CALIBRATION_OK = "simulation.calibration_ok"
    # Optimisation
    OPTIMIZATION_COMPLETED = "opt.completed"
    STRATEGIE_CALCULEE = "optimisation.strategie_calculee"
    CONTRAINTE_VIOLEE = "optimisation.contrainte_violee"
    # Qualité
    DATA_VALIDATION_FAILED = "qual.validation_failed"
    QUALITE_ANOMALIE = "qualite.anomalie_detectee"
    QUALITE_VALIDATION_OK = "qualite.validation_ok"
    QUALITE_VALIDATION_DEMANDEE = "qualite.validation_demandee"
    # Orchestrateur
    TASK_ASSIGNED = "orch.task_assigned"
    ACTION_PROPOSED = "orch.action_proposed"
    # MIS
    PROJET_CREATED = "projet.created"
    PROJET_STATUT_CHANGE = "projet.statut_change"
    BUDGET_DEPENSE = "budget.depense"
    EQUIPEMENT_ETAT_CHANGE = "equipement.etat_change"
    PERSONNEL_INDISPONIBLE = "personnel.indisponible"

class Event(BaseModel):
    id: str
    # `type` is intentionally a plain `str`, not the `EventType` enum. Agents emit
    # and subscribe using dotted event strings (e.g. "veille.article_collected"),
    # and `POST /api/orchestrateur/trigger` forwards arbitrary caller-supplied
    # types. The `EventType` enum above is the canonical list of known values —
    # used as constants/reference, not as a validation gate. Constraining to the
    # enum here would reject every real-world event and block bus wiring.
    type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_agent: str
    payload: Dict[str, Any]

class ActionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"
    REJECTED = "rejected"

class AgentAction(BaseModel):
    id: str
    agent_name: str
    action_type: str
    params: Dict[str, Any]
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class ActionResult(BaseModel):
    action_id: str
    status: ActionStatus
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)

class AuditEntry(BaseModel):
    agent_name: str
    action: str
    entity_type: str
    entity_id: str
    user_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)
