"""add unique usernames to users

Revision ID: 20260518_0009
Revises: 20260518_0008
Create Date: 2026-05-18 18:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260518_0009"
down_revision: str | None = "20260518_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=30), nullable=True))
    op.execute(
        """
        WITH generated AS (
            SELECT
                id,
                LEFT(
                    TRIM(BOTH '_' FROM regexp_replace(lower(COALESCE(NULLIF(split_part(email, '@', 1), ''), name, 'student')), '[^a-z0-9_]+', '_', 'g')),
                    20
                ) AS base_username
            FROM users
            WHERE username IS NULL
        )
        UPDATE users
        SET username = CASE
            WHEN length(generated.base_username) >= 3
                THEN LEFT(generated.base_username || '_' || users.id::text, 30)
            ELSE 'user_' || users.id::text
        END
        FROM generated
        WHERE users.id = generated.id
          AND users.username IS NULL;
        """
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_column("users", "username")
