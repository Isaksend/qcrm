from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db
from app.services.contact_service import contact_service

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.get("", response_model=List[schemas.Contact])
def read_contacts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return contact_service.list_for_user(db, current_user, skip, limit)


@router.post("", response_model=schemas.Contact)
def create_contact(
    contact: schemas.ContactCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return contact_service.create(db, current_user, contact)


@router.get("/search", response_model=schemas.Contact)
def search_contact(
    phone: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return contact_service.search_by_phone(db, current_user, phone)


@router.patch("/{contact_id}", response_model=schemas.Contact)
def update_contact_route(
    contact_id: str,
    body: schemas.ContactUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return contact_service.update(db, current_user, contact_id, body)


@router.delete("/{contact_id}")
def delete_contact_route(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return contact_service.delete(db, current_user, contact_id)
