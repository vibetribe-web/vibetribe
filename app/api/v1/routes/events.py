from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.event import Event
from app.schemas.event import EventDetailResponse, EventPublicResponse
from app.services import event_service

router = APIRouter()


@router.get("/", response_model=list[EventPublicResponse])
def list_events(db: Session = Depends(get_db)) -> list[Event]:
    return event_service.list_public_events(db)


@router.get("/{event_id}", response_model=EventDetailResponse)
def get_event(event_id: int, db: Session = Depends(get_db)) -> Event:
    return event_service.get_public_event(db, event_id)
