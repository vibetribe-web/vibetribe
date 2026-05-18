import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ClubMemberRole(str, enum.Enum):
    leader = "leader"
    member = "member"


class ClubMember(Base):
    __tablename__ = "club_members"
    __table_args__ = (
        Index("ix_club_members_user_id", "user_id"),
        Index("ix_club_members_role", "role"),
    )

    club_id: Mapped[int] = mapped_column(
        ForeignKey("clubs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[ClubMemberRole] = mapped_column(
        Enum(ClubMemberRole, name="club_member_role"),
        default=ClubMemberRole.member,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    added_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    club = relationship("Club", back_populates="members")
    user = relationship("User", back_populates="club_memberships", foreign_keys=[user_id])
    added_by_user = relationship("User", back_populates="club_members_added", foreign_keys=[added_by])
