from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.associations import team_required_skills, user_skills


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)

    users = relationship(
        "User",
        secondary=user_skills,
        back_populates="skill_entities",
    )
    teams = relationship(
        "Team",
        secondary=team_required_skills,
        back_populates="required_skill_entities",
    )
