from __future__ import annotations 
from datetime import datetime , timezone 
from typing import Any , Literal
from uuid import uuid4
from pydantic import BaseModel , Field 

def _utcnow() -> datetime:
    """horodatage UTC , utilise comme val par defaut pour les evenements"""
    return datetime.now(timezone.utc)

class Event(BaseModel):
    """une notification emise par 1 agent sur le bus d'evenements
    exemple: veille --> "article.discovered" --> bibliometrie 
    """

    id: str =Field(default_factory=lambda:str(uuid4()))
    type: str
    source_agent: str
    timestamp: datetime =Field(default_factory=_utcnow)
    correlation_id: str | None = None 
    payload: dict[str , Any]= Field(default_factory=dict)


class AgentAction(BaseModel):
    """ action proposee par un agent (soumise) a validation humaine"""

    agent: str
    action_type: str
    requires_approval: bool
    payload: dict[str , Any]=Field(default_factory=dict)
    status: Literal["proposed","approved","rejected","executed"]="proposed"