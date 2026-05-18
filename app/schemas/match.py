from pydantic import BaseModel, ConfigDict

from app.schemas.team import TeamRead


class RecommendationItem(BaseModel):
    id: int
    name: str
    score: float
    matching_skills: list[str]


class MatchBreakdown(BaseModel):
    skill_score: float
    branch_year_score: float
    college_score: float


class TeamRecommendation(BaseModel):
    team: TeamRead
    score: float
    matched_skills: list[str]
    missing_skills: list[str]
    breakdown: MatchBreakdown

    model_config = ConfigDict(from_attributes=True)
