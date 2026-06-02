import hmac

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.exceptions import AppException
from app.models.request import JoinRequest, RequestStatus
from app.models.team import Team
from app.models.user import User
from app.schemas.admin import AdminBootstrapCreate, AdminBootstrapResponse, AdminDashboard


def _admin_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User).where(User.is_admin.is_(True))) or 0


def bootstrap_admin(
    db: Session,
    payload: AdminBootstrapCreate,
) -> AdminBootstrapResponse:
    configured_key = settings.admin_setup_key
    if not configured_key:
        raise AppException("ADMIN_SETUP_KEY is not configured", status.HTTP_500_INTERNAL_SERVER_ERROR)
    if not hmac.compare_digest(payload.admin_setup_key, configured_key):
        raise AppException("Invalid admin setup key", status.HTTP_403_FORBIDDEN)

    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None:
        raise AppException("Registered user not found", status.HTTP_404_NOT_FOUND)

    message = "User is already an admin" if user.is_admin else "User promoted to admin successfully"
    user.is_admin = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return AdminBootstrapResponse(
        user=user,
        message=message,
    )


def get_dashboard(db: Session) -> AdminDashboard:
    users_count = db.scalar(select(func.count()).select_from(User)) or 0
    teams_count = db.scalar(select(func.count()).select_from(Team)) or 0
    requests_count = db.scalar(select(func.count()).select_from(JoinRequest)) or 0
    pending_requests_count = (
        db.scalar(
            select(func.count())
            .select_from(JoinRequest)
            .where(JoinRequest.status == RequestStatus.pending)
        )
        or 0
    )
    return AdminDashboard(
        users_count=users_count,
        teams_count=teams_count,
        requests_count=requests_count,
        pending_requests_count=pending_requests_count,
    )


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


def list_teams(db: Session) -> list[Team]:
    return list(db.scalars(select(Team).order_by(Team.id)))


def list_requests(db: Session) -> list[JoinRequest]:
    return list(
        db.scalars(
            select(JoinRequest)
            .options(
                joinedload(JoinRequest.team).load_only(Team.id, Team.name),
                joinedload(JoinRequest.from_user).load_only(User.id, User.username, User.name),
            )
            .order_by(JoinRequest.id.desc())
        )
    )


def update_admin_status(db: Session, user_id: int, is_admin: bool, acting_user: User) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise AppException("User not found", status.HTTP_404_NOT_FOUND)
    if user.id == acting_user.id and not is_admin:
        raise AppException("You cannot remove your own admin access", status.HTTP_400_BAD_REQUEST)

    user.is_admin = is_admin
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
