"""add external player statistics staging table

Revision ID: 0006_external_player_statistics
Revises: 0005_external_players
Create Date: 2026-07-13 00:00:05.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0006_external_player_statistics"
down_revision = "0005_external_players"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_player_statistics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="data_go"),
        sa.Column("standard_year", sa.String(length=10), nullable=False),
        sa.Column("racer_name", sa.String(length=255), nullable=False),
        sa.Column("period_number", sa.String(length=20), nullable=True),
        sa.Column("grade", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("run_count", sa.Integer(), nullable=True),
        sa.Column("run_day_count", sa.Integer(), nullable=True),
        sa.Column("rank1_count", sa.Integer(), nullable=True),
        sa.Column("rank2_count", sa.Integer(), nullable=True),
        sa.Column("rank3_count", sa.Integer(), nullable=True),
        sa.Column("rank4_count", sa.Integer(), nullable=True),
        sa.Column("rank5_count", sa.Integer(), nullable=True),
        sa.Column("rank6_count", sa.Integer(), nullable=True),
        sa.Column("rank7_count", sa.Integer(), nullable=True),
        sa.Column("rank8_count", sa.Integer(), nullable=True),
        sa.Column("rank9_count", sa.Integer(), nullable=True),
        sa.Column("eliminated_count", sa.Integer(), nullable=True),
        sa.Column("win_rate", sa.Numeric(8, 3), nullable=True),
        sa.Column("high_rate", sa.Numeric(8, 3), nullable=True),
        sa.Column("high_3_rate", sa.Numeric(8, 3), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "source", "standard_year", "racer_name", "period_number", "grade"):
        op.create_index(op.f(f"ix_external_player_statistics_{column}"), "external_player_statistics", [column], unique=False)


def downgrade() -> None:
    for column in reversed(("id", "source", "standard_year", "racer_name", "period_number", "grade")):
        op.drop_index(op.f(f"ix_external_player_statistics_{column}"), table_name="external_player_statistics")
    op.drop_table("external_player_statistics")
