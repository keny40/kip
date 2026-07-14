"""add external race history staging tables

Revision ID: 0007_external_race_history
Revises: 0006_external_player_statistics
Create Date: 2026-07-14 00:00:07.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0007_external_race_history"
down_revision = "0006_external_player_statistics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_races",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("standard_year", sa.String(length=10), nullable=False),
        sa.Column("meet_name", sa.String(length=100), nullable=False),
        sa.Column("week_count", sa.Integer(), nullable=False),
        sa.Column("day_count", sa.Integer(), nullable=False),
        sa.Column("race_number", sa.String(length=20), nullable=False),
        sa.Column("race_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "standard_year", "meet_name", "week_count", "day_count", "race_number", name="uq_external_races_natural_key"),
    )
    for column in ("id", "source", "standard_year", "meet_name", "week_count", "day_count", "race_number", "race_date", "status"):
        op.create_index(op.f(f"ix_external_races_{column}"), "external_races", [column], unique=False)

    op.create_table(
        "external_race_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("external_race_id", sa.Integer(), nullable=False),
        sa.Column("entry_number", sa.String(length=20), nullable=False),
        sa.Column("player_name", sa.String(length=255), nullable=False),
        sa.Column("period_number", sa.String(length=20), nullable=True),
        sa.Column("grade", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("external_player_id", sa.String(length=64), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["external_race_id"], ["external_races.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_race_id", "entry_number", name="uq_external_race_entries_race_entry"),
    )
    for column in ("id", "external_race_id", "entry_number", "player_name", "period_number", "grade", "external_player_id"):
        op.create_index(op.f(f"ix_external_race_entries_{column}"), "external_race_entries", [column], unique=False)

    op.create_table(
        "external_race_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("external_race_id", sa.Integer(), nullable=False),
        sa.Column("entry_number", sa.String(length=20), nullable=False),
        sa.Column("player_name", sa.String(length=255), nullable=True),
        sa.Column("period_number", sa.String(length=20), nullable=True),
        sa.Column("result_rank", sa.Integer(), nullable=True),
        sa.Column("result_status", sa.String(length=32), nullable=False, server_default="UNKNOWN_RESULT_STATUS"),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["external_race_id"], ["external_races.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_race_id", "entry_number", name="uq_external_race_results_race_entry"),
    )
    for column in ("id", "external_race_id", "entry_number", "player_name", "period_number", "result_rank", "result_status"):
        op.create_index(op.f(f"ix_external_race_results_{column}"), "external_race_results", [column], unique=False)


def downgrade() -> None:
    for column in reversed(("id", "external_race_id", "entry_number", "player_name", "period_number", "result_rank", "result_status")):
        op.drop_index(op.f(f"ix_external_race_results_{column}"), table_name="external_race_results")
    op.drop_table("external_race_results")
    for column in reversed(("id", "external_race_id", "entry_number", "player_name", "period_number", "grade", "external_player_id")):
        op.drop_index(op.f(f"ix_external_race_entries_{column}"), table_name="external_race_entries")
    op.drop_table("external_race_entries")
    for column in reversed(("id", "source", "standard_year", "meet_name", "week_count", "day_count", "race_number", "race_date", "status")):
        op.drop_index(op.f(f"ix_external_races_{column}"), table_name="external_races")
    op.drop_table("external_races")
