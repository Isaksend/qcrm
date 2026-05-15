"""AI-инсайты (CRUD)."""

from sqlalchemy.orm import Session

from app import crud, models, schemas, tenant_access


class InsightService:
    def list_for_user(self, db: Session, user: models.User, skip: int, limit: int):
        return crud.get_ai_insights_for_user(db, user, skip=skip, limit=limit)

    def create(self, db: Session, user: models.User, insight: schemas.AIInsightCreate) -> models.AIInsight:
        tenant_access.validate_ai_insight_target(db, user, insight)
        return crud.create_ai_insight(db=db, insight=insight)


insight_service = InsightService()
