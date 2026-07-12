"""admin auth support

Revision ID: 0004_admin_auth
Revises: 0003_add_tracks
Create Date: 2026-07-12 00:00:03.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0004_admin_auth"
down_revision = "0003_add_tracks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.alter_column(
            "hashed_password",
            existing_type=sa.String(length=255),
            new_column_name="password_hash",
        )
        batch.add_column(sa.Column("role", sa.String(length=20), nullable=False, server_default="user"))
        batch.add_column(sa.Column("status", sa.String(length=20), nullable=False, server_default="active"))

    bind = op.get_bind()
    bind.execute(sa.text("UPDATE users SET role = COALESCE(role, 'user')"))
    bind.execute(
        sa.text(
            "UPDATE users "
            "SET status = CASE WHEN is_active = 1 THEN 'active' ELSE 'inactive' END "
            "WHERE status IS NULL OR trim(status) = ''"
        )
    )

    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)
    op.create_index(op.f("ix_users_status"), "users", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_status"), table_name="users")
    op.drop_index(op.f("ix_users_role"), table_name="users")

    with op.batch_alter_table("users") as batch:
        batch.drop_column("status")
        batch.drop_column("role")
        batch.alter_column(
            "password_hash",
            existing_type=sa.String(length=255),
            new_column_name="hashed_password",
        )
