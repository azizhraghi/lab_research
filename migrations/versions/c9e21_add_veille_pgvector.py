"""Add veille pgvector column + HNSW index

Revision ID: c9e21_add_veille_pgvector
Revises: 5f58e396ab57
Create Date: 2026-07-31

Adds a native VECTOR(1024) column (embedding_vec) to veille_articles and an
HNSW index on it. This only applies on Postgres — pgvector must be installed
as an extension first. On SQLite this migration is a no-op because the column
is added conditionally at the ORM level, not via Alembic.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9e21_add_veille_pgvector'
down_revision: Union[str, Sequence[str], None] = '5f58e396ab57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pgvector column + HNSW index. Safe to re-run (IF NOT EXISTS)."""
    # Skip on SQLite — there is no pgvector extension and the column is
    # handled conditionally in the ORM model.
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect.startswith("sqlite"):
        return

    # Ensure the pgvector extension is installed.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add the native vector column (nullable so existing rows are fine).
    op.add_column(
        "veille_articles",
        sa.Column("embedding_vec", sa.LargeBinary(), nullable=True),
    )
    # Alembic doesn't natively understand the pgvector Vector type, so we
    # cast the raw column to the proper type via raw SQL.
    op.execute("ALTER TABLE veille_articles ALTER COLUMN embedding_vec TYPE vector(1024) USING embedding_vec::vector(1024)")

    # HNSW index — O(log N) approximate nearest-neighbour queries.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_veille_articles_embedding_vec_hnsw "
        "ON veille_articles USING hnsw (embedding_vec vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    """Remove pgvector column + index."""
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect.startswith("sqlite"):
        return

    op.execute("DROP INDEX IF EXISTS ix_veille_articles_embedding_vec_hnsw")
    op.drop_column("veille_articles", "embedding_vec")
