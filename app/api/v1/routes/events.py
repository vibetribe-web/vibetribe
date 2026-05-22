from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.event import EventDetailResponse, EventInterestResponse, EventPublicResponse, EventTeammateRecommendation
from app.services import event_service

router = APIRouter()


@router.get("/", response_model=list[EventPublicResponse])
def list_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EventPublicResponse]:
    return event_service.list_public_events(db, current_user)


@router.get("/{event_id}", response_model=EventDetailResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventPublicResponse:
    return event_service.get_public_event(db, event_id, current_user)


@router.get("/{event_id}/teammates", response_model=list[EventTeammateRecommendation])
def list_event_teammates(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EventTeammateRecommendation]:
    return event_service.list_event_teammates(db, event_id, current_user)


@router.post("/{event_id}/interest", response_model=EventInterestResponse, status_code=status.HTTP_201_CREATED)
def mark_event_interested(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventInterestResponse:
    return event_service.mark_interested(db, event_id, current_user)


@router.delete("/{event_id}/interest", response_model=EventInterestResponse)
def remove_event_interest(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventInterestResponse:
    return event_service.remove_interest(db, event_id, current_user)
