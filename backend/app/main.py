from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas, crud
from app.database import engine, get_db

# Create DB Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tiny CRM API", version="1.0.0")

# Setup CORS to allow Vue frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to Tiny CRM Backend!"}

@app.get("/api/deals", response_model=List[schemas.Deal])
def read_deals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    deals = crud.get_deals(db, skip=skip, limit=limit)
    return deals

@app.post("/api/deals", response_model=schemas.Deal)
def create_deal(deal: schemas.DealCreate, db: Session = Depends(get_db)):
    return crud.create_deal(db=db, deal=deal)

@app.patch("/api/deals/{deal_id}/stage", response_model=schemas.Deal)
def update_stage(deal_id: str, stage: str, db: Session = Depends(get_db)):
    deal = crud.update_deal_stage(db=db, deal_id=deal_id, stage=stage)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal
