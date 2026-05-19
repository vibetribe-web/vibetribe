from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.event import EventPublicResponse
from app.schemas.user import UsernameUpdate, UsernameUpdateResponse, UserPublicResponse, UserRead, UserUpdate
from app.services import event_service, user_service

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_profile(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserRead)
def update_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    return user_service.update_profile(db, current_user, payload)


@router.patch("/me/username", response_model=UsernameUpdateResponse)
def update_username(
    payload: UsernameUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UsernameUpdateResponse:
    return user_service.update_username(db, current_user, payload)


@router.get("/me/interested-events", response_model=list[EventPublicResponse])
def list_my_interested_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EventPublicResponse]:
    return event_service.list_interested_events(db, current_user)


@router.get("/", response_model=list[UserPublicResponse])
def list_users(
    search: str | None = Query(default=None, max_length=120),
    db: Session = Depends(get_db),
) -> list[User]:
    return user_service.list_users(db, search)
