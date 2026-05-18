from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppException
from app.models.club import Club
from app.models.event import Event
from app.models.user import User
from app.schemas.event import EventCreate, EventUpdate
from app.services import club_service


def _url_to_string(value: object) -> str | None:
    return str(value) if value is not None else None


def _validate_event_dates(start_date, end_date) -> None:
    if end_date < start_date:
        raise AppException("end_date must be greater than or equal to start_date", status.HTTP_422_UNPROCESSABLE_ENTITY)


def get_event(db: Session, event_id: int) -> Event:
    event = db.scalar(
        select(Event)
        .options(joinedload(Event.club))
        .where(Event.id == event_id)
    )
    if event is None:
        raise AppException("Event not found", status.HTTP_404_NOT_FOUND)
    return event


def get_public_event(db: Session, event_id: int) -> Event:
    event = db.scalar(
        select(Event)
        .join(Club)
        .options(joinedload(Event.club))
        .where(Event.id == event_id, Club.is_active.is_(True))
    )
    if event is None:
        raise AppException("Event not found", status.HTTP_404_NOT_FOUND)
    return event


def create_event(db: Session, club_id: int, payload: EventCreate, user: User) -> Event:
    club = club_service.get_active_club(db, club_id)
    club_service.ensure_club_member(db, club.id, user)
    event = Event(
        club_id=club.id,
        created_by=user.id,
        title=payload.title,
        description=payload.description,
        event_type=payload.event_type,
        mode=payload.mode,
        venue=payload.venue,
        start_date=payload.start_date,
        end_date=payload.end_date,
        registration_link=_url_to_string(payload.registration_link),
        image_url=_url_to_string(payload.image_url),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def _ensure_event_permission(db: Session, event: Event, club_id: int, user: User) -> None:
    if event.club_id != club_id:
        raise AppException("Event not found for this club", status.HTTP_404_NOT_FOUND)
    if user.is_admin:
        return
    if club_service.is_club_leader(db, club_id, user.id):
        return
    if event.created_by == user.id and club_service.is_club_member(db, club_id, user.id):
        return
    raise AppException("Only club leaders, event owners, or admins can perform this action", status.HTTP_403_FORBIDDEN)


def update_event(
    db: Session,
    club_id: int,
    event_id: int,
    payload: EventUpdate,
    user: User,
) -> Event:
    club_service.get_active_club(db, club_id)
    event = get_event(db, event_id)
    _ensure_event_permission(db, event, club_id, user)

    values = payload.model_dump(exclude_unset=True)
    start_date = values.get("start_date", event.start_date)
    end_date = values.get("end_date", event.end_date)
    _validate_event_dates(start_date, end_date)

    for field, value in values.items():
        if field in {"registration_link", "image_url"}:
            setattr(event, field, _url_to_string(value))
        else:
            setattr(event, field, value)

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, club_id: int, event_id: int, user: User) -> None:
    event = get_event(db, event_id)
    _ensure_event_permission(db, event, club_id, user)
    db.delete(event)
    db.commit()


def list_public_events(db: Session) -> list[Event]:
    return list(
        db.scalars(
            select(Event)
            .join(Club)
            .where(Club.is_active.is_(True))
            .order_by(Event.start_date, Event.id)
        )
    )


def list_club_events(db: Session, club_id: int) -> list[Event]:
    club = club_service.get_active_club(db, club_id)
    return list(
        db.scalars(
            select(Event)
            .where(Event.club_id == club.id)
            .order_by(Event.start_date, Event.id)
        )
    )
