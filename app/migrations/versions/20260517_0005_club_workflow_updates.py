"""update clubs workflow membership and event ownership

Revision ID: 20260517_0005
Revises: 20260517_0004
Create Date: 2026-05-17 18:15:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260517_0005"
down_revision: str | None = "20260517_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("club_members", "created_at", new_column_name="joined_at")
    op.add_column("club_members", sa.Column("added_by", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_club_members_added_by_users",
        "club_members",
        "users",
        ["added_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column("events", "posted_by", new_column_name="created_by")


def downgrade() -> None:
    op.alter_column("events", "created_by", new_column_name="posted_by")
    op.drop_constraint("fk_club_members_added_by_users", "club_members", type_="foreignkey")
    op.drop_column("club_members", "added_by")
    op.alter_column("club_members", "joined_at", new_column_name="created_at")
