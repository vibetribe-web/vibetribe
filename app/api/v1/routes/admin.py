from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.database import get_db
from app.models.request import JoinRequest
from app.models.team import Team
from app.models.user import User
from app.schemas.admin import (
    AdminBootstrapCreate,
    AdminBootstrapResponse,
    AdminDashboard,
    AdminStatusUpdate,
)
from app.schemas.club import (
    ClubAdminResponse,
    ClubCreate,
    ClubLeaderAssignmentResponse,
    ClubUpdate,
)
from app.schemas.request import JoinRequestRead
from app.schemas.team import TeamRead
from app.schemas.user import UserRead
from app.services import admin_service, club_service

router = APIRouter()


@router.post(
    "/bootstrap",
    response_model=AdminBootstrapResponse,
    status_code=status.HTTP_201_CREATED,
)
def bootstrap_admin(
    payload: AdminBootstrapCreate,
    db: Session = Depends(get_db),
) -> AdminBootstrapResponse:
    return admin_service.bootstrap_admin(db, payload)


@router.get("/dashboard", response_model=AdminDashboard)
def get_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> AdminDashboard:
    return admin_service.get_dashboard(db)


@router.get("/users", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[User]:
    return admin_service.list_users(db)


@router.patch("/users/{user_id}/admin-status", response_model=UserRead)
def update_admin_status(
    user_id: int,
    payload: AdminStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> User:
    return admin_service.update_admin_status(db, user_id, payload.is_admin, admin)


@router.get("/teams", response_model=list[TeamRead])
def list_teams(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[Team]:
    return admin_service.list_teams(db)


@router.get("/requests", response_model=list[JoinRequestRead])
def list_requests(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[JoinRequest]:
    return admin_service.list_requests(db)


@router.post("/clubs", response_model=ClubAdminResponse, status_code=status.HTTP_201_CREATED)
def create_club(
    payload: ClubCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ClubAdminResponse:
    return club_service.create_club(db, payload, admin)


@router.put("/clubs/{club_id}", response_model=ClubAdminResponse)
def update_club(
    club_id: int,
    payload: ClubUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ClubAdminResponse:
    return club_service.update_club(db, club_id, payload)


@router.delete("/clubs/{club_id}", response_model=ClubAdminResponse)
def deactivate_club(
    club_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ClubAdminResponse:
    return club_service.deactivate_club(db, club_id)


@router.post(
    "/clubs/{club_id}/leaders/{user_id}",
    response_model=ClubLeaderAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_club_leader(
    club_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ClubLeaderAssignmentResponse:
    return club_service.assign_leader(db, club_id, user_id, admin)


@router.delete(
    "/clubs/{club_id}/leaders/{user_id}",
    response_model=ClubLeaderAssignmentResponse,
)
def remove_club_leader(
    club_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ClubLeaderAssignmentResponse:
    return club_service.remove_leader(db, club_id, user_id)


@router.get("/clubs", response_model=list[ClubAdminResponse])
def list_clubs(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> list[ClubAdminResponse]:
    return club_service.list_admin_clubs(db)
