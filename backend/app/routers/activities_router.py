from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db
from app.services.activity_service import activity_service

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("", response_model=List[schemas.ActivityOut])
def read_activities(
    skip: int = 0,
    limit: int = Query(100, ge=1, le=500),
    type: Optional[str] = Query(None, alias="type"),
    entity_type: Optional[str] = Query(None, alias="entityType"),
    entity_id: Optional[str] = Query(None, alias="entityId"),
    days: Optional[int] = Query(None, ge=1, le=365),
    my_only: bool = Query(False, alias="myOnly"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return activity_service.list_for_user(
        db,
        current_user,
        skip=skip,
        limit=limit,
        activity_type=type,
        entity_type=entity_type,
        entity_id=entity_id,
        days=days,
        my_only=my_only,
    )


@router.post("", response_model=schemas.ActivityOut)
def create_activity(
    activity: schemas.ActivityCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return activity_service.create(db, current_user, activity)


@router.get("/{activity_id}", response_model=schemas.ActivityOut)
def read_activity(
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return activity_service.get_by_id(db, current_user, activity_id)


@router.patch("/{activity_id}", response_model=schemas.ActivityOut)
def update_activity_route(
    activity_id: str,
    body: schemas.ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return activity_service.update(db, current_user, activity_id, body)


@router.delete("/{activity_id}")
def delete_activity_route(
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return activity_service.delete(db, current_user, activity_id)
