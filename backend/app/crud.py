import datetime
import re
import math
import uuid

from sqlalchemy import and_, false, nullslast, or_
from sqlalchemy.orm import Session

from app import models, schemas


def normalize_phone_digits(phone: str | None) -> str:
    """Digits only, for matching +7 771 ... vs 8771..."""
    if not phone:
        return ""
    return re.sub(r"\D", "", phone)

def get_deals(db: Session, skip: int = 0, limit: int = 100, company_id: str = None, user_id: str = None):
    query = db.query(models.Deal)
    if company_id:
        query = query.filter(models.Deal.companyId == company_id)
    if user_id:
        query = query.filter(models.Deal.userId == user_id)
    return query.offset(skip).limit(limit).all()


def _serialize_deal_value(val) -> str | None:
    if val is None:
        return None
    if isinstance(val, float):
        if math.isnan(val):
            return None
        return repr(val)
    return str(val)


def _deal_field_values_equal(field: str, old, new) -> bool:
    if field == "value":
        try:
            return abs(float(old or 0) - float(new or 0)) < 1e-9
        except (TypeError, ValueError):
            return old == new
    if field in ("contactId", "leadId", "userId", "notes", "title"):
        return (old or "") == (new or "")
    return old == new


def append_deal_change(
    db: Session,
    deal_id: str,
    field: str,
    old,
    new,
    changed_by: str | None,
) -> None:
    if _deal_field_values_equal(field, old, new):
        return
    row = models.DealChangeHistory(
        id=str(uuid.uuid4()),
        deal_id=deal_id,
        field=field,
        old_value=_serialize_deal_value(old),
        new_value=_serialize_deal_value(new),
        changed_by=changed_by,
    )
    db.add(row)


def list_deal_change_history(db: Session, deal_id: str, limit: int = 200):
    return (
        db.query(models.DealChangeHistory)
        .filter(models.DealChangeHistory.deal_id == deal_id)
        .order_by(models.DealChangeHistory.changed_at.desc())
        .limit(limit)
        .all()
    )


def _activity_timestamp(dt: datetime.datetime | None = None) -> str:
    ts = (dt or datetime.datetime.utcnow()).replace(microsecond=0)
    return ts.isoformat() + "Z"


def record_system_activity(
    db: Session,
    *,
    activity_type: str,
    entity_type: str,
    entity_id: str,
    description: str,
    timestamp: str | None = None,
) -> models.Activity:
    """Append a CRM-generated activity row (caller commits)."""
    db_act = models.Activity(
        type=activity_type,
        entityType=entity_type,
        entityId=entity_id,
        description=description,
        timestamp=timestamp or _activity_timestamp(),
    )
    db.add(db_act)
    return db_act


def _record_deal_stage_activity(
    db: Session, deal_id: str, old_stage: str, new_stage: str, deal_title: str | None = None
) -> None:
    deal = get_deal(db, deal_id)
    title = deal_title or (deal.title if deal else "Deal")
    if new_stage == "Closed Won":
        activity_type = "deal_won"
        description = f"{title} marked as Closed Won"
    elif new_stage == "Closed Lost":
        activity_type = "deal_lost"
        description = f"{title} marked as Closed Lost"
    else:
        activity_type = "stage_changed"
        description = f"{title}: {old_stage} → {new_stage}"
    record_system_activity(
        db,
        activity_type=activity_type,
        entity_type="deal",
        entity_id=deal_id,
        description=description,
    )


def create_deal(db: Session, deal: schemas.DealCreate, *, history_actor_id: str | None = None):
    # В SQLAlchemy-модели Deal нет полей currency / createdAt из Pydantic-схемы — иначе TypeError и 500.
    data = deal.model_dump(exclude={"currency"})
    if not data.get("createdAt"):
        data["createdAt"] = datetime.datetime.utcnow()
    db_deal = models.Deal(**data)
    db.add(db_deal)
    db.flush()
    actor = history_actor_id or db_deal.createdById or db_deal.userId
    append_deal_change(db, db_deal.id, "deal_created", None, db_deal.title, actor)
    record_system_activity(
        db,
        activity_type="deal_created",
        entity_type="deal",
        entity_id=db_deal.id,
        description=f"Deal created: {db_deal.title}",
    )
    db.commit()
    db.refresh(db_deal)
    return db_deal


def get_deal(db: Session, deal_id: str):
    return db.query(models.Deal).filter(models.Deal.id == deal_id).first()

