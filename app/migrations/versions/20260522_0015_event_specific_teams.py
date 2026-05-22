"""add event specific teams

Revision ID: 20260522_0015
Revises: 20260519_0014
Create Date: 2026-05-22 16:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260522_0015"
down_revision = "20260519_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("teams", sa.Column("event_id", sa.Integer(), nullable=True))
    op.create_index("ix_teams_event_id", "teams", ["event_id"], unique=False)
    op.create_foreign_key(
        "fk_teams_event_id_events",
        "teams",
        "events",
        ["event_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_teams_event_id_events", "teams", type_="foreignkey")
    op.drop_index("ix_teams_event_id", table_name="teams")
    op.drop_column("teams", "event_id")
