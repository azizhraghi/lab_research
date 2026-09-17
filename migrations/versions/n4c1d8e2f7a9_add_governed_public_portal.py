"""Add an approval-controlled, redacted public portal catalogue.

Revision ID: n4c1d8e2f7a9
Revises: m3a9b6c7d8e5
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "n4c1d8e2f7a9"
down_revision: Union[str, Sequence[str], None] = "m3a9b6c7d8e5"
branch_labels = None
depends_on = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table("public_researcher_profiles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("researcher_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("visibility", sa.String(), nullable=False, server_default="hidden"),
        sa.Column("consent_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consent_version", sa.String(), nullable=True),
        sa.Column("consented_at", sa.DateTime(), nullable=True),
        sa.Column("public_bio", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by", sa.String(), nullable=True),
        *_audit_columns(),
    )
    op.create_index("ix_public_researcher_profiles_researcher_id", "public_researcher_profiles", ["researcher_id"])
    op.create_index("ix_public_researcher_profiles_visibility", "public_researcher_profiles", ["visibility"])

    op.create_table("public_publications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source_publication_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("title", sa.String(), nullable=False), sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("doi", sa.String(), nullable=True), sa.Column("journal", sa.String(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True), sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("approved_at", sa.DateTime(), nullable=True), sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True), *_audit_columns(),
    )
    op.create_index("ix_public_publications_source_publication_id", "public_publications", ["source_publication_id"])
    op.create_index("ix_public_publications_status", "public_publications", ["status"])

    op.create_table("public_project_summaries",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("project_id", sa.String(), nullable=False, unique=True),
        sa.Column("title", sa.String(), nullable=False), sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("research_area", sa.String(), nullable=True), sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("start_date", sa.Date(), nullable=True), sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True), sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True), *_audit_columns(),
    )
    op.create_index("ix_public_project_summaries_project_id", "public_project_summaries", ["project_id"])
    op.create_index("ix_public_project_summaries_status", "public_project_summaries", ["status"])

    op.create_table("public_datasets",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False), sa.Column("version", sa.String(), nullable=False),
        sa.Column("license", sa.String(), nullable=False), sa.Column("access_url", sa.String(), nullable=True),
        sa.Column("citation", sa.Text(), nullable=True), sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("approved_at", sa.DateTime(), nullable=True), sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True), *_audit_columns(),
    )
    op.create_index("ix_public_datasets_status", "public_datasets", ["status"])


def downgrade() -> None:
    op.drop_index("ix_public_datasets_status", table_name="public_datasets")
    op.drop_table("public_datasets")
    op.drop_index("ix_public_project_summaries_status", table_name="public_project_summaries")
    op.drop_index("ix_public_project_summaries_project_id", table_name="public_project_summaries")
    op.drop_table("public_project_summaries")
    op.drop_index("ix_public_publications_status", table_name="public_publications")
    op.drop_index("ix_public_publications_source_publication_id", table_name="public_publications")
    op.drop_table("public_publications")
    op.drop_index("ix_public_researcher_profiles_visibility", table_name="public_researcher_profiles")
    op.drop_index("ix_public_researcher_profiles_researcher_id", table_name="public_researcher_profiles")
    op.drop_table("public_researcher_profiles")