def update_deal_stage(db: Session, deal_id: str, stage: str, user_id: str = None):
    db_deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if db_deal:
        old_stage = db_deal.stage
        if old_stage != stage:
            # 1. Update the deal
            db_deal.stage = stage
            if stage in ("Closed Won", "Closed Lost") and not db_deal.closedAt:
                db_deal.closedAt = datetime.datetime.utcnow()

            # 2. Record the history
            history = models.DealStageHistory(
                deal_id=deal_id,
                old_stage=old_stage,
                new_stage=stage,
                changed_by=user_id
            )
            db.add(history)
            append_deal_change(db, deal_id, "stage", old_stage, stage, user_id)
            _record_deal_stage_activity(db, deal_id, old_stage, stage)

            db.commit()
            db.refresh(db_deal)
    return db_deal

def update_deal_combined(db: Session, deal_id: str, upd: schemas.DealUpdate, user_id: str | None = None):
    """Обновление полей сделки + смена стадии с записью в DealStageHistory и deal_change_history."""
    db_deal = get_deal(db, deal_id)
    if not db_deal:
        return None
    data = upd.model_dump(exclude_unset=True)
    if "stage" in data and data["stage"] is not None and data["stage"] != db_deal.stage:
        old_stage = db_deal.stage
        new_stage = data["stage"]
        db_deal.stage = new_stage
        if new_stage in ("Closed Won", "Closed Lost") and not db_deal.closedAt:
            db_deal.closedAt = datetime.datetime.utcnow()
        history = models.DealStageHistory(
            deal_id=deal_id,
            old_stage=old_stage,
            new_stage=new_stage,
            changed_by=user_id,
        )
        db.add(history)
        append_deal_change(db, deal_id, "stage", old_stage, new_stage, user_id)
        _record_deal_stage_activity(db, deal_id, old_stage, new_stage)
        data.pop("stage", None)
    for field in ("title", "value", "notes", "contactId", "leadId", "userId"):
        if field not in data or data[field] is None:
            continue
        old = getattr(db_deal, field)
        new = data[field]
        if _deal_field_values_equal(field, old, new):
            continue
        append_deal_change(db, deal_id, field, old, new, user_id)
        setattr(db_deal, field, new)
    db.commit()
    db.refresh(db_deal)
    return db_deal


def delete_deal(db: Session, deal_id: str):
    db.query(models.Note).filter(models.Note.dealId == deal_id).delete()
    db.query(models.DealTask).filter(models.DealTask.dealId == deal_id).delete()
    db.query(models.Activity).filter(
        models.Activity.entityType == "deal", models.Activity.entityId == deal_id
    ).delete()
    db.query(models.DealStageHistory).filter(models.DealStageHistory.deal_id == deal_id).delete()
    db.query(models.DealChangeHistory).filter(models.DealChangeHistory.deal_id == deal_id).delete()
    db_deal = get_deal(db, deal_id)
    if db_deal:
        db.delete(db_deal)
        db.commit()
    return db_deal


def create_communication_log(db: Session, log_data: dict):
    db_log = models.CommunicationLog(**log_data)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

# Contacts
def get_contacts(db: Session, skip: int = 0, limit: int = 100, company_id: str = None):
    query = db.query(models.Contact)
    if company_id:
        query = query.filter(models.Contact.companyId == company_id)
    return query.offset(skip).limit(limit).all()

def create_contact(db: Session, contact: schemas.ContactCreate):
    db_contact = models.Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def get_contact_by_phone(db: Session, phone: str):
    """Match by exact string or by digits-only equality (avoid duplicates across formats)."""
    if not phone or not str(phone).strip():
        return None
    raw = str(phone).strip()
    norm = normalize_phone_digits(raw)
    exact = db.query(models.Contact).filter(models.Contact.phone == raw).first()
    if exact:
        return exact
    if not norm or len(norm) < 7:
        return None
    for row in db.query(models.Contact).filter(models.Contact.phone.isnot(None)).all():
        if normalize_phone_digits(row.phone) == norm:
            return row
    return None


def get_contact_by_email(db: Session, email: str, company_id: str | None = None):
    if not email or not str(email).strip():
        return None
    em = str(email).strip().lower()
    q = db.query(models.Contact).filter(models.Contact.email == em)
    if company_id is not None:
        q = q.filter(models.Contact.companyId == company_id)
    return q.first()


def get_contact(db: Session, contact_id: str):
    return db.query(models.Contact).filter(models.Contact.id == contact_id).first()


