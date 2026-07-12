"""initial schema

Revision ID: 0001_initial
Revises: None
Create Date: 2026-07-12 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "races",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("race_date", sa.Date(), nullable=False),
        sa.Column("track_name", sa.String(length=255), nullable=False),
        sa.Column("race_number", sa.Integer(), nullable=False),
        sa.Column("scheduled_start_time", sa.Time(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("race_date", "track_name", "race_number", name="uq_races_date_track_number"),
    )
    op.create_index(op.f("ix_races_id"), "races", ["id"], unique=False)
    op.create_index(op.f("ix_races_race_date"), "races", ["race_date"], unique=False)
    op.create_index(op.f("ix_races_race_number"), "races", ["race_number"], unique=False)
    op.create_index(op.f("ix_races_status"), "races", ["status"], unique=False)
    op.create_index(op.f("ix_races_track_name"), "races", ["track_name"], unique=False)

    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("player_number", sa.Integer(), nullable=False),
        sa.Column("grade", sa.String(length=20), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("player_number", name="uq_players_player_number"),
    )
    op.create_index(op.f("ix_players_id"), "players", ["id"], unique=False)
    op.create_index(op.f("ix_players_player_number"), "players", ["player_number"], unique=False)
    op.create_index(op.f("ix_players_grade"), "players", ["grade"], unique=False)
    op.create_index(op.f("ix_players_name"), "players", ["name"], unique=False)
    op.create_index(op.f("ix_players_region"), "players", ["region"], unique=False)
    op.create_index(op.f("ix_players_status"), "players", ["status"], unique=False)

    op.create_table(
        "entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("race_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("entry_number", sa.Integer(), nullable=False),
        sa.Column("lane_number", sa.Integer(), nullable=False),
        sa.Column("lineup_position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["race_id"], ["races.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("race_id", "entry_number", name="uq_entries_race_entry_number"),
        sa.UniqueConstraint("race_id", "player_id", name="uq_entries_race_player"),
    )
    op.create_index(op.f("ix_entries_id"), "entries", ["id"], unique=False)
    op.create_index(op.f("ix_entries_player_id"), "entries", ["player_id"], unique=False)
    op.create_index(op.f("ix_entries_race_id"), "entries", ["race_id"], unique=False)
    op.create_index(op.f("ix_entries_status"), "entries", ["status"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=False)

    op.create_table(
        "results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("race_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("finish_position", sa.Integer(), nullable=False),
        sa.Column("result_time", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["race_id"], ["races.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
    )

    op.create_table(
        "odds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("race_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("win_odds", sa.Numeric(10, 4), nullable=True),
        sa.Column("place_odds", sa.Numeric(10, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["race_id"], ["races.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
    )

    op.create_table(
        "lineups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("race_id", sa.Integer(), nullable=False),
        sa.Column("lineup_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["race_id"], ["races.id"]),
    )

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("race_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("predicted_rank", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["race_id"], ["races.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
    )

    op.create_table(
        "statistics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("metric_name", sa.String(length=255), nullable=False),
        sa.Column("metric_value", sa.Numeric(18, 6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"]),
    )

    op.create_table(
        "logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("logs")
    op.drop_table("payments")
    op.drop_table("subscriptions")
    op.drop_table("statistics")
    op.drop_table("predictions")
    op.drop_table("lineups")
    op.drop_table("odds")
    op.drop_table("results")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_entries_status"), table_name="entries")
    op.drop_index(op.f("ix_entries_race_id"), table_name="entries")
    op.drop_index(op.f("ix_entries_player_id"), table_name="entries")
    op.drop_index(op.f("ix_entries_id"), table_name="entries")
    op.drop_table("entries")
    op.drop_index(op.f("ix_players_status"), table_name="players")
    op.drop_index(op.f("ix_players_region"), table_name="players")
    op.drop_index(op.f("ix_players_name"), table_name="players")
    op.drop_index(op.f("ix_players_grade"), table_name="players")
    op.drop_index(op.f("ix_players_player_number"), table_name="players")
    op.drop_index(op.f("ix_players_id"), table_name="players")
    op.drop_table("players")
    op.drop_index(op.f("ix_races_track_name"), table_name="races")
    op.drop_index(op.f("ix_races_status"), table_name="races")
    op.drop_index(op.f("ix_races_race_number"), table_name="races")
    op.drop_index(op.f("ix_races_race_date"), table_name="races")
    op.drop_index(op.f("ix_races_id"), table_name="races")
    op.drop_table("races")
