from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.associations import team_required_skills


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (
        Index("ix_teams_leader_id", "leader_id"),
        CheckConstraint("max_members > 0", name="ck_teams_max_members_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    leader_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    max_members: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    leader = relationship("User", back_populates="teams_led")
    required_skill_entities = relationship(
        "Skill",
        secondary=team_required_skills,
        back_populates="teams",
    )
    memberships = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    join_requests = relationship(
        "JoinRequest",
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def required_skills(self) -> list[str]:
        return [skill.name for skill in self.required_skill_entities]

    @property
    def members(self) -> list["User"]:
        return [membership.user for membership in self.memberships]
