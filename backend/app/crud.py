from sqlalchemy.orm import Session
from app import models, schemas

def get_deals(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Deal).offset(skip).limit(limit).all()

def create_deal(db: Session, deal: schemas.DealCreate):
    db_deal = models.Deal(**deal.model_dump())
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal

def update_deal_stage(db: Session, deal_id: str, stage: str):
    db_deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if db_deal:
        db_deal.stage = stage
        db.commit()
        db.refresh(db_deal)
    return db_deal
