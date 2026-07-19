from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class PublicationBase(BaseModel):
    title: str
    abstract: Optional[str] = None
    doi: Optional[str] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    type: Optional[str] = None
    source: str

class PublicationCreate(PublicationBase):
    pass

class PublicationResponse(PublicationBase):
    id: int
    citation_count: int
    class Config:
        from_attributes = True

class IndicatorResponse(BaseModel):
    metric_name: str
    value: float
    computed_at: datetime
    class Config:
        from_attributes = True

class CVProfileResponse(BaseModel):
    template: str
    custom_sections: List[Dict[str, Any]]
    last_generated: Optional[datetime]
    class Config:
        from_attributes = True

class ResearcherBase(BaseModel):
    name: str
    email: str
    orcid_id: Optional[str] = None
    scholar_id: Optional[str] = None
    scopus_id: Optional[str] = None
    department: str
    role: str

class ResearcherCreate(ResearcherBase):
    pass

class ResearcherResponse(ResearcherBase):
    id: int
    indicators: List[IndicatorResponse] = []
    cv_profile: Optional[CVProfileResponse] = None
    
    class Config:
        from_attributes = True
