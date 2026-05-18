from fastapi import status
from sqlalchemy import case, func, literal, select
from sqlalchemy.orm import Session, aliased

from app.core.exceptions import AppException
from app.models.associations import team_required_skills, user_skills
from app.models.request import JoinRequest, RequestStatus
from app.models.skill import Skill
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.match import RecommendationItem


def _round_score(value: float | None) -> float:
    return round(float(value or 0), 2)


def get_recommended_teams(db: Session, user_id: int) -> list[RecommendationItem]:
    if db.get(User, user_id) is None:
        raise AppException("User not found", status.HTTP_404_NOT_FOUND)

    required_counts = (
        select(
            team_required_skills.c.team_id.label("team_id"),
            func.count(team_required_skills.c.skill_id).label("required_count"),
        )
        .group_by(team_required_skills.c.team_id)
        .subquery()
    )

    matching_counts = (
        select(
            team_required_skills.c.team_id.label("team_id"),
            func.count(team_required_skills.c.skill_id).label("matching_count"),
        )
        .join(
            user_skills,
            (user_skills.c.skill_id == team_required_skills.c.skill_id)
            & (user_skills.c.user_id == user_id),
        )
        .group_by(team_required_skills.c.team_id)
        .subquery()
    )

    member_counts = (
        select(
            TeamMember.team_id.label("team_id"),
            func.count(TeamMember.user_id).label("member_count"),
        )
        .group_by(TeamMember.team_id)
        .subquery()
    )

    user_membership = aliased(TeamMember)
    pending_request = aliased(JoinRequest)

    required_count = func.coalesce(required_counts.c.required_count, 0)
    matching_count = func.coalesce(matching_counts.c.matching_count, 0)
    member_count = func.coalesce(member_counts.c.member_count, 0)

    skill_score = case(
        (required_count == 0, literal(0.0)),
        else_=(matching_count * 100.0) / required_count,
    )
    final_score = (
        skill_score
        + case((member_count < Team.max_members, literal(10.0)), else_=literal(0.0))
        + case((user_membership.user_id.is_(None), literal(10.0)), else_=literal(0.0))
        + case((pending_request.id.is_(None), literal(10.0)), else_=literal(0.0))
    )

    rows = db.execute(
        select(
            Team.id.label("id"),
            Team.name.label("name"),
            final_score.label("score"),
        )
        .select_from(Team)
        .outerjoin(required_counts, required_counts.c.team_id == Team.id)
        .outerjoin(matching_counts, matching_counts.c.team_id == Team.id)
        .outerjoin(member_counts, member_counts.c.team_id == Team.id)
        .outerjoin(
            user_membership,
            (user_membership.team_id == Team.id) & (user_membership.user_id == user_id),
        )
        .outerjoin(
            pending_request,
            (pending_request.team_id == Team.id)
            & (pending_request.from_user_id == user_id)
            & (pending_request.status == RequestStatus.pending),
        )
        .order_by(final_score.desc(), Team.id.asc())
        .limit(10)
    ).all()

    team_ids = [row.id for row in rows]
    matching_skills = _get_matching_skills_by_team(db, user_id, team_ids)

    return [
        RecommendationItem(
            id=row.id,
            name=row.name,
            score=_round_score(row.score),
            matching_skills=matching_skills.get(row.id, []),
        )
        for row in rows
    ]


def get_recommended_users(db: Session, team_id: int) -> list[RecommendationItem]:
    if db.get(Team, team_id) is None:
        raise AppException("Team not found", status.HTTP_404_NOT_FOUND)

    required_counts = (
        select(
            team_required_skills.c.team_id.label("team_id"),
            func.count(team_required_skills.c.skill_id).label("required_count"),
        )
        .where(team_required_skills.c.team_id == team_id)
        .group_by(team_required_skills.c.team_id)
        .subquery()
    )

    matching_counts = (
        select(
            user_skills.c.user_id.label("user_id"),
            func.count(user_skills.c.skill_id).label("matching_count"),
        )
        .join(
            team_required_skills,
            (team_required_skills.c.skill_id == user_skills.c.skill_id)
            & (team_required_skills.c.team_id == team_id),
        )
        .group_by(user_skills.c.user_id)
        .subquery()
    )

    user_membership = aliased(TeamMember)
    pending_request = aliased(JoinRequest)

    required_count = func.coalesce(required_counts.c.required_count, 0)
    matching_count = func.coalesce(matching_counts.c.matching_count, 0)

    skill_score = case(
        (required_count == 0, literal(0.0)),
        else_=(matching_count * 100.0) / required_count,
    )
    final_score = (
        skill_score
        + case((user_membership.user_id.is_(None), literal(10.0)), else_=literal(0.0))
        + case((pending_request.id.is_(None), literal(10.0)), else_=literal(0.0))
    )

    rows = db.execute(
        select(
            User.id.label("id"),
            User.name.label("name"),
            final_score.label("score"),
        )
        .select_from(User)
        .outerjoin(required_counts, required_counts.c.team_id == team_id)
        .outerjoin(matching_counts, matching_counts.c.user_id == User.id)
        .outerjoin(
            user_membership,
            (user_membership.team_id == team_id) & (user_membership.user_id == User.id),
        )
        .outerjoin(
            pending_request,
            (pending_request.team_id == team_id)
            & (pending_request.from_user_id == User.id)
            & (pending_request.status == RequestStatus.pending),
        )
        .order_by(final_score.desc(), User.id.asc())
        .limit(10)
    ).all()

    user_ids = [row.id for row in rows]
    matching_skills = _get_matching_skills_by_user(db, team_id, user_ids)

    return [
        RecommendationItem(
            id=row.id,
            name=row.name,
            score=_round_score(row.score),
            matching_skills=matching_skills.get(row.id, []),
        )
        for row in rows
    ]


def _get_matching_skills_by_team(
    db: Session,
    user_id: int,
    team_ids: list[int],
) -> dict[int, list[str]]:
    if not team_ids:
        return {}

    rows = db.execute(
        select(team_required_skills.c.team_id, Skill.name)
        .select_from(team_required_skills)
        .join(Skill, Skill.id == team_required_skills.c.skill_id)
        .join(
            user_skills,
            (user_skills.c.skill_id == team_required_skills.c.skill_id)
            & (user_skills.c.user_id == user_id),
        )
        .where(team_required_skills.c.team_id.in_(team_ids))
        .order_by(team_required_skills.c.team_id, Skill.name)
    ).all()

    skills_by_team: dict[int, list[str]] = {team_id: [] for team_id in team_ids}
    for team_id, skill_name in rows:
        skills_by_team[team_id].append(skill_name)
    return skills_by_team


def _get_matching_skills_by_user(
    db: Session,
    team_id: int,
    user_ids: list[int],
) -> dict[int, list[str]]:
    if not user_ids:
        return {}

    rows = db.execute(
        select(user_skills.c.user_id, Skill.name)
        .select_from(user_skills)
        .join(Skill, Skill.id == user_skills.c.skill_id)
        .join(
            team_required_skills,
            (team_required_skills.c.skill_id == user_skills.c.skill_id)
            & (team_required_skills.c.team_id == team_id),
        )
        .where(user_skills.c.user_id.in_(user_ids))
        .order_by(user_skills.c.user_id, Skill.name)
    ).all()

    skills_by_user: dict[int, list[str]] = {user_id: [] for user_id in user_ids}
    for user_id, skill_name in rows:
        skills_by_user[user_id].append(skill_name)
    return skills_by_user


def recommend_teams(db: Session, user: User) -> list[RecommendationItem]:
    return get_recommended_teams(db, user.id)
