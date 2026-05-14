from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db
from app.services.activity_service import activity_service

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("", response_model=List[schemas.Activity])
def read_activities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return activity_service.list_for_user(db, current_user, skip, limit)


@router.post("", response_model=schemas.Activity)
def create_activity(
    activity: schemas.ActivityCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return activity_service.create(db, current_user, activity)


@router.get("/{activity_id}", response_model=schemas.Activity)
def read_activity(
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return activity_service.get_by_id(db, current_user, activity_id)


@router.patch("/{activity_id}", response_model=schemas.Activity)
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
