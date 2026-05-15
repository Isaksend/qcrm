"""Business logic for CRM activities."""

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import crud, models, schemas, tenant_access

SYSTEM_ACTIVITY_TYPES = frozenset(
    {
        "stage_changed",
        "deal_won",
        "deal_lost",
        "deal_created",
        "lead_created",
    }
)


class ActivityService:
    def _enrich(self, db: Session, act: models.Activity) -> schemas.ActivityOut:
        label: str | None = None
        link: str | None = None
        et = (act.entityType or "").lower()
        if et == "contact":
            contact = crud.get_contact(db, act.entityId)
            label = contact.name if contact else act.entityId[:8]
            link = "/contacts"
        elif et == "deal":
            deal = crud.get_deal(db, act.entityId)
            label = deal.title if deal else act.entityId[:8]
            link = f"/deals/{act.entityId}"
        else:
            label = act.entityId[:8] if act.entityId else None

        return schemas.ActivityOut(
            id=act.id,
            type=act.type,
            entityType=act.entityType,
            entityId=act.entityId,
            description=act.description,
            timestamp=act.timestamp,
            entityLabel=label,
            entityLink=link,
            isSystem=act.type in SYSTEM_ACTIVITY_TYPES,
        )

    def list_for_user(
        self,
        db: Session,
        user: models.User,
        *,
        skip: int = 0,
        limit: int = 100,
        activity_type: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        days: int | None = None,
        my_only: bool = False,
    ) -> list[schemas.ActivityOut]:
        rows = crud.get_activities_for_user(
            db,
            user,
            skip=skip,
            limit=limit,
            activity_type=activity_type,
            entity_type=entity_type,
            entity_id=entity_id,
            days=days,
            my_only=my_only,
        )
        return [self._enrich(db, act) for act in rows]

    def create(self, db: Session, user: models.User, activity: schemas.ActivityCreate) -> schemas.ActivityOut:
        tenant_access.validate_activity_target(db, user, activity)
        act = crud.create_activity(db=db, activity=activity)
        return self._enrich(db, act)

    def get_by_id(self, db: Session, user: models.User, activity_id: str) -> schemas.ActivityOut:
        act = tenant_access.ensure_activity_access(db, user, activity_id)
        return self._enrich(db, act)

    def update(
        self, db: Session, user: models.User, activity_id: str, body: schemas.ActivityUpdate
    ) -> schemas.ActivityOut:
        act = tenant_access.ensure_activity_access(db, user, activity_id)
        if act.type in SYSTEM_ACTIVITY_TYPES:
            raise HTTPException(status_code=403, detail="System activities cannot be edited")
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
        return self._enrich(db, updated)

    def delete(self, db: Session, user: models.User, activity_id: str) -> dict:
        act = tenant_access.ensure_activity_access(db, user, activity_id)
        if act.type in SYSTEM_ACTIVITY_TYPES:
            raise HTTPException(status_code=403, detail="System activities cannot be deleted")
        crud.delete_activity(db, activity_id)
        return {"status": "deleted"}


activity_service = ActivityService()
