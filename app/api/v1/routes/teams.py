from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.team import Team
from app.models.user import User
from app.schemas.request import JoinRequestRead
from app.schemas.team import (
    TeamCreate,
    TeamDetail,
    TeamMemberRead,
    TeamRead,
    TeamUpdate,
    TeamWorkflowResponse,
)
from app.schemas.team_message import TeamEventShareCreate, TeamMessageCreate, TeamMessageRead
from app.services import request_service, team_message_service, team_service

router = APIRouter()


@router.post("/", response_model=TeamWorkflowResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamWorkflowResponse:
    return team_service.create_team(db, payload, current_user)


@router.get("/", response_model=list[TeamRead])
def list_teams(db: Session = Depends(get_db)) -> list[Team]:
    return team_service.list_teams(db)


@router.get("/my-teams", response_model=list[TeamWorkflowResponse])
def list_my_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TeamWorkflowResponse]:
    return team_service.list_my_teams(db, current_user)


@router.get("/{team_id}", response_model=TeamDetail)
def get_team(team_id: int, db: Session = Depends(get_db)) -> Team:
    return team_service.get_team(db, team_id)


@router.get("/{team_id}/members", response_model=list[TeamMemberRead])
def list_team_members(
    team_id: int,
    db: Session = Depends(get_db),
) -> list[TeamMemberRead]:
    return team_service.list_team_members(db, team_id)


@router.get("/{team_id}/messages", response_model=list[TeamMessageRead])
def list_team_messages(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TeamMessageRead]:
    return team_message_service.list_messages(db, team_id, current_user)


@router.post("/{team_id}/messages", response_model=TeamMessageRead, status_code=status.HTTP_201_CREATED)
def create_team_message(
    team_id: int,
    payload: TeamMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamMessageRead:
    return team_message_service.create_text_message(db, team_id, payload, current_user)


@router.post("/{team_id}/share-event", response_model=TeamMessageRead, status_code=status.HTTP_201_CREATED)
def share_event_to_team(
    team_id: int,
    payload: TeamEventShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TeamMessageRead:
    return team_message_service.share_event(db, team_id, payload, current_user)


@router.get("/{team_id}/requests", response_model=list[JoinRequestRead])
def list_team_requests(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[JoinRequestRead]:
    return request_service.list_team_requests(db, team_id, current_user)


@router.patch("/{team_id}", response_model=TeamRead)
def update_team(
    team_id: int,
    payload: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Team:
    return team_service.update_team(db, team_id, payload, current_user)
