"""add tracks and migrate races to track_id

Revision ID: 0003_add_tracks
Revises: 0002_results_upgrade
Create Date: 2026-07-12 00:00:02.000000
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op


revision = "0003_add_tracks"
down_revision = "0002_results_upgrade"
branch_labels = None
depends_on = None


def _slugify_code(value: str) -> str:
    code = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_").upper()
    return code or "TRACK"


def upgrade() -> None:
    bind = op.get_bind()

    op.create_table(
        "tracks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code", name="uq_tracks_code"),
        sa.UniqueConstraint("name", name="uq_tracks_name"),
    )
    op.create_index(op.f("ix_tracks_id"), "tracks", ["id"], unique=False)
    op.create_index(op.f("ix_tracks_code"), "tracks", ["code"], unique=False)
    op.create_index(op.f("ix_tracks_name"), "tracks", ["name"], unique=False)
    op.create_index(op.f("ix_tracks_region"), "tracks", ["region"], unique=False)
    op.create_index(op.f("ix_tracks_status"), "tracks", ["status"], unique=False)

    races = sa.table(
        "races",
        sa.column("id", sa.Integer()),
        sa.column("track_name", sa.String()),
        sa.column("track_id", sa.Integer()),
    )
    distinct_track_names = [
        row[0]
        for row in bind.execute(
            sa.text(
                "SELECT DISTINCT track_name "
                "FROM races "
                "WHERE track_name IS NOT NULL AND trim(track_name) <> '' "
                "ORDER BY track_name"
            )
        )
    ]
    track_name_to_id: dict[str, int] = {}
    used_codes: set[str] = set()
    utc_now = datetime.now(timezone.utc)
    tracks_table = sa.table(
        "tracks",
        sa.column("id", sa.Integer()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("region", sa.String()),
        sa.column("address", sa.String()),
        sa.column("status", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    for track_name in distinct_track_names:
        code_base = _slugify_code(track_name)
        code = code_base
        suffix = 2
        while code in used_codes:
            code = f"{code_base}_{suffix}"
            suffix += 1
        used_codes.add(code)

        bind.execute(
            sa.insert(tracks_table).values(
                code=code,
                name=track_name,
                region="Unknown",
                address=None,
                status="active",
                created_at=utc_now,
                updated_at=utc_now,
            )
        )
        inserted_id = bind.scalar(sa.select(tracks_table.c.id).where(tracks_table.c.code == code))
        track_name_to_id[track_name] = int(inserted_id)

    op.add_column("races", sa.Column("track_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_races_track_id"), "races", ["track_id"], unique=False)

    for track_name, track_id in track_name_to_id.items():
        bind.execute(
            sa.text("UPDATE races SET track_id = :track_id WHERE track_name = :track_name"),
            {"track_id": track_id, "track_name": track_name},
        )

    remaining_rows = int(
        bind.scalar(sa.text("SELECT COUNT(*) FROM races WHERE track_id IS NULL")) or 0
    )
    if remaining_rows > 0:
        fallback_code = "UNKNOWN_TRACK"
        fallback_name = "Unknown Track"
        bind.execute(
            sa.insert(tracks_table).values(
                code=fallback_code,
                name=fallback_name,
                region="Unknown",
                address=None,
                status="active",
                created_at=utc_now,
                updated_at=utc_now,
            )
        )
        fallback_track_id = int(bind.scalar(sa.select(tracks_table.c.id).where(tracks_table.c.code == fallback_code)))
        bind.execute(
            sa.text("UPDATE races SET track_id = :track_id WHERE track_id IS NULL"),
            {"track_id": fallback_track_id},
        )

    with op.batch_alter_table("races") as batch:
        batch.alter_column("track_name", existing_type=sa.String(length=255), nullable=True)
        batch.drop_constraint("uq_races_date_track_number", type_="unique")
        batch.create_foreign_key("fk_races_track_id_tracks", "tracks", ["track_id"], ["id"], ondelete="RESTRICT")
        batch.alter_column("track_id", existing_type=sa.Integer(), nullable=False)
        batch.create_unique_constraint("uq_races_date_track_number", ["race_date", "track_id", "race_number"])


def downgrade() -> None:
    with op.batch_alter_table("races") as batch:
        batch.drop_constraint("uq_races_date_track_number", type_="unique")
        batch.drop_constraint("fk_races_track_id_tracks", type_="foreignkey")
        batch.alter_column("track_id", existing_type=sa.Integer(), nullable=True)
        batch.create_unique_constraint("uq_races_date_track_number", ["race_date", "track_name", "race_number"])
        batch.alter_column("track_name", existing_type=sa.String(length=255), nullable=False)

    op.drop_index(op.f("ix_races_track_id"), table_name="races")
    op.drop_column("races", "track_id")

    op.drop_index(op.f("ix_tracks_status"), table_name="tracks")
    op.drop_index(op.f("ix_tracks_region"), table_name="tracks")
    op.drop_index(op.f("ix_tracks_name"), table_name="tracks")
    op.drop_index(op.f("ix_tracks_code"), table_name="tracks")
    op.drop_index(op.f("ix_tracks_id"), table_name="tracks")
    op.drop_table("tracks")
