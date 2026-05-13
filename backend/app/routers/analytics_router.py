from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, false
from app.database import get_db
from app import models, auth

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


def _deal_ids_for_user(db: Session, user: models.User) -> list[str] | None:
    """None = all deals (super_admin). Empty list = no access to deals."""
    if user.role == "super_admin":
        return None
    if not user.company_id:
        return []
    return [r[0] for r in db.query(models.Deal.id).filter(models.Deal.companyId == user.company_id).all()]


def _contact_ids_for_user(db: Session, user: models.User) -> list[str] | None:
    if user.role == "super_admin":
        return None
    if not user.company_id:
        return []
    return [
        r[0] for r in db.query(models.Contact.id).filter(models.Contact.companyId == user.company_id).all()
    ]


def _contacts_query_for_user(db: Session, user: models.User):
    """Contacts visible to the current user (same scope as list contacts)."""
    q = db.query(models.Contact)
    if user.role == "super_admin":
        return q
    if not user.company_id:
        return q.filter(false())
    return q.filter(models.Contact.companyId == user.company_id)


@router.get("/sales-velocity")
async def get_sales_velocity(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Calculates average time spent in each deal stage (scoped to the user's company)."""
    deal_ids = _deal_ids_for_user(db, current_user)
    history_q = db.query(models.DealStageHistory)
    if deal_ids is not None:
        if not deal_ids:
            return {"average_days_per_stage": {}, "total_deals_analyzed": 0}
        history_q = history_q.filter(models.DealStageHistory.deal_id.in_(deal_ids))
    history = history_q.all()

    stage_durations: dict[str, list[int]] = {}

    deal_history: dict[str | None, list] = {}
    for h in history:
        if h.deal_id not in deal_history:
            deal_history[h.deal_id] = []
        deal_history[h.deal_id].append(h)

    for deal_id, records in deal_history.items():
        records.sort(key=lambda x: x.changed_at)
        for i in range(len(records) - 1):
            stage = records[i].new_stage
            duration = (records[i + 1].changed_at - records[i].changed_at).days
            if stage not in stage_durations:
                stage_durations[stage] = []
            stage_durations[stage].append(duration)

    avg_velocity = {stage: (sum(days) / len(days)) if days else 0 for stage, days in stage_durations.items()}

    return {
        "average_days_per_stage": avg_velocity,
        "total_deals_analyzed": len(deal_history),
    }


@router.get("/communication-stats")
async def get_comm_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Returns stats about communication types and statuses (scoped to the user's company)."""
    contact_ids = _contact_ids_for_user(db, current_user)
    q = db.query(models.CommunicationLog.type, func.count(models.CommunicationLog.id))
    if contact_ids is not None:
        if not contact_ids:
            return {"counts_by_type": {}, "period": "Last 45 days"}
        q = q.filter(models.CommunicationLog.contact_id.in_(contact_ids))
    stats = q.group_by(models.CommunicationLog.type).all()

    return {
        "counts_by_type": {t: count for t, count in stats},
        "period": "Last 45 days",
    }


@router.get("/contacts-by-country")
async def contacts_by_country(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Количество контактов по стране (ISO2), в рамках компании пользователя."""
    q = _contacts_query_for_user(db, current_user)
    rows = (
        q.with_entities(models.Contact.country_iso2, func.count(models.Contact.id))
        .group_by(models.Contact.country_iso2)
        .all()
    )
    return {
        "rows": [
            {"country_iso2": iso, "count": cnt}
            for iso, cnt in rows
        ],
        "total_contacts": int(q.count()),
    }


@router.get("/contacts-by-city")
async def contacts_by_city(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
    limit: int = 25,
):
    """Топ городов по числу контактов (только заполненное поле city)."""
    q = (
        _contacts_query_for_user(db, current_user)
        .filter(models.Contact.city.isnot(None))
        .filter(models.Contact.city != "")
    )
    rows = (
        q.with_entities(
            models.Contact.city,
            models.Contact.country_iso2,
            func.count(models.Contact.id).label("cnt"),
        )
        .group_by(models.Contact.city, models.Contact.country_iso2)
        .order_by(func.count(models.Contact.id).desc())
        .limit(min(limit, 100))
        .all()
    )
    return {
        "rows": [
            {"city": city, "country_iso2": iso, "count": int(cnt)}
            for city, iso, cnt in rows
        ],
    }
