"""add clubs and events module

Revision ID: 20260517_0004
Revises: 20260516_0003
Create Date: 2026-05-17 17:30:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260517_0004"
down_revision: str | None = "20260516_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

club_member_role = postgresql.ENUM("leader", "member", name="club_member_role")
event_type = postgresql.ENUM("hackathon", "event", name="event_type")
event_mode = postgresql.ENUM("online", "offline", "hybrid", name="event_mode")


def upgrade() -> None:
    club_member_role.create(op.get_bind(), checkfirst=True)
    event_type.create(op.get_bind(), checkfirst=True)
    event_mode.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "clubs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_clubs_id"), "clubs", ["id"], unique=False)
    op.create_index(op.f("ix_clubs_name"), "clubs", ["name"], unique=True)
    op.create_index("ix_clubs_is_active", "clubs", ["is_active"], unique=False)

    op.create_table(
        "club_members",
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", club_member_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("club_id", "user_id"),
    )
    op.create_index("ix_club_members_user_id", "club_members", ["user_id"], unique=False)
    op.create_index("ix_club_members_role", "club_members", ["role"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("posted_by", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("event_type", event_type, nullable=False),
        sa.Column("mode", event_mode, nullable=False),
        sa.Column("venue", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registration_link", sa.String(length=2048), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["posted_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_id"), "events", ["id"], unique=False)
    op.create_index("ix_events_club_id", "events", ["club_id"], unique=False)
    op.create_index("ix_events_start_date", "events", ["start_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_events_start_date", table_name="events")
    op.drop_index("ix_events_club_id", table_name="events")
    op.drop_index(op.f("ix_events_id"), table_name="events")
    op.drop_table("events")

    op.drop_index("ix_club_members_role", table_name="club_members")
    op.drop_index("ix_club_members_user_id", table_name="club_members")
    op.drop_table("club_members")

    op.drop_index("ix_clubs_is_active", table_name="clubs")
    op.drop_index(op.f("ix_clubs_name"), table_name="clubs")
    op.drop_index(op.f("ix_clubs_id"), table_name="clubs")
    op.drop_table("clubs")

    event_mode.drop(op.get_bind(), checkfirst=True)
    event_type.drop(op.get_bind(), checkfirst=True)
    club_member_role.drop(op.get_bind(), checkfirst=True)
