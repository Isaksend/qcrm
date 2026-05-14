"""Бизнес-логика сделок и заметок к сделке."""

import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app import crud, models, schemas, tenant_access, roles

audit_logger = logging.getLogger("audit")


def _assert_assignee_for_deal(db: Session, deal: models.Deal, new_user_id: str) -> None:
    """Ответственный — активный пользователь той же компании, что и сделка (не super_admin)."""
    if not deal.companyId:
        raise HTTPException(status_code=400, detail="Deal has no company; cannot assign owner")
    target = crud.get_user(db, new_user_id)
    if not target or not target.is_active:
        raise HTTPException(status_code=400, detail="Assignee not found or inactive")
    if target.company_id != deal.companyId:
        raise HTTPException(status_code=400, detail="Assignee must belong to the same company as the deal")
    if target.role == "super_admin":
        raise HTTPException(status_code=400, detail="Cannot assign a deal to a super administrator")


class DealService:
    def list_for_user(self, db: Session, user: models.User, skip: int, limit: int):
        company_id = user.company_id
        user_id_filter = None
        if roles.is_super_admin(user.role):
            company_id = None
        elif roles.sees_own_deals_only(user.role):
            user_id_filter = user.id
        return crud.get_deals(
            db, skip=skip, limit=limit, company_id=company_id, user_id=user_id_filter
        )

    def create(self, db: Session, user: models.User, deal: schemas.DealCreate) -> models.Deal:
        if roles.is_sales_rep(user.role) or roles.is_manager(user.role):
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
        return tenant_access.ensure_deal_access(db, user, deal_id)

    def update_stage(self, db: Session, user: models.User, deal_id: str, stage: str) -> models.Deal:
        tenant_access.ensure_deal_access(db, user, deal_id)
        return crud.update_deal_stage(db=db, deal_id=deal_id, stage=stage, user_id=user.id)

    def update(self, db: Session, user: models.User, deal_id: str, body: schemas.DealUpdate) -> models.Deal:
        deal = tenant_access.ensure_deal_access(db, user, deal_id)
        data = body.model_dump(exclude_unset=True)
        if "userId" in data and data["userId"] is not None:
            new_uid = data["userId"]
            if new_uid != deal.userId:
                if not (roles.is_super_admin(user.role) or user.role == "admin"):
                    raise HTTPException(
                        status_code=403,
                        detail="Only company administrators can reassign the deal owner",
                    )
                _assert_assignee_for_deal(db, deal, new_uid)
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
