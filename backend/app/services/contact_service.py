"""Бизнес-логика контактов."""

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import crud, models, schemas, tenant_access


class ContactService:
    def list_for_user(self, db: Session, user: models.User, skip: int, limit: int):
        comp_id = user.company_id if user.role != "super_admin" else None
        return crud.get_contacts(db, skip=skip, limit=limit, company_id=comp_id)

    def create(self, db: Session, user: models.User, contact: schemas.ContactCreate) -> models.Contact:
        if user.role != "super_admin":
            contact = contact.model_copy(update={"companyId": user.company_id})
        return crud.create_contact(db=db, contact=contact)

    def update(self, db: Session, user: models.User, contact_id: str, body: schemas.ContactUpdate) -> models.Contact:
        tenant_access.ensure_contact_access(db, user, contact_id)
        updated = crud.update_contact(db, contact_id, body)
        if not updated:
            raise HTTPException(status_code=404, detail="Contact not found")
        return updated

    def delete(self, db: Session, user: models.User, contact_id: str) -> dict:
        tenant_access.ensure_contact_access(db, user, contact_id)
        if not crud.delete_contact(db, contact_id):
            raise HTTPException(status_code=404, detail="Contact not found")
        return {"status": "deleted"}

    def search_by_phone(self, db: Session, user: models.User, phone: str) -> models.Contact:
        return tenant_access.ensure_contact_by_phone(db, user, phone)


contact_service = ContactService()
