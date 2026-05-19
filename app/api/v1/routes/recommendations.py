from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.match import RecommendationItem, RecommendedTeamResponse
from app.services import matching_service, team_recommendation_service

router = APIRouter()


@router.get("/teams/{user_id}", response_model=list[RecommendationItem])
def get_recommended_teams(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[RecommendationItem]:
    return matching_service.get_recommended_teams(db, user_id)


@router.get("/teams", response_model=list[RecommendedTeamResponse])
def get_my_recommended_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RecommendedTeamResponse]:
    return team_recommendation_service.get_recommended_teams(db, current_user)


@router.get("/users/{team_id}", response_model=list[RecommendationItem])
def get_recommended_users(
    team_id: int,
    db: Session = Depends(get_db),
) -> list[RecommendationItem]:
    return matching_service.get_recommended_users(db, team_id)
