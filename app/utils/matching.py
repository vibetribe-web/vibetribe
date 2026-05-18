from dataclasses import dataclass


@dataclass(frozen=True)
class MatchScore:
    score: float
    skill_score: float
    branch_year_score: float
    college_score: float
    matched_skills: list[str]
    missing_skills: list[str]


def normalize_skills(skills: list[str] | None) -> set[str]:
    return {
        skill.strip().lower()
        for skill in (skills or [])
        if skill and skill.strip()
    }


def calculate_team_match_score(
    user_skills: list[str] | None,
    team_required_skills: list[str] | None,
    user_branch: str | None = None,
    leader_branch: str | None = None,
    user_year: int | None = None,
    leader_year: int | None = None,
    user_college: str | None = None,
    leader_college: str | None = None,
) -> MatchScore:
    user_skill_set = normalize_skills(user_skills)
    required_skill_set = normalize_skills(team_required_skills)

    matched_skill_set = user_skill_set & required_skill_set
    missing_skill_set = required_skill_set - user_skill_set

    skill_score = 0.0
    if required_skill_set:
        skill_score = len(matched_skill_set) / len(required_skill_set)

    branch_year_score = 0.0
    if user_branch and leader_branch:
        if user_branch.strip().lower() == leader_branch.strip().lower():
            branch_year_score += 0.5
    if user_year and leader_year and user_year == leader_year:
        branch_year_score += 0.5

    college_score = 0.0
    if user_college and leader_college:
        if user_college.strip().lower() == leader_college.strip().lower():
            college_score = 1.0

    final_score = (
        skill_score * 0.75
        + branch_year_score * 0.15
        + college_score * 0.10
    )

    return MatchScore(
        score=round(min(final_score * 100, 100), 2),
        skill_score=round(skill_score * 100, 2),
        branch_year_score=round(branch_year_score * 100, 2),
        college_score=round(college_score * 100, 2),
        matched_skills=sorted(matched_skill_set),
        missing_skills=sorted(missing_skill_set),
    )
