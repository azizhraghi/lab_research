"""Project research dossiers with explicit literature snapshots."""
from alembic import op
import sqlalchemy as sa

revision = "q7f4a1b5c0d2"
down_revision = "p6e3f0a4b9c1"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("mis_project_dossiers",
        sa.Column("project_id", sa.String(), sa.ForeignKey("projets.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        *(sa.Column(name, sa.Text(), nullable=False) for name in ("questions", "approach", "findings", "limitations")),
        sa.Column("references", sa.JSON(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False))
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE mis_project_dossiers ENABLE ROW LEVEL SECURITY")
        # The backend owns access; client roles must not bypass its role checks.
        op.execute("""DO $$ BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
            REVOKE ALL ON mis_project_dossiers FROM anon;
          END IF;
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
            REVOKE ALL ON mis_project_dossiers FROM authenticated;
          END IF;
        END $$""")

def downgrade():
    op.drop_table("mis_project_dossiers")
