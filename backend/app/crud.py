from sqlalchemy.orm import Session
from app import models, schemas

def get_deals(db: Session, skip: int = 0, limit: int = 100, company_id: str = None, user_id: str = None):
    query = db.query(models.Deal)
    if company_id:
        query = query.filter(models.Deal.companyId == company_id)
    if user_id:
        query = query.filter(models.Deal.userId == user_id)
    return query.offset(skip).limit(limit).all()

def create_deal(db: Session, deal: schemas.DealCreate):
    db_deal = models.Deal(**deal.model_dump())
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal

    return db_deal

def get_deal(db: Session, deal_id: str):
    return db.query(models.Deal).filter(models.Deal.id == deal_id).first()

def update_deal_stage(db: Session, deal_id: str, stage: str):
    db_deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if db_deal:
        db_deal.stage = stage
        db.commit()
        db.refresh(db_deal)
    return db_deal

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
    return db.query(models.Contact).filter(models.Contact.phone == phone).first()



def create_activity(db: Session, activity: schemas.ActivityCreate):
    db_act = models.Activity(**activity.model_dump())
    db.add(db_act)
    db.commit()
    db.refresh(db_act)
    return db_act

# Notes
def get_deal_notes(db: Session, deal_id: str):
    return db.query(models.Note).filter(models.Note.dealId == deal_id).order_by(models.Note.createdAt.desc()).all()

def create_note(db: Session, note: schemas.NoteCreate, user_id: str):
    db_note = models.Note(**note.model_dump(), userId=user_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

# AI Insights
def get_ai_insights(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AIInsight).offset(skip).limit(limit).all()

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
