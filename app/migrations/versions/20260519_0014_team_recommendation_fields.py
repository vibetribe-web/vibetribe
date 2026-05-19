"""add team recommendation metadata

Revision ID: 20260519_0014
Revises: 20260519_0013
Create Date: 2026-05-19 18:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260519_0014"
down_revision: str | None = "20260519_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("teams", sa.Column("interests", sa.Text(), nullable=True))
    op.add_column("teams", sa.Column("preferred_roles", sa.Text(), nullable=True))
    op.add_column("teams", sa.Column("hackathon_category", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("teams", "hackathon_category")
    op.drop_column("teams", "preferred_roles")
    op.drop_column("teams", "interests")
