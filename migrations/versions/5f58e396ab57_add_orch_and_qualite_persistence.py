"""add_orch_and_qualite_persistence

Revision ID: 5f58e396ab57
Revises: b814_forecast_calibration
Create Date: 2026-07-30 21:09:05.696214

Adds persistent tables for the Orchestrator (alerts + event history) and
Qualité agent (validation reports). Previously both agents kept state only in
Python lists, losing everything on restart.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f58e396ab57'
down_revision: Union[str, Sequence[str], None] = 'b814_forecast_calibration'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'orch_alertes',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('niveau', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('source_evenement', sa.String(), nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('resolue', sa.Boolean(), nullable=False, default=False, index=True),
    )

    op.create_table(
        'orch_historique',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('type_evenement', sa.String(), nullable=False, index=True),
        sa.Column('source_agent', sa.String(), nullable=False, index=True),
        sa.Column('payload', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('traite', sa.Boolean(), nullable=False, default=True),
        sa.Column('alertes_generees', sa.JSON(), nullable=False, server_default='[]'),
    )

    op.create_table(
        'qualite_rapports',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('entite_type', sa.String(), nullable=False, index=True),
        sa.Column('entite_id', sa.String(), nullable=False, index=True),
        sa.Column('niveau', sa.String(), nullable=False),
        sa.Column('problemes', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('conforme_rgpd', sa.Boolean(), nullable=False, default=True),
    )


def downgrade() -> None:
    op.drop_table('qualite_rapports')
    op.drop_table('orch_historique')
    op.drop_table('orch_alertes')
