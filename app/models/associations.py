from sqlalchemy import Column, ForeignKey, Index, Integer, Table

from app.db.base import Base

user_skills = Table(
    "user_skills",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "skill_id",
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("ix_user_skills_skill_id", "skill_id"),
)

team_required_skills = Table(
    "team_required_skills",
    Base.metadata,
    Column(
        "team_id",
        Integer,
        ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "skill_id",
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Index("ix_team_required_skills_skill_id", "skill_id"),
)
