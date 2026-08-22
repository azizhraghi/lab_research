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

class OrcidSyncResponse(BaseModel):
    """Outcome of POST /researchers/{id}/publications/sync.

    Counts are reported separately because they answer different questions:
    `works_found` is what ORCID holds, `publications_created` is what was new to
    the lab, and `links_created` is what was new to *this* researcher. A
    co-author's second sync typically shows works_found > 0 with
    publications_created == 0 and links_created > 0 — the paper already existed,
    the authorship did not.
    """
    researcher_id: int
    source: str
    orcid_id: str
    works_found: int
    publications_created: int
    publications_enriched: int
    links_created: int
    links_already_present: int
    # Scholar syncs refresh citation counts on matched rows; ORCID never does.
    citations_updated: int = 0


class ScholarSyncResponse(BaseModel):
    """Outcome of POST /researchers/{id}/publications/sync/scholar.

    Same counting semantics as OrcidSyncResponse, plus `citations_updated` —
    Scholar is the source that refreshes citation counts on matched rows.
    """
    researcher_id: int
    source: str
    scholar_id: str
    works_found: int
    publications_created: int
    publications_enriched: int
    links_created: int
    links_already_present: int
    citations_updated: int = 0


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
