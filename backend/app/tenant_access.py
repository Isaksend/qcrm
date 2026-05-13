"""Authorization helpers: tenant (company) scoping for CRM resources."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas


def ensure_deal_access(db: Session, user: models.User, deal_id: str) -> models.Deal:
    deal = crud.get_deal(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if user.role == "super_admin":
        return deal
    if user.role == "admin":
        if deal.companyId != user.company_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this deal")
        return deal
    if deal.userId != user.id or deal.companyId != user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this deal")
    return deal


def ensure_contact_access(db: Session, user: models.User, contact_id: str) -> models.Contact:
    contact = crud.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    if user.role == "super_admin":
        return contact
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this contact")
    if contact.companyId == user.company_id:
        return contact
    raise HTTPException(status_code=403, detail="Not authorized to access this contact")


def ensure_contact_by_phone(db: Session, user: models.User, phone: str) -> models.Contact:
    contact = crud.get_contact_by_phone(db, phone=phone)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    if user.role == "super_admin":
        return contact
    if not user.company_id or contact.companyId != user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return contact


def validate_activity_target(db: Session, user: models.User, activity: schemas.ActivityCreate) -> None:
    if user.role == "super_admin":
        return
    et = (activity.entityType or "").lower()
    if et == "contact":
        ensure_contact_access(db, user, activity.entityId)
    elif et == "deal":
        ensure_deal_access(db, user, activity.entityId)
    else:
        raise HTTPException(
            status_code=403,
            detail="Only super administrators can create activities for this entity type",
        )


def validate_ai_insight_target(db: Session, user: models.User, insight: schemas.AIInsightCreate) -> None:
    if user.role == "super_admin":
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
