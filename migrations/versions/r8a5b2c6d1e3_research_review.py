"""Evidence-linked findings, evaluation records and preserved submissions."""
from alembic import op
import sqlalchemy as sa
revision = "r8a5b2c6d1e3"
down_revision = "q7f4a1b5c0d2"
branch_labels = None
depends_on = None

def upgrade():
    for name in ("claims", "evaluations"):
        op.add_column("mis_project_dossiers", sa.Column(name, sa.JSON(), nullable=False, server_default='[]'))
    op.create_table("mis_dossier_submissions",
        sa.Column("id",sa.String(),primary_key=True),
        sa.Column("project_id",sa.String(),nullable=False),
        sa.Column("revision",sa.Integer(),nullable=False),
        sa.Column("snapshot",sa.JSON(),nullable=False),
        sa.Column("digest",sa.String(),nullable=False),
        sa.Column("submitted_by",sa.String(),nullable=False),
        sa.Column("submitted_at",sa.DateTime(),nullable=False),
        sa.Column("status",sa.String(),nullable=False),
        sa.Column("reviewed_by",sa.String(),nullable=True),
        sa.Column("reviewed_at",sa.DateTime(),nullable=True),
        sa.Column("feedback",sa.Text(),nullable=True),
        sa.UniqueConstraint("project_id","revision",name="uq_submission_project_revision"))
    op.create_index("ix_mis_dossier_submissions_project_id","mis_dossier_submissions",["project_id"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE mis_dossier_submissions ENABLE ROW LEVEL SECURITY")
        op.execute("""DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN REVOKE ALL ON mis_dossier_submissions FROM anon; END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN REVOKE ALL ON mis_dossier_submissions FROM authenticated; END IF;
        END $$""")

def downgrade():
    op.drop_table("mis_dossier_submissions")
    op.drop_column("mis_project_dossiers","evaluations")
    op.drop_column("mis_project_dossiers","claims")
