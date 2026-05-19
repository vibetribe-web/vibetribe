import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TeamMessageType(str, enum.Enum):
    text = "text"
    event_share = "event_share"


class TeamMessage(Base):
    __tablename__ = "team_messages"
    __table_args__ = (
        Index("ix_team_messages_team_id", "team_id"),
        Index("ix_team_messages_created_at", "created_at"),
        CheckConstraint(
            "(message_type <> 'text') OR (content IS NOT NULL AND length(trim(content)) > 0)",
            name="ck_team_messages_text_content_required",
        ),
        CheckConstraint(
            "(message_type <> 'event_share') OR (shared_event_id IS NOT NULL)",
            name="ck_team_messages_event_share_event_required",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_type: Mapped[TeamMessageType] = mapped_column(
        Enum(TeamMessageType, name="team_message_type"),
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    shared_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    team = relationship("Team", back_populates="messages")
    sender = relationship("User", back_populates="team_messages")
    event = relationship("Event", back_populates="team_messages")
