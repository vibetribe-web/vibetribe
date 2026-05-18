from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.associations import user_skills


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    username: Mapped[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_provider: Mapped[str] = mapped_column(String(40), default="email", nullable=False)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    college_id: Mapped[int | None] = mapped_column(
        ForeignKey("colleges.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    branch_id: Mapped[int | None] = mapped_column(
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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

    college_ref = relationship("College", back_populates="users")
    branch_ref = relationship("Branch", back_populates="users")
    skill_entities = relationship(
        "Skill",
        secondary=user_skills,
        back_populates="users",
    )
    teams_led = relationship(
        "Team",
        back_populates="leader",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    team_memberships = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    clubs_created = relationship(
        "Club",
        back_populates="creator",
        foreign_keys="Club.created_by",
    )
    club_memberships = relationship(
        "ClubMember",
        back_populates="user",
        foreign_keys="ClubMember.user_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    club_members_added = relationship(
        "ClubMember",
        back_populates="added_by_user",
        foreign_keys="ClubMember.added_by",
    )
    events_created = relationship(
        "Event",
        back_populates="creator",
        foreign_keys="Event.created_by",
    )
    join_requests = relationship(
        "JoinRequest",
        back_populates="from_user",
        cascade="all, delete-orphan",
        foreign_keys="JoinRequest.from_user_id",
        passive_deletes=True,
    )

    @property
    def college(self) -> str | None:
        return self.college_ref.name if self.college_ref else None

    @property
    def branch(self) -> str | None:
        return self.branch_ref.name if self.branch_ref else None

    @property
    def skills(self) -> list[str]:
        return [skill.name for skill in self.skill_entities]
