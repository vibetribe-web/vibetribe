"""align team messages shared event column

Revision ID: 20260519_0012
Revises: 20260519_0011
Create Date: 2026-05-19 11:00:00.000000
"""
from collections.abc import Sequence

from alembic import op

revision: str = "20260519_0012"
down_revision: str | None = "20260519_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'team_messages'
                  AND column_name = 'event_id'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'team_messages'
                  AND column_name = 'shared_event_id'
            ) THEN
                ALTER TABLE team_messages
                DROP CONSTRAINT IF EXISTS ck_team_messages_event_share_event_required;

                ALTER TABLE team_messages
                RENAME COLUMN event_id TO shared_event_id;

                ALTER TABLE team_messages
                ADD CONSTRAINT ck_team_messages_event_share_event_required
                CHECK ((message_type <> 'event_share') OR (shared_event_id IS NOT NULL));
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'team_messages'
                  AND column_name = 'shared_event_id'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'team_messages'
                  AND column_name = 'event_id'
            ) THEN
                ALTER TABLE team_messages
                DROP CONSTRAINT IF EXISTS ck_team_messages_event_share_event_required;

                ALTER TABLE team_messages
                RENAME COLUMN shared_event_id TO event_id;

                ALTER TABLE team_messages
                ADD CONSTRAINT ck_team_messages_event_share_event_required
                CHECK ((message_type <> 'event_share') OR (event_id IS NOT NULL));
            END IF;
        END $$;
        """
    )
