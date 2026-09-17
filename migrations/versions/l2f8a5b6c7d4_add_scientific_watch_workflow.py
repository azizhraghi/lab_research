"""Add persisted subscriptions, inbox state, digests, and collection audits.

Revision ID: l2f8a5b6c7d4
Revises: k1e7f4a1b5c3
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "l2f8a5b6c7d4"
down_revision: Union[str, Sequence[str], None] = "k1e7f4a1b5c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The original pre-integration table allowed a null frequency. Preserve old
    # lab rules by treating that legacy value as the conservative daily cadence.
    op.execute("UPDATE veille_alert_rules SET frequency = 'daily' WHERE frequency IS NULL")
    op.add_column("veille_alert_rules", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("veille_alert_rules", sa.Column("delivery_channel", sa.String(), nullable=False, server_default="in_app"))
    op.add_column("veille_alert_rules", sa.Column("last_digest_at", sa.DateTime(), nullable=True))
    op.add_column("veille_alert_rules", sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.add_column("veille_alert_rules", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))

    op.create_table(
        "veille_article_user_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("veille_articles.id"), nullable=False),
        sa.Column("is_saved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("shared_at", sa.DateTime(), nullable=True),
        sa.Column("share_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("user_id", "article_id", name="uq_veille_article_user_state"),
    )
    op.create_index("ix_veille_article_user_states_user_id", "veille_article_user_states", ["user_id"])
    op.create_index("ix_veille_article_user_states_article_id", "veille_article_user_states", ["article_id"])

    op.create_table(
        "veille_watch_digests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("veille_alert_rules.id"), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("frequency", sa.String(), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_veille_watch_digests_rule_id", "veille_watch_digests", ["rule_id"])
    op.create_index("ix_veille_watch_digests_user_id", "veille_watch_digests", ["user_id"])

    op.create_table(
        "veille_watch_digest_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("digest_id", sa.Integer(), sa.ForeignKey("veille_watch_digests.id"), nullable=False),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("veille_articles.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("digest_id", "article_id", name="uq_veille_digest_article"),
    )
    op.create_index("ix_veille_watch_digest_items_digest_id", "veille_watch_digest_items", ["digest_id"])
    op.create_index("ix_veille_watch_digest_items_article_id", "veille_watch_digest_items", ["article_id"])

    op.create_table(
        "veille_collection_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trigger", sa.String(), nullable=False, server_default="manual"),
        sa.Column("status", sa.String(), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("articles_collected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("digests_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("veille_collection_runs")
    op.drop_index("ix_veille_watch_digest_items_article_id", table_name="veille_watch_digest_items")
    op.drop_index("ix_veille_watch_digest_items_digest_id", table_name="veille_watch_digest_items")
    op.drop_table("veille_watch_digest_items")
    op.drop_index("ix_veille_watch_digests_user_id", table_name="veille_watch_digests")
    op.drop_index("ix_veille_watch_digests_rule_id", table_name="veille_watch_digests")
    op.drop_table("veille_watch_digests")
    op.drop_index("ix_veille_article_user_states_article_id", table_name="veille_article_user_states")
    op.drop_index("ix_veille_article_user_states_user_id", table_name="veille_article_user_states")
    op.drop_table("veille_article_user_states")
    for column in ("updated_at", "created_at", "last_digest_at", "delivery_channel", "active"):
        op.drop_column("veille_alert_rules", column)
