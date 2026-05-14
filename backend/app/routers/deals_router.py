from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db
from app.services.deal_service import deal_service

router = APIRouter(prefix="/api/deals", tags=["deals"])


@router.get("", response_model=List[schemas.Deal])
def read_deals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return deal_service.list_for_user(db, current_user, skip, limit)


@router.post("", response_model=schemas.Deal)
def create_deal(
    deal: schemas.DealCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return deal_service.create(db, current_user, deal)


@router.get("/{deal_id}", response_model=schemas.Deal)
def read_deal(
    deal_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return deal_service.get_by_id(db, current_user, deal_id)


@router.patch("/{deal_id}/stage", response_model=schemas.Deal)
def update_stage(
    deal_id: str,
    stage: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return deal_service.update_stage(db, current_user, deal_id, stage)


@router.patch("/{deal_id}", response_model=schemas.Deal)
def update_deal(
    deal_id: str,
    body: schemas.DealUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return deal_service.update(db, current_user, deal_id, body)


@router.delete("/{deal_id}")
def remove_deal(
    deal_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return deal_service.delete(db, current_user, deal_id)


@router.get("/{deal_id}/notes", response_model=List[schemas.Note])
def read_deal_notes(
    deal_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return deal_service.list_notes(db, current_user, deal_id)


@router.post("/{deal_id}/notes", response_model=schemas.Note)
def create_deal_note(
    deal_id: str,
    note: schemas.NoteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return deal_service.add_note(db, current_user, deal_id, note)
