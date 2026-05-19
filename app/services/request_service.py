from datetime import datetime, timezone

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.request import JoinRequest, RequestStatus
from app.models.team_member import TeamMember, TeamMemberRole
from app.models.user import User
from app.schemas.request import JoinRequestCreate, JoinRequestRespond
from app.schemas.team import TeamWorkflowResponse
from app.services import team_service


def create_join_request(
    db: Session,
    payload: JoinRequestCreate,
    user: User,
) -> TeamWorkflowResponse:
    team = team_service.get_team(db, payload.team_id)
    if team_service.is_team_member(db, payload.team_id, user.id):
        raise AppException(
            "You are already a member of this team",
            status.HTTP_409_CONFLICT,
        )

    if team_service.get_member_count(db, payload.team_id) >= team.max_members:
        raise AppException("Team is already full", status.HTTP_400_BAD_REQUEST)

    existing_request = db.scalar(
        select(JoinRequest).where(
            JoinRequest.team_id == payload.team_id,
            JoinRequest.from_user_id == user.id,
            JoinRequest.status == RequestStatus.pending,
        )
    )
    if existing_request:
        raise AppException(
            "You already have a pending request for this team",
            status.HTTP_409_CONFLICT,
        )

    join_request = JoinRequest(
        from_user_id=user.id,
        team_id=payload.team_id,
        message=payload.message,
    )
    db.add(join_request)
    db.commit()
    db.refresh(join_request)
    return team_service.build_team_workflow_response(
        db,
        team,
        request_status=join_request.status,
        message="Join request sent successfully",
    )


def list_my_requests(db: Session, user: User) -> list[JoinRequest]:
    return list(
        db.scalars(
            select(JoinRequest)
            .where(JoinRequest.from_user_id == user.id)
            .order_by(JoinRequest.id.desc())
        )
    )


def list_team_requests(db: Session, team_id: int, user: User) -> list[JoinRequest]:
    team_service.get_team(db, team_id)
    team_service.ensure_team_leader(db, team_id, user)

    return list(
        db.scalars(
            select(JoinRequest)
            .where(JoinRequest.team_id == team_id)
            .order_by(JoinRequest.id.desc())
        )
    )


def respond_to_join_request(
    db: Session,
    request_id: int,
    payload: JoinRequestRespond,
    user: User,
) -> TeamWorkflowResponse:
    if payload.status == RequestStatus.pending:
        raise AppException(
            "Response status must be accepted or rejected",
            status.HTTP_400_BAD_REQUEST,
        )

    join_request = db.get(JoinRequest, request_id)
    if join_request is None:
        raise AppException("Request not found", status.HTTP_404_NOT_FOUND)
    team_service.ensure_team_leader(db, join_request.team_id, user)
    if join_request.status != RequestStatus.pending:
        raise AppException("Request has already been handled", status.HTTP_400_BAD_REQUEST)

    if payload.status == RequestStatus.accepted:
        membership = team_service.get_membership(
            db,
            join_request.team_id,
            join_request.from_user_id,
        )
        if membership is not None:
            raise AppException(
                "User is already a member of this team",
                status.HTTP_409_CONFLICT,
            )

        member_count = team_service.get_member_count(db, join_request.team_id)
        if member_count >= join_request.team.max_members:
            raise AppException("Team is already full", status.HTTP_400_BAD_REQUEST)

    join_request.status = payload.status
    join_request.reply_message = payload.reply_message
    join_request.responded_at = datetime.now(timezone.utc)
    if payload.status == RequestStatus.accepted:
        db.add(
            TeamMember(
                team_id=join_request.team_id,
                user_id=join_request.from_user_id,
                role=TeamMemberRole.member,
            )
        )
    db.add(join_request)
    db.commit()
    db.refresh(join_request)
    message = (
        "Join request accepted successfully"
        if join_request.status == RequestStatus.accepted
        else "Join request rejected successfully"
    )
    return team_service.build_team_workflow_response(
        db,
        join_request.team,
        request_status=join_request.status,
        message=message,
    )
