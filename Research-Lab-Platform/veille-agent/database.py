from sqlalchemy import create_engine, Column, String, Text    # imports column types for our table
from sqlalchemy.orm import declarative_base, Session          # base class for our models
from sqlalchemy import JSON                                    # JSON type to store embedding vectors

Base = declarative_base()    # creates the base class all models inherit from

class Paper(Base):
    __tablename__ = "papers"    # the actual table name in the database

    id        = Column(String, primary_key=True)    # unique arXiv ID — no two papers share this
    title     = Column(String, nullable=False)       # paper title — required, can't be empty
    authors   = Column(String)                       # comma-separated list of author names
    summary   = Column(Text)                         # raw abstract from arXiv
    embedding = Column(JSON, nullable=True)          # vector of 1024 numbers for semantic search
    topic     = Column(String, nullable=True)        # theme tag assigned by mistral-small
    plain_summary = Column(Text, nullable=True)      # NEW: our plain-language summary from mistral-large

def get_engine():
    return create_engine("sqlite:///papers.db")    # connects to (or creates) papers.db

def init_db(engine):
    Base.metadata.create_all(engine)    # creates all tables if they don't exist yet