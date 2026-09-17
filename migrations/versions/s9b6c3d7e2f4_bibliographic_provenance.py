"""Metric provider provenance and manual identifier review history."""
from alembic import op
import sqlalchemy as sa
revision='s9b6c3d7e2f4'
down_revision='r8a5b2c6d1e3'
branch_labels=None
depends_on=None
def upgrade():
    op.add_column('biblio_indicators',sa.Column('source',sa.String(),nullable=True))
    op.create_table('biblio_identity_reviews',sa.Column('id',sa.String(),primary_key=True),
        sa.Column('researcher_id',sa.Integer(),nullable=False),sa.Column('identifiers',sa.JSON(),nullable=False),
        sa.Column('reviewer_id',sa.String(),nullable=False),sa.Column('rationale',sa.String(),nullable=False),
        sa.Column('reviewed_at',sa.DateTime(),nullable=False))
    op.create_index('ix_biblio_identity_reviews_researcher_id','biblio_identity_reviews',['researcher_id'])
    if op.get_bind().dialect.name=='postgresql':
        op.execute('ALTER TABLE biblio_identity_reviews ENABLE ROW LEVEL SECURITY')
        op.execute("""DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN REVOKE ALL ON biblio_identity_reviews FROM anon; END IF;
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN REVOKE ALL ON biblio_identity_reviews FROM authenticated; END IF;
        END $$""")
def downgrade():
    op.drop_table('biblio_identity_reviews')
    op.drop_column('biblio_indicators','source')
