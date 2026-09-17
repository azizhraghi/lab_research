from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from shared.database import Base
import datetime

class Researcher(Base):
    __tablename__ = "biblio_researchers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    orcid_id = Column(String, unique=True, nullable=True)
    scholar_id = Column(String, unique=True, nullable=True)
    scopus_id = Column(String, unique=True, nullable=True)
    department = Column(String)
    role = Column(String)
    
    publications = relationship("ResearcherPublication", back_populates="researcher")
    indicators = relationship("BiblioIndicator", back_populates="researcher")
    cv_profile = relationship("CVProfile", back_populates="researcher", uselist=False)


class IdentityReview(Base):
    __tablename__ = "biblio_identity_reviews"
    id = Column(String, primary_key=True)
    researcher_id = Column(Integer, nullable=False, index=True)
    identifiers = Column(JSON, nullable=False)
    reviewer_id = Column(String, nullable=False)
    rationale = Column(String, nullable=False)
    reviewed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class Publication(Base):
    __tablename__ = "biblio_publications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    abstract = Column(String, nullable=True)
    doi = Column(String, unique=True, index=True, nullable=True)
    journal = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    type = Column(String, nullable=True) # article, book, conference, etc.
    citation_count = Column(Integer, default=0)
    source = Column(String) # orcid, scholar, scopus, manual
    
    researchers = relationship("ResearcherPublication", back_populates="publication")


class ResearcherPublication(Base):
    __tablename__ = "biblio_researcher_publications"

    researcher_id = Column(Integer, ForeignKey("biblio_researchers.id"), primary_key=True)
    publication_id = Column(Integer, ForeignKey("biblio_publications.id"), primary_key=True)
    author_position = Column(Integer, nullable=True)
    
    researcher = relationship("Researcher", back_populates="publications")
    publication = relationship("Publication", back_populates="researchers")


class BiblioIndicator(Base):
    __tablename__ = "biblio_indicators"

    id = Column(Integer, primary_key=True, index=True)
    researcher_id = Column(Integer, ForeignKey("biblio_researchers.id"))
    metric_name = Column(String) # h-index, citations, etc.
    value = Column(Float)
    source = Column(String, nullable=True)
    computed_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    researcher = relationship("Researcher", back_populates="indicators")


class CVProfile(Base):
    __tablename__ = "biblio_cv_profiles"

    id = Column(Integer, primary_key=True, index=True)
    researcher_id = Column(Integer, ForeignKey("biblio_researchers.id"), unique=True)
    template = Column(String, default="default")
    custom_sections = Column(JSON, default=list) # [{title: "Experience", content: "..."}]
    last_generated = Column(DateTime, nullable=True)
    
    researcher = relationship("Researcher", back_populates="cv_profile")
