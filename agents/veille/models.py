import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from shared.config import settings
from shared.database import Base

# pgvector is only available on Postgres. On SQLite (dev) the embedding lives in
# the JSON column below and similarity is computed in Python; on Postgres (prod)
# we ALSO keep a real VECTOR column so dedup runs as an indexed SQL query.
_IS_POSTGRES = settings.database_url.startswith("postgres")
if _IS_POSTGRES:
    from pgvector.sqlalchemy import Vector
    # mistral-embed outputs 1024 dimensions.
    EMBEDDING_DIM = 1024

class Source(Base):
    __tablename__ = "veille_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)  # rss, atom, arxiv, pubmed, api, etc.
    url = Column(String)
    config = Column(JSON, nullable=True)
    active = Column(Boolean, default=True)
    last_scraped = Column(DateTime, nullable=True)

    articles = relationship("Article", back_populates="source")

class Article(Base):
    __tablename__ = "veille_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    abstract = Column(Text, nullable=True)
    authors = Column(JSON, nullable=True)  # List of authors
    doi = Column(String, unique=True, index=True, nullable=True)
    url = Column(String, nullable=True)
    source_id = Column(Integer, ForeignKey("veille_sources.id"))
    published_at = Column(DateTime, nullable=True)
    # JSON copy of the embedding — always present, works on every dialect.
    embedding = Column(JSON, nullable=True)
    collected_at = Column(DateTime, default=datetime.datetime.utcnow)
    # Native vector column — Postgres only. Mirrors `embedding` and is what the
    # HNSW index and the <=> / <#> operators run against for O(log N) dedup.
    if _IS_POSTGRES:
        embedding_vec = Column(Vector(EMBEDDING_DIM), nullable=True)

    source = relationship("Source", back_populates="articles")
    tags = relationship("ArticleTag", back_populates="article", cascade="all, delete-orphan")
    summaries = relationship("ArticleSummary", back_populates="article", cascade="all, delete-orphan")
    notifications = relationship("AlertNotification", back_populates="article")

class ArticleTag(Base):
    __tablename__ = "veille_article_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("veille_articles.id"))
    tag = Column(String, index=True)
    confidence = Column(Float, nullable=True)

    article = relationship("Article", back_populates="tags")

class ArticleSummary(Base):
    __tablename__ = "veille_article_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("veille_articles.id"))
    language = Column(String(10)) # en, fr
    summary_text = Column(Text)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

    article = relationship("Article", back_populates="summaries")

class AlertRule(Base):
    """A researcher's saved watch subscription and digest cadence."""
    __tablename__ = "veille_alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True) # ID from the auth system
    keywords = Column(JSON, nullable=True)
    themes = Column(JSON, nullable=True)
    frequency = Column(String, nullable=False, default="daily") # daily, weekly
    active = Column(Boolean, nullable=False, default=True)
    delivery_channel = Column(String, nullable=False, default="in_app")
    last_digest_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    
    notifications = relationship("AlertNotification", back_populates="rule")

class AlertNotification(Base):
    __tablename__ = "veille_alert_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("veille_alert_rules.id"))
    article_id = Column(Integer, ForeignKey("veille_articles.id"))
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)
    channel = Column(String) # email, in_app

    rule = relationship("AlertRule", back_populates="notifications")
    article = relationship("Article", back_populates="notifications")


class ArticleUserState(Base):
    """Private, persisted reading state for one user and one collected article."""
    __tablename__ = "veille_article_user_states"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_veille_article_user_state"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("veille_articles.id"), nullable=False, index=True)
    is_saved = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime, nullable=True)
    shared_at = Column(DateTime, nullable=True)
    share_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    article = relationship("Article")


class WatchDigest(Base):
    """Immutable in-app digest created for a subscription at a known time."""
    __tablename__ = "veille_watch_digests"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("veille_alert_rules.id"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    frequency = Column(String, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    item_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    rule = relationship("AlertRule")
    items = relationship("WatchDigestItem", back_populates="digest", cascade="all, delete-orphan")


class WatchDigestItem(Base):
    __tablename__ = "veille_watch_digest_items"

    id = Column(Integer, primary_key=True, index=True)
    digest_id = Column(Integer, ForeignKey("veille_watch_digests.id"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("veille_articles.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    digest = relationship("WatchDigest", back_populates="items")
    article = relationship("Article")


class CollectionRun(Base):
    """Auditable collection attempt, including empty and failed runs."""
    __tablename__ = "veille_collection_runs"

    id = Column(Integer, primary_key=True, index=True)
    trigger = Column(String, nullable=False, default="manual")
    status = Column(String, nullable=False, default="running")
    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    source_count = Column(Integer, nullable=False, default=0)
    articles_collected = Column(Integer, nullable=False, default=0)
    digests_created = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)


class LiteratureReview(Base):
    """A private topic-specific review with source snapshots and decisions."""
    __tablename__ = "veille_literature_reviews"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    topic = Column(String, nullable=False)
    status = Column(String, nullable=False, default="collecting")
    error_message = Column(Text, nullable=True)
    items = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
