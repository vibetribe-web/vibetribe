"""normalized matching schema

Revision ID: 20260516_0003
Revises: 20260516_0002
Create Date: 2026-05-16 19:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260516_0003"
down_revision: str | None = "20260516_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

team_member_role = postgresql.ENUM("leader", "member", name="team_member_role")


def upgrade() -> None:
    bind = op.get_bind()

    op.create_table(
        "colleges",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_colleges_id"), "colleges", ["id"], unique=False)
    op.create_index(op.f("ix_colleges_name"), "colleges", ["name"], unique=True)

    op.create_table(
        "branches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_branches_id"), "branches", ["id"], unique=False)
    op.create_index(op.f("ix_branches_name"), "branches", ["name"], unique=True)

    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_skills_id"), "skills", ["id"], unique=False)
    op.create_index(op.f("ix_skills_name"), "skills", ["name"], unique=True)

    op.add_column("users", sa.Column("college_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("branch_id", sa.Integer(), nullable=True))
    op.add_column(
        "users",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_users_college_id"), "users", ["college_id"], unique=False)
    op.create_index(op.f("ix_users_branch_id"), "users", ["branch_id"], unique=False)
    op.create_foreign_key(
        "fk_users_college_id_colleges",
        "users",
        "colleges",
        ["college_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_users_branch_id_branches",
        "users",
        "branches",
        ["branch_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "teams",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "teams",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_teams_leader_id", "teams", ["leader_id"], unique=False)

    op.create_table(
        "user_skills",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "skill_id"),
    )
    op.create_index("ix_user_skills_skill_id", "user_skills", ["skill_id"], unique=False)

    op.create_table(
        "team_required_skills",
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("team_id", "skill_id"),
    )
    op.create_index(
        "ix_team_required_skills_skill_id",
        "team_required_skills",
        ["skill_id"],
        unique=False,
    )

    op.create_table(
        "team_members",
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", team_member_role, nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("team_id", "user_id"),
    )
    op.create_index("ix_team_members_user_id", "team_members", ["user_id"], unique=False)

    op.add_column("join_requests", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("join_requests", sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_join_requests_team_status", "join_requests", ["team_id", "status"], unique=False)
    op.create_index("ix_join_requests_from_user_status", "join_requests", ["from_user_id", "status"], unique=False)
    op.create_index(
        "ux_pending_join_request",
        "join_requests",
        ["from_user_id", "team_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )

    bind.execute(sa.text("INSERT INTO colleges (name) SELECT DISTINCT college FROM users WHERE college IS NOT NULL AND college <> '' ON CONFLICT (name) DO NOTHING"))
    bind.execute(sa.text("INSERT INTO branches (name) SELECT DISTINCT branch FROM users WHERE branch IS NOT NULL AND branch <> '' ON CONFLICT (name) DO NOTHING"))
    bind.execute(sa.text("UPDATE users SET college_id = colleges.id FROM colleges WHERE users.college = colleges.name"))
    bind.execute(sa.text("UPDATE users SET branch_id = branches.id FROM branches WHERE users.branch = branches.name"))
    bind.execute(sa.text("INSERT INTO team_members (team_id, user_id, role) SELECT id, leader_id, 'leader'::team_member_role FROM teams ON CONFLICT DO NOTHING"))

    bind.execute(sa.text("""
        INSERT INTO skills (name)
        SELECT DISTINCT value
        FROM (
            SELECT jsonb_array_elements_text(skills) AS value FROM users WHERE skills IS NOT NULL
            UNION
            SELECT jsonb_array_elements_text(required_skills) AS value FROM teams WHERE required_skills IS NOT NULL
        ) skill_values
        WHERE value IS NOT NULL AND value <> ''
        ON CONFLICT (name) DO NOTHING
    """))
    bind.execute(sa.text("""
        INSERT INTO user_skills (user_id, skill_id)
        SELECT users.id, skills.id
        FROM users
        CROSS JOIN LATERAL jsonb_array_elements_text(users.skills) AS user_skill(name)
        JOIN skills ON skills.name = user_skill.name
        ON CONFLICT DO NOTHING
    """))
    bind.execute(sa.text("""
        INSERT INTO team_required_skills (team_id, skill_id)
        SELECT teams.id, skills.id
        FROM teams
        CROSS JOIN LATERAL jsonb_array_elements_text(teams.required_skills) AS team_skill(name)
        JOIN skills ON skills.name = team_skill.name
        ON CONFLICT DO NOTHING
    """))

    op.drop_index("ix_users_skills_gin", table_name="users", if_exists=True)
    op.drop_index("ix_teams_required_skills_gin", table_name="teams", if_exists=True)
    op.drop_column("users", "college")
    op.drop_column("users", "branch")
    op.drop_column("users", "skills")
    op.drop_column("teams", "required_skills")


def downgrade() -> None:
    op.add_column("teams", sa.Column("required_skills", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False))
    op.add_column("users", sa.Column("skills", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False))
    op.add_column("users", sa.Column("branch", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("college", sa.String(length=255), nullable=True))

    op.drop_index("ux_pending_join_request", table_name="join_requests")
    op.drop_index("ix_join_requests_from_user_status", table_name="join_requests")
    op.drop_index("ix_join_requests_team_status", table_name="join_requests")
    op.drop_column("join_requests", "responded_at")
    op.drop_column("join_requests", "created_at")

    op.drop_index("ix_team_members_user_id", table_name="team_members")
    op.drop_table("team_members")
    op.drop_index("ix_team_required_skills_skill_id", table_name="team_required_skills")
    op.drop_table("team_required_skills")
    op.drop_index("ix_user_skills_skill_id", table_name="user_skills")
    op.drop_table("user_skills")

    op.drop_index("ix_teams_leader_id", table_name="teams")
    op.drop_column("teams", "updated_at")
    op.drop_column("teams", "created_at")

    op.drop_constraint("fk_users_branch_id_branches", "users", type_="foreignkey")
    op.drop_constraint("fk_users_college_id_colleges", "users", type_="foreignkey")
    op.drop_index(op.f("ix_users_branch_id"), table_name="users")
    op.drop_index(op.f("ix_users_college_id"), table_name="users")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "created_at")
    op.drop_column("users", "branch_id")
    op.drop_column("users", "college_id")

    op.drop_index(op.f("ix_skills_name"), table_name="skills")
    op.drop_index(op.f("ix_skills_id"), table_name="skills")
    op.drop_table("skills")
    op.drop_index(op.f("ix_branches_name"), table_name="branches")
    op.drop_index(op.f("ix_branches_id"), table_name="branches")
    op.drop_table("branches")
    op.drop_index(op.f("ix_colleges_name"), table_name="colleges")
    op.drop_index(op.f("ix_colleges_id"), table_name="colleges")
    op.drop_table("colleges")
    team_member_role.drop(op.get_bind(), checkfirst=True)
