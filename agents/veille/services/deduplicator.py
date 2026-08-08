"""Embedding generation + duplicate detection for the veille agent.

Two backends:
  - Postgres (prod): the Article table has a native VECTOR(1024) column
    (`embedding_vec`) with an HNSW index. Dedup runs as a single indexed SQL
    query using the cosine distance operator `<=>`, so it scales to millions of
    articles instead of the in-memory O(N) loop.
  - SQLite (dev): no pgvector. Embeddings live in the JSON `embedding` column and
    similarity is computed by looping over rows in Python. Fine for the hundreds
    of articles a dev DB holds; not for production scale.

The dialect is chosen once at import time from the configured DATABASE_URL.
"""
import math
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import settings
from agents.veille.models import Article
from shared.llm_client import llm_client

_IS_POSTGRES = settings.database_url.startswith("postgres")


def cosine_distance(v1: list[float], v2: list[float]) -> float:
    """Cosine *distance* (1 - similarity). 0 = identical, 2 = opposite."""
    if not v1 or not v2:
        return 1.0
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if not mag1 or not mag2:
        return 1.0
    return 1.0 - (dot / (mag1 * mag2))


async def generate_embedding(text: str) -> list[float]:
    """Generate an embedding for the given text using Mistral (mistral-embed, 1024-d)."""
    try:
        embeddings = await llm_client.generate_embeddings([text])
        return embeddings[0] if embeddings else []
    except Exception as e:
        print(f"[veille:dedup] Error generating embedding: {e}")
        return []


def _has_embedding_vec() -> bool:
    """True only when the model class actually carries the Vector column."""
    return _IS_POSTGRES and hasattr(Article, "embedding_vec")


async def is_duplicate(db: AsyncSession, embedding: list[float], threshold: float = 0.1) -> bool:
    """Return True if a near-duplicate article already exists.

    `threshold` is a cosine DISTANCE (0–2). 0.1 means "treat anything within ~0.9
    cosine similarity as a duplicate". On Postgres this is a single indexed query;
    on SQLite it's a Python loop over all stored embeddings.
    """
    if not embedding:
        return False

    if _has_embedding_vec():
        # Postgres path: indexed approximate nearest-neighbour via pgvector.
        # ORDER BY ... USING GIST/HNSW + LIMIT 1 lets the index short-circuit.
        stmt = (
            select(Article.id)
            .where(Article.embedding_vec.is_not(None))
            .order_by(Article.embedding_vec.cosine_distance(embedding))
            .limit(1)
        )
        # We need the distance value to apply the threshold; pgvector exposes it
        # via the same expression used in ORDER BY.
        from sqlalchemy import literal
        distance_expr = Article.embedding_vec.cosine_distance(embedding)
        stmt = (
            select(Article.id, distance_expr.label("distance"))
            .where(Article.embedding_vec.is_not(None))
            .order_by(distance_expr)
            .limit(1)
        )
        result = await db.execute(stmt)
        row = result.first()
        if row is not None and row.distance is not None and row.distance < threshold:
            return True
        return False

    # SQLite path: in-memory cosine loop over the JSON column.
    stmt = select(Article.id, Article.embedding).where(Article.embedding.is_not(None))
    result = await db.execute(stmt)
    for article_id, db_embedding in result:
        if db_embedding and cosine_distance(embedding, db_embedding) < threshold:
            return True
    return False


async def store_embedding(article: Article, embedding: list[float]) -> None:
    """Write the embedding to both the JSON column and, on Postgres, the vector column.

    Call this right after creating the Article and before flush() so both columns
    land in the same INSERT.
    """
    article.embedding = embedding
    if _has_embedding_vec():
        article.embedding_vec = embedding
