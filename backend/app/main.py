from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Force uvicorn to reload after installing passlib
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas, crud, auth
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

# -------- CONTACTS --------
@app.get("/api/contacts", response_model=List[schemas.Contact])
def read_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_contacts(db, skip=skip, limit=limit)

@app.post("/api/contacts", response_model=schemas.Contact)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    return crud.create_contact(db=db, contact=contact)

# -------- SELLERS --------
@app.get("/api/sellers", response_model=List[schemas.Seller])
def read_sellers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_sellers(db, skip=skip, limit=limit)

@app.post("/api/sellers", response_model=schemas.Seller)
def create_seller(seller: schemas.SellerCreate, db: Session = Depends(get_db)):
    return crud.create_seller(db=db, seller=seller)

# -------- ACTIVITIES --------
@app.get("/api/activities", response_model=List[schemas.Activity])
def read_activities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_activities(db, skip=skip, limit=limit)

@app.post("/api/activities", response_model=schemas.Activity)
def create_activity(activity: schemas.ActivityCreate, db: Session = Depends(get_db)):
    return crud.create_activity(db=db, activity=activity)

# -------- AI INSIGHTS --------
@app.get("/api/insights", response_model=List[schemas.AIInsight])
def read_ai_insights(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_ai_insights(db, skip=skip, limit=limit)

@app.post("/api/insights", response_model=schemas.AIInsight)
def create_ai_insight(insight: schemas.AIInsightCreate, db: Session = Depends(get_db)):
    return crud.create_ai_insight(db=db, insight=insight)

# -------- AUTH --------
@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/api/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = auth.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

# -------- RBAC USERS MANAGEMENT --------
@app.get("/api/users", response_model=List[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin)):
    # Admins see their company users. Super Admins see all.
    comp_id = current_user.company_id if current_user.role != "super_admin" else None
    return crud.get_users(db, skip=skip, limit=limit, company_id=comp_id)

@app.post("/api/users", response_model=schemas.UserResponse)
def create_new_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin)):
    # Restrict roles based on who is creating
    if current_user.role != "super_admin":
        if user.role == "super_admin":
            raise HTTPException(status_code=403, detail="Cannot create super admin")
        user.company_id = current_user.company_id # Force admin's company id
    return crud.create_user(db=db, user=user)

@app.delete("/api/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin)):
    target_user = crud.get_user(db, user_id=user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if current_user.role != "super_admin" and target_user.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Not permitted to delete users outside your company")
        
    crud.delete_user(db, user_id=user_id)
    return {"status": "deleted"}

# -------- COMPANIES MANAGEMENT --------
@app.post("/api/companies", response_model=schemas.CompanyResponse)
def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_super_admin)):
    return crud.create_company(db=db, company=company)

@app.get("/api/companies", response_model=List[schemas.CompanyResponse])
def get_companies_list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_super_admin)):
    return crud.get_companies(db, skip=skip, limit=limit)
