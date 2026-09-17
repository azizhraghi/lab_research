"""Private topic-specific literature reviews."""
from alembic import op
import sqlalchemy as sa
revision = "p6e3f0a4b9c1"
down_revision = "o5d2e9f3a8b0"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("veille_literature_reviews",
        sa.Column("id",sa.String(),primary_key=True),
        sa.Column("user_id",sa.String(),nullable=False),
        sa.Column("topic",sa.String(),nullable=False),
        sa.Column("status",sa.String(),nullable=False),
        sa.Column("error_message",sa.Text(),nullable=True),
        sa.Column("items",sa.JSON(),nullable=False),
        sa.Column("created_at",sa.DateTime(),nullable=False),
        sa.Column("updated_at",sa.DateTime(),nullable=False))
    op.create_index("ix_veille_literature_reviews_user_id","veille_literature_reviews",["user_id"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE veille_literature_reviews ENABLE ROW LEVEL SECURITY")

def downgrade():
    op.drop_table("veille_literature_reviews")
