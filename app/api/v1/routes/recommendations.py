from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.match import RecommendationItem
from app.services import matching_service

router = APIRouter()


@router.get("/teams/{user_id}", response_model=list[RecommendationItem])
def get_recommended_teams(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[RecommendationItem]:
    return matching_service.get_recommended_teams(db, user_id)


@router.get("/users/{team_id}", response_model=list[RecommendationItem])
def get_recommended_users(
    team_id: int,
    db: Session = Depends(get_db),
) -> list[RecommendationItem]:
    return matching_service.get_recommended_users(db, team_id)
