from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.event import Event
from app.models.event_interest import EventInterest
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.user import User
from app.schemas.match import RecommendedTeamMember, RecommendedTeamResponse
from app.services import team_service


def get_recommended_teams(db: Session, user: User, limit: int = 5) -> list[RecommendedTeamResponse]:
    user_skill_names = {skill.name.lower() for skill in user.skill_entities}
    pending_team_ids = team_service.get_pending_request_team_ids(db, user.id)
    user_event_ids, user_club_ids = get_user_interest_context(db, user.id)

    teams = list(
        db.scalars(
            select(Team)
            .options(
                selectinload(Team.required_skill_entities),
                selectinload(Team.memberships)
                .selectinload(TeamMember.user)
                .selectinload(User.skill_entities),
            )
            .order_by(Team.id)
        )
    )
    team_interest_context = get_team_interest_contexts(db, teams)

    recommendations = []
    for team in teams:
        member_count = len(team.memberships)
        open_slots = max(team.max_members - member_count, 0)
        if any(membership.user_id == user.id for membership in team.memberships):
            continue
        if team.id in pending_team_ids:
            continue
        if open_slots <= 0:
            continue

        score, reasons, reason_tags = score_team(
            db,
            team,
            user,
            user_skill_names,
            user_event_ids,
            user_club_ids,
            team_interest_context.get(team.id, (set(), set())),
            open_slots,
        )
        if score <= 0:
            continue

        recommendations.append(
            RecommendedTeamResponse(
                team_id=team.id,
                team_name=team.name,
                match_score=min(score, 100),
                open_slots=open_slots,
                required_skills=team.required_skills,
                reasons=reasons,
                reason_tags=reason_tags,
                members=[
                    RecommendedTeamMember(
                        name=membership.user.name,
                        username=membership.user.username,
                    )
                    for membership in team.memberships[:4]
                ],
            )
        )

    return sorted(
        recommendations,
        key=lambda recommendation: (-recommendation.match_score, recommendation.team_name.lower()),
    )[:limit]


def score_team(
    db: Session,
    team: Team,
    user: User,
    user_skill_names: set[str],
    user_event_ids: set[int],
    user_club_ids: set[int],
    team_interest_context: tuple[set[int], set[int]],
    open_slots: int,
) -> tuple[int, list[str], list[str]]:
    score = 0
    reasons: list[str] = []
    reason_tags: list[str] = []

    required_skills = {skill.name.lower(): skill.name for skill in team.required_skill_entities}
    matching_required_skills = sorted(
        required_skills[skill]
        for skill in user_skill_names
        if skill in required_skills
    )
    if matching_required_skills:
        score += 40
        reasons.append(f"Needs {', '.join(matching_required_skills[:3])}")
        reason_tags.append("Same Skill")

    team_event_ids, team_club_ids = team_interest_context
    same_events = user_event_ids & team_event_ids
    if same_events:
        score += 25
        reasons.append("Interested in the same hackathon/event")
        reason_tags.append("AI Interest")

    if user_club_ids & team_club_ids:
        score += 15
        reasons.append("Connected through the same club events")
        reason_tags.append("Same Club")

    member_users = [membership.user for membership in team.memberships]
    if user.branch_id and any(member.branch_id == user.branch_id for member in member_users):
        score += 10
        reasons.append("Same branch")
        reason_tags.append("Same Branch")

    if user.year and any(member.year == user.year for member in member_users):
        score += 5
        reasons.append("Same year")
        reason_tags.append("Same Year")

    if user.college_id and any(member.college_id == user.college_id for member in member_users):
        score += 5
        reasons.append("Same college")
        reason_tags.append("Same College")

    if open_slots > 0:
        score += 20
        reasons.append(f"{open_slots} open slot{'s' if open_slots != 1 else ''}")

    team_stack = {
        skill.name.lower()
        for member in member_users
        for skill in member.skill_entities
    }
    missing_user_skills = sorted(skill for skill in user_skill_names if skill not in team_stack)
    if missing_user_skills:
        score += 15
        skill_label = missing_user_skills[0].replace("_", " ").title()
        reasons.append(f"Your {skill_label} skill is missing in this team")
        reason_tags.append(f"Needs {skill_label}")

    if team.hackathon_category:
        user_interest_terms = {interest.lower() for interest in team.interest_list}
        if team.hackathon_category.lower() in user_interest_terms:
            score += 5

    return score, dedupe(reasons), dedupe(reason_tags)


def get_user_interest_context(db: Session, user_id: int) -> tuple[set[int], set[int]]:
    rows = db.execute(
        select(EventInterest.event_id, Event.club_id)
        .join(Event, Event.id == EventInterest.event_id)
        .where(EventInterest.user_id == user_id)
    ).all()
    return {event_id for event_id, _club_id in rows}, {club_id for _event_id, club_id in rows}


def get_team_interest_contexts(db: Session, teams: list[Team]) -> dict[int, tuple[set[int], set[int]]]:
    team_ids = [team.id for team in teams]
    if not team_ids:
        return {}
    rows = db.execute(
        select(TeamMember.team_id, EventInterest.event_id, Event.club_id)
        .join(EventInterest, EventInterest.user_id == TeamMember.user_id)
        .join(Event, Event.id == EventInterest.event_id)
        .where(TeamMember.team_id.in_(team_ids))
    ).all()
    context: dict[int, tuple[set[int], set[int]]] = {
        team_id: (set(), set()) for team_id in team_ids
    }
    for team_id, event_id, club_id in rows:
        context[team_id][0].add(event_id)
        context[team_id][1].add(club_id)
    return context


def dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result
