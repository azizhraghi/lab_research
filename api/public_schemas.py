from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


Visibility = Literal["hidden", "summary", "full"]
PublicationStatus = Literal["draft", "published", "withdrawn"]
CatalogStatus = Literal["draft", "published", "withdrawn"]


class ResearcherPublicationSettings(BaseModel):
    visibility: Visibility
    consent_confirmed: bool = False
    consent_version: str | None = Field(None, max_length=80)
    public_bio: str | None = Field(None, max_length=3000)


class PublicResearcherResponse(BaseModel):
    id: int
    name: str
    department: str
    role: str
    visibility: Visibility
    public_bio: str | None = None


class PublicPublicationCreate(BaseModel):
    source_publication_id: int
    keywords: list[str] = Field(default_factory=list, max_length=12)
    status: PublicationStatus = "draft"


class PublicPublicationResponse(BaseModel):
    id: str
    source_publication_id: int
    title: str
    abstract: str | None = None
    doi: str | None = None
    journal: str | None = None
    year: int | None = None
    keywords: list[str]
    status: PublicationStatus
    published_at: datetime | None = None

    model_config = {"from_attributes": True}


class PublicProjectCreate(BaseModel):
    project_id: str
    summary: str = Field(min_length=20, max_length=5000)
    research_area: str | None = Field(None, max_length=160)
    status: CatalogStatus = "draft"


class PublicProjectResponse(BaseModel):
    id: str
    project_id: str
    title: str
    summary: str
    research_area: str | None = None
    status: CatalogStatus
    start_date: date | None = None
    end_date: date | None = None
    published_at: datetime | None = None

    model_config = {"from_attributes": True}


class PublicDatasetCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    description: str = Field(min_length=20, max_length=5000)
    version: str = Field(min_length=1, max_length=80)
    license: str = Field(min_length=2, max_length=160)
    access_url: HttpUrl | None = None
    citation: str | None = Field(None, max_length=3000)
    keywords: list[str] = Field(default_factory=list, max_length=12)
    status: CatalogStatus = "draft"


class PublicDatasetResponse(BaseModel):
    id: str
    title: str
    description: str
    version: str
    license: str
    access_url: str | None = None
    citation: str | None = None
    keywords: list[str]
    status: CatalogStatus
    published_at: datetime | None = None

    model_config = {"from_attributes": True}


class PublicationStatusUpdate(BaseModel):
    status: PublicationStatus


class CatalogStatusUpdate(BaseModel):
    status: CatalogStatus


from pydantic import ConfigDict, model_validator

ContentKind = Literal["news", "events", "theses"]

class ContentWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    kind: ContentKind
    title: str = Field(min_length=3, max_length=240)
    body: str = Field(min_length=20, max_length=20000)
    event_date: date | None = None
    end_date: date | None = None
    location: str | None = Field(None, max_length=300)
    author: str | None = Field(None, max_length=160)
    supervisor: str | None = Field(None, max_length=300)
    degree: Literal["PhD", "Masters"] | None = None
    defense_date: date | None = None
    link: HttpUrl | None = None

    @model_validator(mode="after")
    def validate_kind_fields(self):
        if self.kind == "events":
            if not self.event_date or not self.location:
                raise ValueError("Events require a date and location.")
            if self.end_date and self.end_date < self.event_date:
                raise ValueError("Event end cannot precede its start.")
        if self.kind == "theses" and not (self.author and self.supervisor and self.degree):
            raise ValueError("Theses require author, supervisor and degree.")
        return self

class ContentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    kind: ContentKind
    title: str
    body: str
    details: dict
    status: CatalogStatus
    published_at: datetime | None
