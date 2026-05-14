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


def _can_delegate_task_assignee(user: models.User) -> bool:
    """Назначать задачу на другого пользователя компании могут админ, менеджер и super_admin."""
    if roles.is_super_admin(user.role):
        return True
    if user.role == "admin":
        return True
    if roles.is_manager(user.role):
        return True
    return False


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
        new_deal = crud.create_deal(db=db, deal=deal, history_actor_id=user.id)
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

    def list_deal_history(self, db: Session, user: models.User, deal_id: str) -> list[schemas.DealHistoryEntry]:
        tenant_access.ensure_deal_access(db, user, deal_id)
        rows = crud.list_deal_change_history(db, deal_id)
        out: list[schemas.DealHistoryEntry] = []
        for r in rows:
            actor = crud.get_user(db, r.changed_by) if r.changed_by else None
            out.append(
                schemas.DealHistoryEntry(
                    id=r.id,
                    deal_id=r.deal_id,
                    field=r.field,
                    old_value=r.old_value,
                    new_value=r.new_value,
                    changed_at=r.changed_at,
                    changed_by_id=r.changed_by,
                    changed_by_name=actor.name if actor else None,
                )
            )
        return out

    def list_tasks(self, db: Session, user: models.User, deal_id: str) -> list[models.DealTask]:
        tenant_access.ensure_deal_access(db, user, deal_id)
        return crud.list_deal_tasks(db, deal_id)

    def create_task(self, db: Session, user: models.User, deal_id: str, body: schemas.DealTaskCreate) -> models.DealTask:
        deal = tenant_access.ensure_deal_access(db, user, deal_id)
        title = (body.title or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        raw_assign = (body.assignedUserId or "").strip() if body.assignedUserId else ""
        if _can_delegate_task_assignee(user):
            assignee_id = raw_assign or (deal.userId and str(deal.userId).strip()) or user.id
        else:
            assignee_id = user.id
        _assert_assignee_for_deal(db, deal, assignee_id)
        payload = schemas.DealTaskCreate(title=title, dueAt=body.dueAt, assignedUserId=assignee_id)
        return crud.create_deal_task(db, deal_id, payload, created_by=user.id, assigned_user_id=assignee_id)

    def update_task(
        self, db: Session, user: models.User, deal_id: str, task_id: str, body: schemas.DealTaskUpdate
    ) -> models.DealTask:
        deal = tenant_access.ensure_deal_access(db, user, deal_id)
        data = body.model_dump(exclude_unset=True)
        if "title" in data:
            title = (data["title"] or "").strip()
            if not title:
                raise HTTPException(status_code=400, detail="Title cannot be empty")
            body = body.model_copy(update={"title": title})
        if "assignedUserId" in data and data["assignedUserId"] is not None:
            aid = str(data["assignedUserId"]).strip()
            if not aid:
                raise HTTPException(status_code=400, detail="assignedUserId cannot be empty")
            if not _can_delegate_task_assignee(user) and aid != user.id:
                raise HTTPException(
                    status_code=403,
                    detail="Only company administrators and managers can assign tasks to other users",
                )
            _assert_assignee_for_deal(db, deal, aid)
            body = body.model_copy(update={"assignedUserId": aid})
        updated = crud.update_deal_task(db, deal_id, task_id, body)
        if not updated:
            raise HTTPException(status_code=404, detail="Task not found")
        return updated

    def delete_task(self, db: Session, user: models.User, deal_id: str, task_id: str) -> None:
        tenant_access.ensure_deal_access(db, user, deal_id)
        if not crud.delete_deal_task(db, deal_id, task_id):
            raise HTTPException(status_code=404, detail="Task not found")

    def list_my_open_deal_tasks(self, db: Session, user: models.User, limit: int = 100) -> schemas.MyDealTasksResponse:
        cnt = crud.count_my_open_deal_tasks(db, user)
        rows = crud.list_my_open_deal_task_rows(db, user, limit=limit)
        items: list[schemas.MyDealTaskItem] = []
        for t, d in rows:
            deal_title = (d.title or "").strip() or "—"
            items.append(
                schemas.MyDealTaskItem(
                    id=t.id,
                    dealId=t.dealId,
                    dealTitle=deal_title,
                    title=t.title,
                    dueAt=t.dueAt,
                    assignedUserId=t.assignedUserId,
                    createdAt=t.createdAt,
                )
            )
        return schemas.MyDealTasksResponse(openCount=cnt, items=items)


deal_service = DealService()
