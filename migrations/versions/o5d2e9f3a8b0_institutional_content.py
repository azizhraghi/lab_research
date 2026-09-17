"""Institutional publishing; backend-only writes."""
from alembic import op
import sqlalchemy as sa
revision = "o5d2e9f3a8b0"
down_revision = "n4c1d8e2f7a9"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("institutional_content",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_index("ix_institutional_content_kind", "institutional_content", ["kind"])
    op.create_index("ix_institutional_content_status", "institutional_content", ["status"])
    if op.get_bind().dialect.name == "postgresql":
        # The trusted backend uses the owner connection. Browser Data API roles
        # get no direct access; public projection is served by FastAPI.
        op.execute("ALTER TABLE institutional_content ENABLE ROW LEVEL SECURITY")

def downgrade():
    op.drop_table("institutional_content")
