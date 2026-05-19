"""add event interests

Revision ID: 20260519_0013
Revises: 20260519_0012
Create Date: 2026-05-19 17:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260519_0013"
down_revision: str | None = "20260519_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_interests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "event_id", name="uq_event_interests_user_event"),
    )
    op.create_index(op.f("ix_event_interests_id"), "event_interests", ["id"], unique=False)
    op.create_index("ix_event_interests_user_id", "event_interests", ["user_id"], unique=False)
    op.create_index("ix_event_interests_event_id", "event_interests", ["event_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_event_interests_event_id", table_name="event_interests")
    op.drop_index("ix_event_interests_user_id", table_name="event_interests")
    op.drop_index(op.f("ix_event_interests_id"), table_name="event_interests")
    op.drop_table("event_interests")
