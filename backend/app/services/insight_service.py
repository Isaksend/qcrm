"""AI-инсайты и анализ чата по контакту."""

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import crud, models, schemas, tenant_access, ai_analyzer


class InsightService:
    def list_for_user(self, db: Session, user: models.User, skip: int, limit: int):
        return crud.get_ai_insights_for_user(db, user, skip=skip, limit=limit)

    def create(self, db: Session, user: models.User, insight: schemas.AIInsightCreate) -> models.AIInsight:
        tenant_access.validate_ai_insight_target(db, user, insight)
        return crud.create_ai_insight(db=db, insight=insight)

    async def analyze_contact_chat(self, db: Session, user: models.User, contact_id: str) -> models.AIInsight:
        tenant_access.ensure_contact_access(db, user, contact_id)
        msgs = crud.get_chat_messages(db, contact_id=contact_id, limit=50)
        if not msgs:
            raise HTTPException(status_code=400, detail="No messages to analyze")

        transcript = ""
        for m in reversed(msgs):
            sender = m.senderName
            content = m.content if m.messageType == "text" else "[Image]"
            transcript += f"{sender}: {content}\n"

        insight_data = await ai_analyzer.analyze_chat_probability(transcript)
        if not insight_data:
            raise HTTPException(status_code=503, detail="AI Service unavailable")

        return crud.create_ai_insight(
            db,
            insight=schemas.AIInsightCreate(
                entityType="contact",
                entityId=contact_id,
                category="prediction",
                title=insight_data["title"],
                content=insight_data["content"],
                confidence=insight_data["confidence"],
                suggestions=insight_data["suggestions"],
            ),
        )


insight_service = InsightService()
