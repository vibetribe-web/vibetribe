"""add team conversation messages

Revision ID: 20260519_0011
Revises: 20260518_0010
Create Date: 2026-05-19 10:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260519_0011"
down_revision: str | None = "20260518_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

team_message_type = postgresql.ENUM("text", "event_share", name="team_message_type", create_type=False)


def upgrade() -> None:
    postgresql.ENUM("text", "event_share", name="team_message_type").create(
        op.get_bind(),
        checkfirst=True,
    )

    op.create_table(
        "team_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("message_type", team_message_type, nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("shared_event_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "(message_type <> 'text') OR (content IS NOT NULL AND length(trim(content)) > 0)",
            name="ck_team_messages_text_content_required",
        ),
        sa.CheckConstraint(
            "(message_type <> 'event_share') OR (shared_event_id IS NOT NULL)",
            name="ck_team_messages_event_share_event_required",
        ),
        sa.ForeignKeyConstraint(["shared_event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_team_messages_id"), "team_messages", ["id"], unique=False)
    op.create_index("ix_team_messages_team_id", "team_messages", ["team_id"], unique=False)
    op.create_index("ix_team_messages_created_at", "team_messages", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_team_messages_created_at", table_name="team_messages")
    op.drop_index("ix_team_messages_team_id", table_name="team_messages")
    op.drop_index(op.f("ix_team_messages_id"), table_name="team_messages")
    op.drop_table("team_messages")
    team_message_type.drop(op.get_bind(), checkfirst=True)
