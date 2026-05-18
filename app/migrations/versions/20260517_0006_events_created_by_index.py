"""add events created_by index

Revision ID: 20260517_0006
Revises: 20260517_0005
Create Date: 2026-05-17 18:45:00.000000
"""
from collections.abc import Sequence

from alembic import op

revision: str = "20260517_0006"
down_revision: str | None = "20260517_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_events_created_by", "events", ["created_by"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_events_created_by", table_name="events")
