from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.request import RequestStatus
from app.models.team import Team
from app.models.team_member import TeamMember, TeamMemberRole
from app.models.user import User
from app.schemas.team import TeamCreate, TeamMemberRead, TeamUpdate, TeamWorkflowResponse
from app.services.taxonomy_service import get_or_create_skills


def create_team(db: Session, payload: TeamCreate, leader: User) -> TeamWorkflowResponse:
    team = Team(
        name=payload.name,
        description=payload.description,
        leader_id=leader.id,
        max_members=payload.max_members,
    )
    team.required_skill_entities = get_or_create_skills(db, payload.required_skills)
    team.memberships.append(
        TeamMember(user=leader, role=TeamMemberRole.leader),
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    return build_team_workflow_response(
        db,
        team,
        message="Team created successfully",
    )


def list_teams(db: Session) -> list[Team]:
    return list(db.scalars(select(Team).order_by(Team.id)))


def get_team(db: Session, team_id: int) -> Team:
    team = db.get(Team, team_id)
    if team is None:
        raise AppException("Team not found", status.HTTP_404_NOT_FOUND)
    return team


def get_member_count(db: Session, team_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(TeamMember)
            .where(TeamMember.team_id == team_id)
        )
        or 0
    )


def get_membership(db: Session, team_id: int, user_id: int) -> TeamMember | None:
    return db.get(TeamMember, {"team_id": team_id, "user_id": user_id})


def is_team_member(db: Session, team_id: int, user_id: int) -> bool:
    return get_membership(db, team_id, user_id) is not None


def ensure_team_leader(db: Session, team_id: int, user: User) -> TeamMember:
    membership = get_membership(db, team_id, user.id)
    if membership is None or membership.role != TeamMemberRole.leader:
        raise AppException("Only team leader can perform this action", status.HTTP_403_FORBIDDEN)
    return membership


def build_team_workflow_response(
    db: Session,
    team: Team,
    message: str,
    request_status: RequestStatus | None = None,
) -> TeamWorkflowResponse:
    return TeamWorkflowResponse(
        team_id=team.id,
        team_name=team.name,
        member_count=get_member_count(db, team.id),
        max_members=team.max_members,
        request_status=request_status,
        message=message,
    )


def list_my_teams(db: Session, user: User) -> list[TeamWorkflowResponse]:
    teams = list(
        db.scalars(
            select(Team)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .where(TeamMember.user_id == user.id)
            .order_by(Team.id)
        )
    )
    return [
        build_team_workflow_response(
            db,
            team,
            message="Team membership found",
        )
        for team in teams
    ]


def list_team_members(db: Session, team_id: int) -> list[TeamMemberRead]:
    get_team(db, team_id)
    memberships = list(
        db.scalars(
            select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .join(TeamMember.user)
            .order_by(TeamMember.role, User.name)
        )
    )
    return [
        TeamMemberRead(
            user_id=membership.user_id,
            name=membership.user.name,
            email=membership.user.email,
            role=membership.role,
            joined_at=membership.joined_at,
        )
        for membership in memberships
    ]


def update_team(db: Session, team_id: int, payload: TeamUpdate, user: User) -> Team:
    team = get_team(db, team_id)
    ensure_team_leader(db, team_id, user)

    values = payload.model_dump(exclude_unset=True)
    if "name" in values:
        team.name = values["name"]
    if "description" in values:
        team.description = values["description"]
    if "max_members" in values:
        team.max_members = values["max_members"]
    if "required_skills" in values:
        team.required_skill_entities = get_or_create_skills(db, values["required_skills"])
    db.add(team)
    db.commit()
    db.refresh(team)
    return team
