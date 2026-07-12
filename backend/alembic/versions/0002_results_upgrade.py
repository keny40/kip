"""upgrade results schema

Revision ID: 0002_results_upgrade
Revises: 0001_initial
Create Date: 2026-07-12 00:00:00.000001
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_results_upgrade"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("results")
    op.create_table(
        "results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("race_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("finish_position", sa.Integer(), nullable=False),
        sa.Column("finish_time", sa.String(length=50), nullable=True),
        sa.Column("result_status", sa.String(length=32), nullable=False),
        sa.Column("points", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["race_id"], ["races.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("race_id", "player_id", name="uq_results_race_player"),
    )
    op.create_index(op.f("ix_results_id"), "results", ["id"], unique=False)
    op.create_index(op.f("ix_results_race_id"), "results", ["race_id"], unique=False)
    op.create_index(op.f("ix_results_player_id"), "results", ["player_id"], unique=False)
    op.create_index(op.f("ix_results_result_status"), "results", ["result_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_results_result_status"), table_name="results")
    op.drop_index(op.f("ix_results_player_id"), table_name="results")
    op.drop_index(op.f("ix_results_race_id"), table_name="results")
    op.drop_index(op.f("ix_results_id"), table_name="results")
    op.drop_table("results")
