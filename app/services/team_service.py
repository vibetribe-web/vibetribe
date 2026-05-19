from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppException
from app.models.request import JoinRequest, RequestStatus
from app.models.team import Team
from app.models.team_member import TeamMember, TeamMemberRole
from app.models.user import User
from app.schemas.team import TeamCreate, TeamDetail, TeamMemberRead, TeamRead, TeamUpdate, TeamWorkflowResponse
from app.services.taxonomy_service import get_or_create_skills


def create_team(db: Session, payload: TeamCreate, leader: User) -> TeamWorkflowResponse:
    team = Team(
        name=payload.name,
        description=payload.description,
        interests=join_text_list(payload.interests),
        preferred_roles=join_text_list(payload.preferred_roles),
        hackathon_category=payload.hackathon_category,
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


def list_teams(db: Session, user: User) -> list[TeamRead]:
    teams = list(
        db.scalars(
            select(Team)
            .options(
                selectinload(Team.leader),
                selectinload(Team.memberships).selectinload(TeamMember.user),
                selectinload(Team.required_skill_entities),
            )
            .order_by(Team.id)
        )
    )
    pending_team_ids = get_pending_request_team_ids(db, user.id)
    return [build_team_response(team, user, pending_team_ids) for team in teams]


def get_team(db: Session, team_id: int) -> Team:
    team = db.get(Team, team_id)
    if team is None:
        raise AppException("Team not found", status.HTTP_404_NOT_FOUND)
    return team


def get_team_detail(db: Session, team_id: int, user: User) -> TeamDetail:
    team = db.scalar(
        select(Team)
        .where(Team.id == team_id)
        .options(
            selectinload(Team.leader),
            selectinload(Team.memberships).selectinload(TeamMember.user),
            selectinload(Team.required_skill_entities),
        )
    )
    if team is None:
        raise AppException("Team not found", status.HTTP_404_NOT_FOUND)
    pending_team_ids = get_pending_request_team_ids(db, user.id)
    return TeamDetail.model_validate(build_team_response(team, user, pending_team_ids))


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


def get_pending_request_team_ids(db: Session, user_id: int) -> set[int]:
    return set(
        db.scalars(
            select(JoinRequest.team_id).where(
                JoinRequest.from_user_id == user_id,
                JoinRequest.status == RequestStatus.pending,
            )
        )
    )


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


def build_team_member_read(membership: TeamMember) -> TeamMemberRead:
    return TeamMemberRead(
        user_id=membership.user_id,
        name=membership.user.name,
        email=membership.user.email,
        username=membership.user.username,
        profile_image_url=membership.user.profile_image_url,
        role=membership.role,
        joined_at=membership.joined_at,
    )


def build_team_response(team: Team, user: User, pending_team_ids: set[int]) -> TeamRead:
    members = [
        build_team_member_read(membership)
        for membership in sorted(
            team.memberships,
            key=lambda membership: (
                0 if membership.role == TeamMemberRole.leader else 1,
                membership.user.name.lower(),
            ),
        )
    ]
    current_members_count = len(members)
    is_current_user_leader = team.leader_id == user.id
    is_current_user_member = any(member.user_id == user.id for member in members)
    return TeamRead(
        id=team.id,
        name=team.name,
        description=team.description,
        required_skills=team.required_skills,
        interests=team.interest_list,
        preferred_roles=team.preferred_role_list,
        hackathon_category=team.hackathon_category,
        max_members=team.max_members,
        leader_id=team.leader_id,
        leader=team.leader,
        current_members_count=current_members_count,
        available_slots=max(team.max_members - current_members_count, 0),
        members=members,
        is_current_user_member=is_current_user_member,
        is_current_user_leader=is_current_user_leader,
        has_pending_request=team.id in pending_team_ids,
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
    return [build_team_member_read(membership) for membership in memberships]


def update_team(db: Session, team_id: int, payload: TeamUpdate, user: User) -> TeamRead:
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
    if "interests" in values:
        team.interests = join_text_list(values["interests"])
    if "preferred_roles" in values:
        team.preferred_roles = join_text_list(values["preferred_roles"])
    if "hackathon_category" in values:
        team.hackathon_category = values["hackathon_category"]
    db.add(team)
    db.commit()
    pending_team_ids = get_pending_request_team_ids(db, user.id)
    refreshed_team = db.scalar(
        select(Team)
        .where(Team.id == team.id)
        .options(
            selectinload(Team.leader),
            selectinload(Team.memberships).selectinload(TeamMember.user),
            selectinload(Team.required_skill_entities),
        )
    )
    if refreshed_team is None:
        raise AppException("Team not found", status.HTTP_404_NOT_FOUND)
    return build_team_response(refreshed_team, user, pending_team_ids)


def join_text_list(values: list[str] | None) -> str | None:
    return ", ".join(values) if values else None
