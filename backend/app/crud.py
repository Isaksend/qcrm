import re

from sqlalchemy import and_, or_
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

def create_deal(db: Session, deal: schemas.DealCreate):
    # В SQLAlchemy-модели Deal нет полей currency / createdAt из Pydantic-схемы — иначе TypeError и 500.
    data = deal.model_dump(exclude={"currency", "createdAt"})
    db_deal = models.Deal(**data)
    db.add(db_deal)
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
            
            # 2. Record the history
            history = models.DealStageHistory(
                deal_id=deal_id,
                old_stage=old_stage,
                new_stage=stage,
                changed_by=user_id
            )
            db.add(history)
            
            db.commit()
            db.refresh(db_deal)
    return db_deal

def update_deal_combined(db: Session, deal_id: str, upd: schemas.DealUpdate, user_id: str | None = None):
    """Обновление полей сделки + смена стадии с записью в DealStageHistory."""
    db_deal = get_deal(db, deal_id)
    if not db_deal:
        return None
    data = upd.model_dump(exclude_unset=True)
    if "stage" in data and data["stage"] is not None and data["stage"] != db_deal.stage:
        old_stage = db_deal.stage
        new_stage = data["stage"]
        db_deal.stage = new_stage
        history = models.DealStageHistory(
            deal_id=deal_id,
            old_stage=old_stage,
            new_stage=new_stage,
            changed_by=user_id,
        )
        db.add(history)
        data.pop("stage", None)
    for field in ("title", "value", "notes", "contactId", "leadId", "userId"):
        if field in data and data[field] is not None:
            setattr(db_deal, field, data[field])
    db.commit()
    db.refresh(db_deal)
    return db_deal


def delete_deal(db: Session, deal_id: str):
    db.query(models.Note).filter(models.Note.dealId == deal_id).delete()
    db.query(models.Activity).filter(
        models.Activity.entityType == "deal", models.Activity.entityId == deal_id
    ).delete()
    db.query(models.DealStageHistory).filter(models.DealStageHistory.deal_id == deal_id).delete()
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


def get_activities_for_user(db: Session, user: models.User, skip: int = 0, limit: int = 100):
    q = db.query(models.Activity)
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
            and_(models.Activity.entityType == "contact", models.Activity.entityId.in_(contact_ids))
        )
    if deal_ids:
        parts.append(and_(models.Activity.entityType == "deal", models.Activity.entityId.in_(deal_ids)))
    if not parts:
        return []
    return q.filter(or_(*parts)).offset(skip).limit(limit).all()


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
    db_company = models.Company(name=company.name, created_at=datetime.datetime.utcnow().isoformat())
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
    if data.name is not None:
        c.name = data.name
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