def update_contact(db: Session, contact_id: str, data: schemas.ContactUpdate):
    c = get_contact(db, contact_id)
    if not c:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        if hasattr(c, k) and v is not None:
            setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


def delete_contact(db: Session, contact_id: str):
    c = get_contact(db, contact_id)
    if not c:
        return None
    for d in db.query(models.Deal).filter(models.Deal.contactId == contact_id).all():
        d.contactId = None
    db.query(models.Activity).filter(
        models.Activity.entityType == "contact", models.Activity.entityId == contact_id
    ).delete()
    db.delete(c)
    db.commit()
    return c

def get_contact_by_telegram_id(db: Session, telegram_id: str):
    return db.query(models.Contact).filter(models.Contact.telegram_id == telegram_id).first()

# Chat Messages
def get_chat_messages(db: Session, contact_id: str, limit: int = 100):
    return db.query(models.ChatMessage).filter(
        models.ChatMessage.contactId == contact_id
    ).order_by(models.ChatMessage.timestamp.asc()).limit(limit).all()

def create_chat_message(db: Session, contact_id: str, deal_id: str | None, sender_role: str, sender_id: str | None, sender_name: str, content: str, message_type: str = "text"):
    msg = models.ChatMessage(
        contactId=contact_id,
        dealId=deal_id,
        senderRole=sender_role,
        senderId=sender_id,
        senderName=sender_name,
        content=content,
        messageType=message_type,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg



def create_activity(db: Session, activity: schemas.ActivityCreate):
    db_act = models.Activity(**activity.model_dump())
    db.add(db_act)
    db.commit()
    db.refresh(db_act)
    return db_act


def get_activity(db: Session, activity_id: str):
    return db.query(models.Activity).filter(models.Activity.id == activity_id).first()


def update_activity(db: Session, activity_id: str, data: schemas.ActivityUpdate):
    act = get_activity(db, activity_id)
    if not act:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        if hasattr(act, k) and v is not None:
            setattr(act, k, v)
    db.commit()
    db.refresh(act)
    return act


def delete_activity(db: Session, activity_id: str):
    act = get_activity(db, activity_id)
    if act:
        db.delete(act)
        db.commit()
    return act


def _deal_ids_scope(db: Session, user: models.User, *, my_only: bool) -> list[str] | None:
    """None = all deals (super_admin). Empty = no deals."""
    from app import roles

    if user.role == "super_admin":
        if my_only:
            return [r[0] for r in db.query(models.Deal.id).filter(models.Deal.userId == user.id).all()]
        return None
    if not user.company_id:
        return []
    q = db.query(models.Deal.id).filter(models.Deal.companyId == user.company_id)
    if my_only:
        q = q.filter(models.Deal.userId == user.id)
    return [r[0] for r in q.all()]


def _contact_ids_scope(db: Session, user: models.User, deal_ids: list[str], *, my_only: bool) -> list[str]:
    if user.role == "super_admin" and not my_only:
        return [r[0] for r in db.query(models.Contact.id).all()]
    if not user.company_id:
        return []
    if my_only and deal_ids:
        rows = (
            db.query(models.Deal.contactId)
            .filter(models.Deal.id.in_(deal_ids), models.Deal.contactId.isnot(None))
            .distinct()
            .all()
        )
        return [r[0] for r in rows if r[0]]
    return [
        r[0]
        for r in db.query(models.Contact.id).filter(models.Contact.companyId == user.company_id).all()
    ]


def get_activities_for_user(
    db: Session,
    user: models.User,
    *,
    skip: int = 0,
    limit: int = 100,
    activity_type: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    days: int | None = None,
    my_only: bool = False,
):
    q = db.query(models.Activity)
    deal_ids = _deal_ids_scope(db, user, my_only=my_only)
    contact_ids = _contact_ids_scope(db, user, deal_ids or [], my_only=my_only)

    if deal_ids is not None:
        parts = []
        if contact_ids:
            parts.append(
                and_(models.Activity.entityType == "contact", models.Activity.entityId.in_(contact_ids))
            )
        if deal_ids:
            parts.append(and_(models.Activity.entityType == "deal", models.Activity.entityId.in_(deal_ids)))
        if not parts:
            return []
        q = q.filter(or_(*parts))

    if activity_type:
        q = q.filter(models.Activity.type == activity_type)
    if entity_type:
        q = q.filter(models.Activity.entityType == entity_type)
    if entity_id:
        q = q.filter(models.Activity.entityId == entity_id)
    if days is not None and days > 0:
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        cutoff_s = _activity_timestamp(cutoff)
        q = q.filter(models.Activity.timestamp >= cutoff_s)

    rows = q.order_by(models.Activity.timestamp.desc()).offset(skip).limit(limit).all()
    return rows


# Notes
def get_deal_notes(db: Session, deal_id: str):
    return db.query(models.Note).filter(models.Note.dealId == deal_id).order_by(models.Note.createdAt.desc()).all()

def create_note(db: Session, note: schemas.NoteCreate, user_id: str):
    db_note = models.Note(**note.model_dump(), userId=user_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def note_to_response(db: Session, n: models.Note) -> schemas.Note:
    u = get_user(db, n.userId)
    base = schemas.Note.model_validate(n)
    return base.model_copy(update={"authorName": u.name if u else None})


# Задачи / напоминания по сделке
def list_deal_tasks(db: Session, deal_id: str):
    return (
        db.query(models.DealTask)
        .filter(models.DealTask.dealId == deal_id)
        .order_by(
            models.DealTask.isDone.asc(),
            nullslast(models.DealTask.dueAt.asc()),
            models.DealTask.createdAt.desc(),
        )
        .all()
    )


def get_deal_task(db: Session, task_id: str) -> models.DealTask | None:
    return db.query(models.DealTask).filter(models.DealTask.id == task_id).first()


def create_deal_task(
    db: Session,
    deal_id: str,
    payload: schemas.DealTaskCreate,
    created_by: str | None,
    assigned_user_id: str | None,
):
    t = models.DealTask(
        dealId=deal_id,
        title=payload.title.strip(),
        dueAt=payload.dueAt,
        isDone=0,
        createdBy=created_by,
        createdAt=datetime.datetime.utcnow(),
        assignedUserId=assigned_user_id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def update_deal_task(
    db: Session,
    deal_id: str,
    task_id: str,
    body: schemas.DealTaskUpdate,
) -> models.DealTask | None:
    t = get_deal_task(db, task_id)
    if not t or t.dealId != deal_id:
        return None
    data = body.model_dump(exclude_unset=True)
    if "title" in data and data["title"] is not None:
        t.title = data["title"].strip()
    if "dueAt" in data:
        t.dueAt = data["dueAt"]
    if "isDone" in data and data["isDone"] is not None:
        t.isDone = int(data["isDone"])
    if "assignedUserId" in data and data["assignedUserId"] is not None:
        t.assignedUserId = str(data["assignedUserId"]).strip() or None
    db.commit()
    db.refresh(t)
    return t


def delete_deal_task(db: Session, deal_id: str, task_id: str) -> bool:
    t = get_deal_task(db, task_id)
    if not t or t.dealId != deal_id:
        return False
    db.delete(t)
    db.commit()
    return True


def _my_open_deal_tasks_query(db: Session, user: models.User):
    """Задачи с isDone=0, назначенные на user, по сделкам, которые пользователь может открыть."""
    from app import roles

    q = (
        db.query(models.DealTask, models.Deal)
        .join(models.Deal, models.Deal.id == models.DealTask.dealId)
        .filter(models.DealTask.assignedUserId == user.id)
        .filter(models.DealTask.isDone == 0)
        .filter(models.DealTask.assignedUserId.isnot(None))
    )
    if roles.is_super_admin(user.role):
        return q
    if user.role == "admin":
        if not user.company_id:
            return q.filter(false())
        return q.filter(models.Deal.companyId == user.company_id)
    if not user.company_id:
        return q.filter(false())
    q = q.filter(models.Deal.companyId == user.company_id)
    if roles.sees_own_deals_only(user.role):
        q = q.filter(models.Deal.userId == user.id)
    return q


def count_my_open_deal_tasks(db: Session, user: models.User) -> int:
    q = _my_open_deal_tasks_query(db, user)
    return q.with_entities(models.DealTask.id).count()


def list_my_open_deal_task_rows(db: Session, user: models.User, limit: int = 200):
    q = _my_open_deal_tasks_query(db, user)
    return (
        q.order_by(nullslast(models.DealTask.dueAt.asc()), models.DealTask.createdAt.desc())
        .limit(limit)
        .all()
    )


# AI Insights
def get_ai_insights(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AIInsight).offset(skip).limit(limit).all()


def get_ai_insights_for_user(db: Session, user: models.User, skip: int = 0, limit: int = 100):
    q = db.query(models.AIInsight)
    if user.role == "super_admin":
        return q.offset(skip).limit(limit).all()
    company_id = user.company_id
    if not company_id:
        return []
    contact_ids = [
        r[0] for r in db.query(models.Contact.id).filter(models.Contact.companyId == company_id).all()
    ]
    deal_ids = [r[0] for r in db.query(models.Deal.id).filter(models.Deal.companyId == company_id).all()]
    parts = []
    if contact_ids:
        parts.append(
            and_(models.AIInsight.entityType == "contact", models.AIInsight.entityId.in_(contact_ids))
        )
    if deal_ids:
        parts.append(and_(models.AIInsight.entityType == "deal", models.AIInsight.entityId.in_(deal_ids)))
    if not parts:
        return []
    return q.filter(or_(*parts)).offset(skip).limit(limit).all()


def create_ai_insight(db: Session, insight: schemas.AIInsightCreate):
    db_insight = models.AIInsight(**insight.model_dump())
    db.add(db_insight)
    db.commit()
    db.refresh(db_insight)
    return db_insight

# Users
def get_user(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    from app.auth import get_password_hash
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        company_id=user.company_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_admin(db: Session, user_id: str, data: schemas.UserAdminUpdate) -> models.User | None:
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "name" in payload and payload["name"] is not None:
        db_user.name = payload["name"]
    if "role" in payload and payload["role"] is not None:
        db_user.role = payload["role"]
    if "company_id" in payload:
        db_user.company_id = payload["company_id"]
    if "is_active" in payload and payload["is_active"] is not None:
        db_user.is_active = int(payload["is_active"])
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(db: Session, skip: int = 0, limit: int = 100, company_id: str = None):
    query = db.query(models.User)
    if company_id:
        query = query.filter(models.User.company_id == company_id)
    return query.offset(skip).limit(limit).all()

def delete_user(db: Session, user_id: str):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return user

# Companies
def create_company(db: Session, company: schemas.CompanyCreate):
    import datetime
    tz = (company.timezone or "UTC").strip() or "UTC"
    db_company = models.Company(
        name=company.name,
        created_at=datetime.datetime.utcnow().isoformat(),
        timezone=tz,
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def get_companies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Company).offset(skip).limit(limit).all()


def get_company(db: Session, company_id: str):
    return db.query(models.Company).filter(models.Company.id == company_id).first()


def update_company(db: Session, company_id: str, data: schemas.CompanyUpdate):
    c = get_company(db, company_id)
    if not c:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "name" in payload and payload["name"] is not None:
        c.name = payload["name"]
    if "timezone" in payload and payload["timezone"] is not None:
        c.timezone = payload["timezone"]
    db.commit()
    db.refresh(c)
    return c


def delete_company(db: Session, company_id: str):
    c = get_company(db, company_id)
    if not c:
        return
    db.delete(c)
    db.commit()

# AI Feature Engineering
def get_contact_ai_features(db: Session, contact_id: str):
    import datetime
    from sqlalchemy import func
    
    # 1. Total Deal Value
    total_value = db.query(func.sum(models.Deal.value)).filter(models.Deal.contactId == contact_id).scalar() or 0.0
    
    # 2. Activity Metrics
    now = datetime.datetime.utcnow()
    thirty_days_ago = now - datetime.timedelta(days=30)
    
    # Get all activities for this contact
    activities = db.query(models.Activity).filter(
        models.Activity.entityType == "contact",
        models.Activity.entityId == contact_id
    ).all()
    
    activity_count_30d = 0
    last_contact_date = None
    
    for act in activities:
        try:
            # Assuming ISO format string
            act_date = datetime.datetime.fromisoformat(act.timestamp.replace('Z', ''))
            if act_date > thirty_days_ago:
                activity_count_30d += 1
            
            if last_contact_date is None or act_date > last_contact_date:
                last_contact_date = act_date
        except Exception:
            continue
            
    days_since_last_contact = (now - last_contact_date).days if last_contact_date else 30 # default to 30 if never
    
    # 3. Simple Interaction Score (based on diversity of activity types)
    unique_types = len(set(a.type for a in activities))
    interaction_score = min(unique_types / 5.0, 1.0) # Normalized to 0-1
    
    return {
        "activity_count_30d": activity_count_30d,
        "days_since_last_contact": days_since_last_contact,
        "total_deal_value": total_value,
        "interaction_score": interaction_score
    }
