# -*- coding: utf-8 -*-
from __future__ import annotations
from pydantic import BaseModel, Field          # pydantic for data validation
from typing import Optional, List              # type hints
from datetime import datetime, timezone        # for timestamps
from uuid import uuid4                         # for unique IDs

class Publication(BaseModel):
    """represents a single publication linked to a researcher"""
    id: str                                    # paper ID (arxiv:xxx or pubmed:xxx)
    title: str                                 # paper title
    topic: str                                 # classified topic
    source: str                                # arxiv or pubmed
    discovered_at: datetime = Field(           # when veille agent found it
        default_factory=lambda: datetime.now(timezone.utc)
    )

class Researcher(BaseModel):
    """represents a lab researcher with their profile and metrics"""
    id: str = Field(                           # unique ID auto-generated
        default_factory=lambda: str(uuid4())
    )
    name: str                                  # full name e.g. "Ahmed Ben Ali"
    email: Optional[str] = None               # lab email
    orcid: Optional[str] = None               # ORCID identifier if available
    google_scholar_id: Optional[str] = None   # Google Scholar profile ID if available
    publications: List[Publication] = []       # list of their known publications
    h_index: Optional[int] = None             # h-index computed from Scholar
    citation_count: Optional[int] = None      # total citations
    topics: List[str] = []                    # research topics derived from publications
    last_updated: datetime = Field(            # when profile was last refreshed
        default_factory=lambda: datetime.now(timezone.utc)
    )

class ResearcherCreate(BaseModel):
    """schema for creating a new researcher — only required fields"""
    name: str                                  # only name is required to create a researcher
    email: Optional[str] = None
    orcid: Optional[str] = None
    google_scholar_id: Optional[str] = None