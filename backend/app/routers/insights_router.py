from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db
from app.services.insight_service import insight_service

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("", response_model=List[schemas.AIInsight])
def read_ai_insights(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return insight_service.list_for_user(db, current_user, skip, limit)


@router.post("", response_model=schemas.AIInsight)
def create_ai_insight(
    insight: schemas.AIInsightCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return insight_service.create(db, current_user, insight)
