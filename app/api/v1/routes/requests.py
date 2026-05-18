from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.request import JoinRequest
from app.models.user import User
from app.schemas.request import JoinRequestCreate, JoinRequestRead, JoinRequestRespond
from app.schemas.team import TeamWorkflowResponse
from app.services import request_service

router = APIRouter()


@router.post("/", response_model=TeamWorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_join_request(
    payload: JoinRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamWorkflowResponse:
    return request_service.create_join_request(db, payload, current_user)


@router.get("/me", response_model=list[JoinRequestRead])
def list_my_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[JoinRequest]:
    return request_service.list_my_requests(db, current_user)


@router.get("/team/{team_id}", response_model=list[JoinRequestRead])
def list_team_requests(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[JoinRequest]:
    return request_service.list_team_requests(db, team_id, current_user)


@router.patch("/{request_id}/respond", response_model=TeamWorkflowResponse)
def respond_to_join_request(
    request_id: int,
    payload: JoinRequestRespond,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamWorkflowResponse:
    return request_service.respond_to_join_request(db, request_id, payload, current_user)
