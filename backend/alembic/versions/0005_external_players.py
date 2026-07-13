"""add external player staging table

Revision ID: 0005_external_players
Revises: 0004_admin_auth
Create Date: 2026-07-13 00:00:04.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0005_external_players"
down_revision = "0004_admin_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("period_number", sa.String(length=20), nullable=True),
        sa.Column("grade", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("region", sa.String(length=100), nullable=False, server_default="unknown"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("detail_url", sa.String(length=500), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "external_id", name="uq_external_players_source_external_id"),
    )
    op.create_index(op.f("ix_external_players_id"), "external_players", ["id"], unique=False)
    op.create_index(op.f("ix_external_players_source"), "external_players", ["source"], unique=False)
    op.create_index(op.f("ix_external_players_external_id"), "external_players", ["external_id"], unique=False)
    op.create_index(op.f("ix_external_players_name"), "external_players", ["name"], unique=False)
    op.create_index(op.f("ix_external_players_period_number"), "external_players", ["period_number"], unique=False)
    op.create_index(op.f("ix_external_players_grade"), "external_players", ["grade"], unique=False)
    op.create_index(op.f("ix_external_players_region"), "external_players", ["region"], unique=False)
    op.create_index(op.f("ix_external_players_status"), "external_players", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_external_players_status"), table_name="external_players")
    op.drop_index(op.f("ix_external_players_region"), table_name="external_players")
    op.drop_index(op.f("ix_external_players_grade"), table_name="external_players")
    op.drop_index(op.f("ix_external_players_period_number"), table_name="external_players")
    op.drop_index(op.f("ix_external_players_name"), table_name="external_players")
    op.drop_index(op.f("ix_external_players_external_id"), table_name="external_players")
    op.drop_index(op.f("ix_external_players_source"), table_name="external_players")
    op.drop_index(op.f("ix_external_players_id"), table_name="external_players")
    op.drop_table("external_players")
