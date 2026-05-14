"""Бизнес-логика активностей."""

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import crud, models, schemas, tenant_access


class ActivityService:
    def list_for_user(self, db: Session, user: models.User, skip: int, limit: int):
        return crud.get_activities_for_user(db, user, skip=skip, limit=limit)

    def create(self, db: Session, user: models.User, activity: schemas.ActivityCreate) -> models.Activity:
        tenant_access.validate_activity_target(db, user, activity)
        return crud.create_activity(db=db, activity=activity)

    def get_by_id(self, db: Session, user: models.User, activity_id: str) -> models.Activity:
        return tenant_access.ensure_activity_access(db, user, activity_id)

    def update(self, db: Session, user: models.User, activity_id: str, body: schemas.ActivityUpdate) -> models.Activity:
        act = tenant_access.ensure_activity_access(db, user, activity_id)
        merged = schemas.ActivityCreate(
            type=body.type if body.type is not None else act.type,
            entityType=body.entityType if body.entityType is not None else act.entityType,
            entityId=body.entityId if body.entityId is not None else act.entityId,
            description=body.description if body.description is not None else act.description,
            timestamp=body.timestamp if body.timestamp is not None else act.timestamp,
        )
        tenant_access.validate_activity_target(db, user, merged)
        updated = crud.update_activity(db, activity_id, body)
        if not updated:
            raise HTTPException(status_code=404, detail="Activity not found")
        return updated

    def delete(self, db: Session, user: models.User, activity_id: str) -> dict:
        tenant_access.ensure_activity_access(db, user, activity_id)
        crud.delete_activity(db, activity_id)
        return {"status": "deleted"}


activity_service = ActivityService()
