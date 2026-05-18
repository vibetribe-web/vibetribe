from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.match import RecommendationItem
from app.services import matching_service

router = APIRouter()


@router.get("/recommendations", response_model=list[RecommendationItem])
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RecommendationItem]:
    return matching_service.recommend_teams(db, current_user)
