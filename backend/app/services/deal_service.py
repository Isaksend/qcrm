"""Бизнес-логика сделок и заметок к сделке."""

import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import crud, models, schemas, tenant_access, roles

audit_logger = logging.getLogger("audit")


class DealService:
    def list_for_user(self, db: Session, user: models.User, skip: int, limit: int):
        user_id = None
        company_id = user.company_id
        if roles.is_sales_rep(user.role):
            user_id = user.id
        elif roles.is_super_admin(user.role):
            company_id = None
        return crud.get_deals(db, skip=skip, limit=limit, company_id=company_id, user_id=user_id)

    def create(self, db: Session, user: models.User, deal: schemas.DealCreate) -> models.Deal:
        if roles.is_sales_rep(user.role):
            deal = deal.model_copy(update={"userId": user.id})
        if roles.is_super_admin(user.role):
            if not deal.companyId:
                raise HTTPException(
                    status_code=400,
                    detail="companyId is required in the request body when creating a deal as super_admin",
                )
            deal = deal.model_copy(update={"createdById": user.id})
        else:
            deal = deal.model_copy(update={"companyId": user.company_id, "createdById": user.id})
        new_deal = crud.create_deal(db=db, deal=deal)
        audit_logger.info("User %s created deal: %s (ID: %s)", user.email, new_deal.title, new_deal.id)
        return new_deal

    def get_by_id(self, db: Session, user: models.User, deal_id: str) -> models.Deal:
        deal = crud.get_deal(db, deal_id=deal_id)
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        if roles.is_sales_rep(user.role) and deal.userId != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this deal")
        if roles.is_company_admin(user.role) and deal.companyId != user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this deal")
        return deal

    def update_stage(self, db: Session, user: models.User, deal_id: str, stage: str) -> models.Deal:
        deal = crud.get_deal(db, deal_id=deal_id)
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")
        if roles.is_sales_rep(user.role) and deal.userId != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this deal")
        if roles.is_company_admin(user.role) and deal.companyId != user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this deal")
        return crud.update_deal_stage(db=db, deal_id=deal_id, stage=stage, user_id=user.id)

    def update(self, db: Session, user: models.User, deal_id: str, body: schemas.DealUpdate) -> models.Deal:
        tenant_access.ensure_deal_access(db, user, deal_id)
        updated = crud.update_deal_combined(db, deal_id, body, user_id=user.id)
        if not updated:
            raise HTTPException(status_code=404, detail="Deal not found")
        return updated

    def delete(self, db: Session, user: models.User, deal_id: str) -> dict:
        tenant_access.ensure_deal_access(db, user, deal_id)
        if not crud.delete_deal(db, deal_id):
            raise HTTPException(status_code=404, detail="Deal not found")
        return {"status": "deleted"}

    def list_notes(self, db: Session, user: models.User, deal_id: str):
        tenant_access.ensure_deal_access(db, user, deal_id)
        rows = crud.get_deal_notes(db, deal_id=deal_id)
        return [crud.note_to_response(db, n) for n in rows]

    def add_note(self, db: Session, user: models.User, deal_id: str, note: schemas.NoteCreate) -> schemas.Note:
        tenant_access.ensure_deal_access(db, user, deal_id)
        if note.dealId != deal_id:
            raise HTTPException(status_code=400, detail="Mismatched deal ID")
        saved = crud.create_note(db, note=note, user_id=user.id)
        return crud.note_to_response(db, saved)


deal_service = DealService()
