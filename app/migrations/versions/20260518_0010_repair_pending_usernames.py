"""repair missing or pending usernames

Revision ID: 20260518_0010
Revises: 20260518_0009
Create Date: 2026-05-18 19:10:00.000000
"""
from collections.abc import Sequence

from alembic import op

revision: str = "20260518_0010"
down_revision: str | None = "20260518_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE
            rec RECORD;
            base TEXT;
            candidate TEXT;
            suffix TEXT;
        BEGIN
            FOR rec IN
                SELECT id, name
                FROM users
                WHERE username IS NULL OR username = 'pending'
                ORDER BY id
            LOOP
                base := lower(COALESCE(NULLIF(rec.name, ''), 'user_' || rec.id::text));
                base := regexp_replace(base, '[^a-z0-9_]+', '_', 'g');
                base := regexp_replace(base, '_+', '_', 'g');
                base := trim(both '_' from base);

                IF length(base) < 3 THEN
                    base := 'user_' || rec.id::text;
                END IF;

                base := left(base, 24);
                candidate := base;

                WHILE EXISTS (
                    SELECT 1 FROM users
                    WHERE username = candidate
                      AND id <> rec.id
                ) LOOP
                    suffix := (1000 + floor(random() * 9000)::int)::text;
                    candidate := left(base, 25) || '_' || suffix;
                    candidate := left(candidate, 30);
                END LOOP;

                UPDATE users
                SET username = candidate
                WHERE id = rec.id;
            END LOOP;
        END $$;
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)")


def downgrade() -> None:
    pass
