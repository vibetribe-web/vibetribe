"""add google oauth user fields

Revision ID: 20260517_0007
Revises: 20260517_0006
Create Date: 2026-05-17 19:30:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260517_0007"
down_revision: str | None = "20260517_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("auth_provider", sa.String(length=40), server_default="email", nullable=False),
    )
    op.add_column("users", sa.Column("google_id", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("profile_image_url", sa.String(length=2048), nullable=True))
    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_google_id"), table_name="users")
    op.drop_column("users", "profile_image_url")
    op.drop_column("users", "google_id")
    op.drop_column("users", "auth_provider")
