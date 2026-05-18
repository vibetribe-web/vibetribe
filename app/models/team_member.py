import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TeamMemberRole(str, enum.Enum):
    leader = "leader"
    member = "member"


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        Index("ix_team_members_user_id", "user_id"),
    )

    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[TeamMemberRole] = mapped_column(
        Enum(TeamMemberRole, name="team_member_role"),
        default=TeamMemberRole.member,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    team = relationship("Team", back_populates="memberships")
    user = relationship("User", back_populates="team_memberships")
