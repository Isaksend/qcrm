"""Authorization helpers: tenant (company) scoping for CRM resources."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app import roles


def ensure_deal_access(db: Session, user: models.User, deal_id: str) -> models.Deal:
    deal = crud.get_deal(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if roles.is_super_admin(user.role):
        return deal
    if user.role == "admin":
        if deal.companyId != user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this deal")
        return deal
    if roles.sees_own_deals_only(user.role):
        if deal.companyId != user.company_id or deal.userId != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this deal")
        return deal
    raise HTTPException(status_code=403, detail="Not authorized to access this deal")


def ensure_contact_access(db: Session, user: models.User, contact_id: str) -> models.Contact:
    contact = crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    if roles.is_super_admin(user.role):
        return contact
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this contact")
    if contact.companyId is None or contact.companyId == user.company_id:
        return contact
    raise HTTPException(status_code=403, detail="Not authorized to access this contact")


def ensure_contact_by_phone(db: Session, user: models.User, phone: str) -> models.Contact:
    contact = crud.get_contact_by_phone(db, phone=phone)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    if roles.is_super_admin(user.role):
        return contact
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Чужая компания — как «не найден», без 403 (меньше шума в UI / CORS при ошибках прокси).
    if contact.companyId is not None and contact.companyId != user.company_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


def user_can_read_deal(user: models.User, deal: models.Deal) -> bool:
    """Согласовано с read_deal: кто может открыть карточку сделки."""
    if roles.is_super_admin(user.role):
        return True
    if user.role == "admin":
        return bool(user.company_id and deal.companyId == user.company_id)
    if roles.sees_own_deals_only(user.role):
        return bool(
            user.company_id
            and deal.companyId == user.company_id
            and deal.userId == user.id
        )
    return False


def ensure_chat_contact_access(
    db: Session, user: models.User, contact_id: str, deal_id: str | None
) -> models.Contact:
    """
    Доступ к чату контакта: обычно по компании контакта; если контакт «чужой» по companyId,
    но передан deal_id и у пользователя есть право на эту сделку с этим contactId — разрешаем
    (данные контакта/сделки могли разъехаться).
    """
    contact = crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    try:
        return ensure_contact_access(db, user, contact_id)
    except HTTPException as exc:
        if exc.status_code != 403:
            raise
    if not deal_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this contact")
    deal = crud.get_deal(db, deal_id)
    if not deal or (deal.contactId or "") != contact_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this contact")
    if not user_can_read_deal(user, deal):
        raise HTTPException(status_code=403, detail="Not authorized to access this deal")
    return contact


def ensure_activity_access(db: Session, user: models.User, activity_id: str) -> models.Activity:
    act = crud.get_activity(db, activity_id)
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")
    et = (act.entityType or "").lower()
    if et == "contact":
        ensure_contact_access(db, user, act.entityId)
    elif et == "deal":
        ensure_deal_access(db, user, act.entityId)
    elif roles.is_super_admin(user.role):
        return act
    else:
        raise HTTPException(status_code=403, detail="Not authorized to access this activity")
    return act


def validate_activity_target(db: Session, user: models.User, activity: schemas.ActivityCreate) -> None:
    if roles.is_super_admin(user.role):
        return
    et = (activity.entityType or "").lower()
    if et == "contact":
        ensure_contact_access(db, user, activity.entityId)
    elif et == "deal":
        ensure_deal_access(db, user, activity.entityId)
    else:
        raise HTTPException(
            status_code=403,
            detail="Activities must be linked to entityType contact or deal",
        )


def validate_ai_insight_target(db: Session, user: models.User, insight: schemas.AIInsightCreate) -> None:
    if roles.is_super_admin(user.role):
        return
    if not insight.entityId:
        raise HTTPException(status_code=400, detail="entityId is required")
    et = (insight.entityType or "").lower()
    if et == "contact":
        ensure_contact_access(db, user, insight.entityId)
    elif et == "deal":
        ensure_deal_access(db, user, insight.entityId)
    else:
        raise HTTPException(status_code=403, detail="Unsupported entity type for this role")
