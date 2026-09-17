"""Add MIS project operations: lifecycle, finance, reservations, maintenance.

Revision ID: m3a9b6c7d8e5
Revises: l2f8a5b6c7d4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "m3a9b6c7d8e5"
down_revision: Union[str, Sequence[str], None] = "l2f8a5b6c7d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps(columns: list[sa.Column]) -> list[sa.Column]:
    return columns + [
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    ]


def upgrade() -> None:
    # The original MIS models pre-date the migration discipline and were
    # created only by CREATE_SCHEMA_ON_STARTUP in development. Make a clean,
    # migration-only deployment complete while leaving existing lab databases
    # untouched.
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("projets"):
        op.create_table("projets",
            sa.Column("id", sa.String(), primary_key=True), sa.Column("nom", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=True), sa.Column("statut", sa.String(), nullable=False),
            sa.Column("date_debut", sa.Date(), nullable=False), sa.Column("date_fin_prevue", sa.Date(), nullable=True),
            sa.Column("budget_alloue", sa.Float(), nullable=False), sa.Column("responsable", sa.String(), nullable=False),
        )
    if not inspector.has_table("personnels"):
        op.create_table("personnels",
            sa.Column("id", sa.String(), primary_key=True), sa.Column("nom", sa.String(), nullable=False),
            sa.Column("prenom", sa.String(), nullable=False), sa.Column("email", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False), sa.Column("competences", sa.String(), nullable=False),
            sa.Column("disponible", sa.Boolean(), nullable=False), sa.Column("projet_actuel_id", sa.String(), nullable=True),
        )
    if not inspector.has_table("equipements"):
        op.create_table("equipements",
            sa.Column("id", sa.String(), primary_key=True), sa.Column("nom", sa.String(), nullable=False),
            sa.Column("type", sa.String(), nullable=False), sa.Column("etat", sa.String(), nullable=False),
            sa.Column("localisation", sa.String(), nullable=False), sa.Column("responsable_id", sa.String(), nullable=True),
            sa.Column("date_acquisition", sa.Date(), nullable=True), sa.Column("valeur_estimee", sa.Float(), nullable=False),
        )
    if not inspector.has_table("budgets"):
        op.create_table("budgets",
            sa.Column("id", sa.String(), primary_key=True), sa.Column("projet_id", sa.String(), nullable=False),
            sa.Column("montant_alloue", sa.Float(), nullable=False), sa.Column("montant_depense", sa.Float(), nullable=False),
            sa.Column("devise", sa.String(), nullable=False), sa.Column("date_debut", sa.Date(), nullable=False),
            sa.Column("date_fin", sa.Date(), nullable=True), sa.Column("description", sa.String(), nullable=True),
        )

    op.create_table("mis_project_milestones", *_timestamps([
        sa.Column("id", sa.String(), primary_key=True), sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False), sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("owner_id", sa.String(), nullable=True), sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    ]))
    op.create_index("ix_mis_project_milestones_project_id", "mis_project_milestones", ["project_id"])
    op.create_index("ix_mis_project_milestones_status", "mis_project_milestones", ["status"])

    op.create_table("mis_project_deliverables", *_timestamps([
        sa.Column("id", sa.String(), primary_key=True), sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False), sa.Column("deliverable_type", sa.String(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True), sa.Column("status", sa.String(), nullable=False, server_default="planned"),
        sa.Column("owner_id", sa.String(), nullable=True), sa.Column("url", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True), sa.Column("submitted_at", sa.DateTime(), nullable=True),
    ]))
    op.create_index("ix_mis_project_deliverables_project_id", "mis_project_deliverables", ["project_id"])
    op.create_index("ix_mis_project_deliverables_status", "mis_project_deliverables", ["status"])

    op.create_table("mis_project_risks", *_timestamps([
        sa.Column("id", sa.String(), primary_key=True), sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False), sa.Column("description", sa.Text(), nullable=True),
        sa.Column("likelihood", sa.Integer(), nullable=False, server_default="3"), sa.Column("impact", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("status", sa.String(), nullable=False, server_default="open"), sa.Column("owner_id", sa.String(), nullable=True),
        sa.Column("mitigation", sa.Text(), nullable=True),
    ]))
    op.create_index("ix_mis_project_risks_project_id", "mis_project_risks", ["project_id"])
    op.create_index("ix_mis_project_risks_status", "mis_project_risks", ["status"])

    op.create_table("mis_budget_entries",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("budget_id", sa.String(), nullable=False), sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("entry_type", sa.String(), nullable=False), sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False), sa.Column("vendor", sa.String(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False), sa.Column("currency", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.Date(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for column in ("budget_id", "project_id", "entry_type"):
        op.create_index(f"ix_mis_budget_entries_{column}", "mis_budget_entries", [column])

    op.create_table("mis_equipment_reservations",
        sa.Column("id", sa.String(), primary_key=True), sa.Column("equipment_id", sa.String(), nullable=False), sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("requester_id", sa.String(), nullable=False), sa.Column("purpose", sa.String(), nullable=False),
        sa.Column("start_at", sa.DateTime(), nullable=False), sa.Column("end_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="requested"), sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True), sa.Column("notes", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for column in ("equipment_id", "project_id", "start_at", "end_at", "status"):
        op.create_index(f"ix_mis_equipment_reservations_{column}", "mis_equipment_reservations", [column])

    op.create_table("mis_equipment_maintenance", *_timestamps([
        sa.Column("id", sa.String(), primary_key=True), sa.Column("equipment_id", sa.String(), nullable=False),
        sa.Column("maintenance_type", sa.String(), nullable=False), sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="scheduled"), sa.Column("performed_at", sa.DateTime(), nullable=True),
        sa.Column("performed_by", sa.String(), nullable=True), sa.Column("notes", sa.Text(), nullable=True),
    ]))
    for column in ("equipment_id", "due_date", "status"):
        op.create_index(f"ix_mis_equipment_maintenance_{column}", "mis_equipment_maintenance", [column])


def downgrade() -> None:
    for table, indexes in (
        ("mis_equipment_maintenance", ("equipment_id", "due_date", "status")),
        ("mis_equipment_reservations", ("equipment_id", "project_id", "start_at", "end_at", "status")),
        ("mis_budget_entries", ("budget_id", "project_id", "entry_type")),
        ("mis_project_risks", ("project_id", "status")),
        ("mis_project_deliverables", ("project_id", "status")),
        ("mis_project_milestones", ("project_id", "status")),
    ):
        for column in indexes:
            op.drop_index(f"ix_{table}_{column}", table_name=table)
        op.drop_table(table)
