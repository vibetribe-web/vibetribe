"""add business check constraints

Revision ID: 20260518_0008
Revises: 20260517_0007
Create Date: 2026-05-18 12:15:00.000000
"""
from collections.abc import Sequence

from alembic import op

revision: str = "20260518_0008"
down_revision: str | None = "20260517_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'ck_teams_max_members_positive'
                  AND conrelid = 'teams'::regclass
            ) THEN
                ALTER TABLE teams
                ADD CONSTRAINT ck_teams_max_members_positive
                CHECK (max_members > 0) NOT VALID;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'ck_events_end_date_after_start_date'
                  AND conrelid = 'events'::regclass
            ) THEN
                ALTER TABLE events
                ADD CONSTRAINT ck_events_end_date_after_start_date
                CHECK (end_date >= start_date) NOT VALID;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE events DROP CONSTRAINT IF EXISTS ck_events_end_date_after_start_date")
    op.execute("ALTER TABLE teams DROP CONSTRAINT IF EXISTS ck_teams_max_members_positive")
