from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from contextlib import asynccontextmanager
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel

from app import models, schemas, crud, auth, ai_analyzer, tenant_access, roles
from app.database import get_db, ensure_deals_created_by_column
from app.telegram_bot import start_polling, stop_polling, send_telegram_message, get_telegram_user_info, send_telegram_photo
from app.services.ai_service import ai_service
from app.routers import ai_router, analytics_router
from app.config import get_settings

# Configure Sentry
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            StarletteIntegration(),
        ],
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

# Configure Audit Logger
_settings = get_settings()
_audit_path = _settings.AUDIT_LOG_PATH
os.makedirs(os.path.dirname(_audit_path) or ".", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(_audit_path),
        logging.StreamHandler()
    ]
)
audit_logger = logging.getLogger("audit")

# Create uploads directory
os.makedirs("uploads/chat", exist_ok=True)

# Create DB Tables - Handled by Alembic in production
# models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    ensure_deals_created_by_column()
    try:
        ai_service.load_artifacts(get_settings().ML_MODELS_PATH)
    except Exception as exc:
        logging.getLogger("uvicorn.error").warning("AI model load skipped or failed: %s", exc)
    try:
        start_polling()
    except Exception as exc:
        logging.getLogger("uvicorn.error").warning("Telegram polling start issue: %s", exc)
    yield
    print("Shutting down...")
    stop_polling()

app = FastAPI(title="Tiny CRM API", version="1.0.0", lifespan=lifespan)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}


@app.middleware("http")
async def audit_middleware(request, call_next):
    response = await call_next(request)
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        # In a real app, we would get the user from the token here
        # but middleware runs before auth dependencies usually.
        # We can log basic info for now.
        audit_logger.info(f"Action: {request.method} {request.url.path} - Status: {response.status_code}")
    return response

# Serve uploaded files (images etc.)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Setup CORS
_settings_cors = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings_cors.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include AI Router
app.include_router(ai_router.router)
app.include_router(analytics_router.router)

@app.post("/api/chat/{contact_id}/analyze", response_model=schemas.AIInsight)
async def analyze_contact_chat(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    tenant_access.ensure_contact_access(db, current_user, contact_id)
    # Fetch recent messages (up to 50 for context)
    msgs = crud.get_chat_messages(db, contact_id=contact_id, limit=50)
    if not msgs:
        raise HTTPException(status_code=400, detail="No messages to analyze")

    # Format transcript
    transcript = ""
    for m in reversed(msgs):
        sender = m.senderName
        content = m.content if m.messageType == 'text' else "[Image]"
        transcript += f"{sender}: {content}\n"

    # Analyze with Gemini
    insight_data = await ai_analyzer.analyze_chat_probability(transcript)
    if not insight_data:
        raise HTTPException(status_code=503, detail="AI Service unavailable")

    # Save to AI Insights
    saved = crud.create_ai_insight(
        db,
        insight=schemas.AIInsightCreate(
            entityType="contact",
            entityId=contact_id,
            category="prediction",
            title=insight_data["title"],
            content=insight_data["content"],
            confidence=insight_data["confidence"],
            suggestions=insight_data["suggestions"],
        )
    )
    return saved

@app.get("/")
def root():
    return {"message": "Welcome to Tiny CRM Backend!"}

# Note: lifespan handles startup/shutdown now

@app.get("/api/deals", response_model=List[schemas.Deal])
def read_deals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    user_id = None
    company_id = current_user.company_id
    
    if roles.is_sales_rep(current_user.role):
        user_id = current_user.id
    elif roles.is_super_admin(current_user.role):
        company_id = None
        
    return crud.get_deals(db, skip=skip, limit=limit, company_id=company_id, user_id=user_id)

@app.post("/api/deals", response_model=schemas.Deal)
def create_deal(deal: schemas.DealCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    if roles.is_sales_rep(current_user.role):
        deal.userId = current_user.id

    deal.companyId = current_user.company_id
    deal = deal.model_copy(update={"createdById": current_user.id})
    new_deal = crud.create_deal(db=db, deal=deal)
    audit_logger.info(f"User {current_user.email} created deal: {new_deal.title} (ID: {new_deal.id})")
    return new_deal

@app.get("/api/deals/{deal_id}", response_model=schemas.Deal)
def read_deal(deal_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    deal = crud.get_deal(db, deal_id=deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
        
    if roles.is_sales_rep(current_user.role) and deal.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this deal")
        
    if roles.is_company_admin(current_user.role) and deal.companyId != current_user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this deal")
        
    return deal

@app.patch("/api/deals/{deal_id}/stage", response_model=schemas.Deal)
def update_stage(deal_id: str, stage: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    # Check access before updating
    deal = crud.get_deal(db, deal_id=deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    if roles.is_sales_rep(current_user.role) and deal.userId != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this deal")
    
    if roles.is_company_admin(current_user.role) and deal.companyId != current_user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this deal")

    return crud.update_deal_stage(db=db, deal_id=deal_id, stage=stage, user_id=current_user.id)


@app.patch("/api/deals/{deal_id}", response_model=schemas.Deal)
def update_deal(
    deal_id: str,
    body: schemas.DealUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    tenant_access.ensure_deal_access(db, current_user, deal_id)
    updated = crud.update_deal_combined(db, deal_id, body, user_id=current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Deal not found")
    return updated


@app.delete("/api/deals/{deal_id}")
def remove_deal(
    deal_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    tenant_access.ensure_deal_access(db, current_user, deal_id)
    if not crud.delete_deal(db, deal_id):
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"status": "deleted"}

@app.get("/api/deals/{deal_id}/notes", response_model=List[schemas.Note])
def read_deal_notes(deal_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    tenant_access.ensure_deal_access(db, current_user, deal_id)
    rows = crud.get_deal_notes(db, deal_id=deal_id)
    return [crud.note_to_response(db, n) for n in rows]


@app.post("/api/deals/{deal_id}/notes", response_model=schemas.Note)
def create_deal_note(deal_id: str, note: schemas.NoteCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    tenant_access.ensure_deal_access(db, current_user, deal_id)
    if note.dealId != deal_id:
        raise HTTPException(status_code=400, detail="Mismatched deal ID")
    saved = crud.create_note(db, note=note, user_id=current_user.id)
    return crud.note_to_response(db, saved)

# -------- CONTACTS --------
@app.get("/api/contacts", response_model=List[schemas.Contact])
def read_contacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    comp_id = current_user.company_id if current_user.role != "super_admin" else None
    return crud.get_contacts(db, skip=skip, limit=limit, company_id=comp_id)

@app.post("/api/contacts", response_model=schemas.Contact)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    if current_user.role != "super_admin":
        contact.companyId = current_user.company_id
    return crud.create_contact(db=db, contact=contact)


@app.patch("/api/contacts/{contact_id}", response_model=schemas.Contact)
def update_contact_route(
    contact_id: str,
    body: schemas.ContactUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    tenant_access.ensure_contact_access(db, current_user, contact_id)
    updated = crud.update_contact(db, contact_id, body)
    if not updated:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated


@app.delete("/api/contacts/{contact_id}")
def delete_contact_route(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    tenant_access.ensure_contact_access(db, current_user, contact_id)
    if not crud.delete_contact(db, contact_id):
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"status": "deleted"}

@app.get("/api/contacts/search", response_model=schemas.Contact)
def search_contact(
    phone: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return tenant_access.ensure_contact_by_phone(db, current_user, phone)



# -------- ACTIVITIES --------
@app.get("/api/activities", response_model=List[schemas.Activity])
def read_activities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return crud.get_activities_for_user(db, current_user, skip=skip, limit=limit)

@app.post("/api/activities", response_model=schemas.Activity)
def create_activity(
    activity: schemas.ActivityCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    tenant_access.validate_activity_target(db, current_user, activity)
    return crud.create_activity(db=db, activity=activity)


@app.get("/api/activities/{activity_id}", response_model=schemas.Activity)
def read_activity(
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return tenant_access.ensure_activity_access(db, current_user, activity_id)


@app.patch("/api/activities/{activity_id}", response_model=schemas.Activity)
def update_activity_route(
    activity_id: str,
    body: schemas.ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    act = tenant_access.ensure_activity_access(db, current_user, activity_id)
    merged = schemas.ActivityCreate(
        type=body.type if body.type is not None else act.type,
        entityType=body.entityType if body.entityType is not None else act.entityType,
        entityId=body.entityId if body.entityId is not None else act.entityId,
        description=body.description if body.description is not None else act.description,
        timestamp=body.timestamp if body.timestamp is not None else act.timestamp,
    )
    tenant_access.validate_activity_target(db, current_user, merged)
    updated = crud.update_activity(db, activity_id, body)
    if not updated:
        raise HTTPException(status_code=404, detail="Activity not found")
    return updated


@app.delete("/api/activities/{activity_id}")
def delete_activity_route(
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    tenant_access.ensure_activity_access(db, current_user, activity_id)
    crud.delete_activity(db, activity_id)
    return {"status": "deleted"}

# -------- AI INSIGHTS --------
@app.get("/api/insights", response_model=List[schemas.AIInsight])
def read_ai_insights(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return crud.get_ai_insights_for_user(db, current_user, skip=skip, limit=limit)

@app.post("/api/insights", response_model=schemas.AIInsight)
def create_ai_insight(
    insight: schemas.AIInsightCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    tenant_access.validate_ai_insight_target(db, current_user, insight)
    return crud.create_ai_insight(db=db, insight=insight)

# -------- AUTH --------
@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    safe = user.model_copy(update={"role": "sales_representative"})
    return crud.create_user(db=db, user=safe)

@app.post("/api/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = auth.access_token_expires_delta()
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user


@app.get("/api/users/{user_id}", response_model=schemas.UserResponse)
def read_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """Карточка пользователя по id (та же компания или super_admin) — для отображения на сделке."""
    target = crud.get_user(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if roles.is_super_admin(current_user.role):
        return target
    if current_user.id == target.id:
        return target
    if not current_user.company_id or target.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Not permitted to view this user")
    return target


# -------- RBAC USERS MANAGEMENT --------
@app.get("/api/users", response_model=List[schemas.UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    """Список коллег компании для всех авторизованных (имена в карточках сделок и т.д.). Управление — отдельные эндпоинты с RBAC."""
    if roles.is_super_admin(current_user.role):
        comp_id = None
    elif current_user.company_id:
        comp_id = current_user.company_id
    else:
        return []
    return crud.get_users(db, skip=skip, limit=limit, company_id=comp_id)

@app.post("/api/users", response_model=schemas.UserResponse)
def create_new_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin_or_manager)):
    if user.role == "user":
        user = user.model_copy(update={"role": "sales_representative"})

    if current_user.role == "manager":
        if user.role != "sales_representative":
            raise HTTPException(status_code=403, detail="Managers may only create sales representative accounts")
        user = user.model_copy(update={"company_id": current_user.company_id})
        return crud.create_user(db=db, user=user)

    if current_user.role == "super_admin":
        allowed_roles = ("super_admin", "admin", "manager", "sales_representative")
        if user.role not in allowed_roles:
            raise HTTPException(status_code=400, detail=f"role must be one of {allowed_roles}")
        return crud.create_user(db=db, user=user)

    if user.role == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot create super admin")
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Only super administrators can create company administrators")
    if user.role not in ("manager", "sales_representative"):
        raise HTTPException(status_code=403, detail="Invalid role for company administrator")
    user = user.model_copy(update={"company_id": current_user.company_id})
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
def get_companies_list(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_active_user)):
    if roles.is_super_admin(current_user.role):
        return crud.get_companies(db, skip=skip, limit=limit)
    if roles.is_company_admin(current_user.role) and current_user.company_id:
        c = crud.get_company(db, current_user.company_id)
        return [c] if c else []
    raise HTTPException(status_code=403, detail="Not permitted to list companies")


@app.patch("/api/companies/{company_id}", response_model=schemas.CompanyResponse)
def patch_company(
    company_id: str,
    body: schemas.CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    if roles.is_super_admin(current_user.role):
        pass
    elif roles.is_company_admin(current_user.role) and current_user.company_id == company_id:
        pass
    else:
        raise HTTPException(status_code=403, detail="Not permitted to update this company")
    c = crud.update_company(db, company_id, body)
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")
    return c


@app.delete("/api/companies/{company_id}")
def remove_company(
    company_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_super_admin),
):
    company = crud.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    if db.query(models.User).filter(models.User.company_id == company_id).count() > 0:
        raise HTTPException(status_code=400, detail="Reassign or remove users before deleting this company")
    crud.delete_company(db, company_id)
    return {"status": "deleted"}

# -------- TELEGRAM CHAT --------
@app.get("/api/chat/{contact_id}", response_model=List[schemas.ChatMessageOut])
def get_chat_history(
    contact_id: str,
    limit: int = 100,
    deal_id: Optional[str] = Query(None, alias="dealId"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    tenant_access.ensure_chat_contact_access(db, current_user, contact_id, deal_id)
    return crud.get_chat_messages(db, contact_id=contact_id, limit=limit)

@app.post("/api/chat/send", response_model=schemas.ChatMessageOut)
async def send_message_to_client(
    msg: schemas.ChatMessageSend,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Find the contact to get their telegram_id
    contact = db.query(models.Contact).filter(models.Contact.id == msg.contactId).first()
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact with ID {msg.contactId} not found")
    tenant_access.ensure_chat_contact_access(db, current_user, contact.id, msg.dealId)
    if not contact.telegram_id:
        raise HTTPException(status_code=400, detail="Contact has no Telegram ID linked. Ask the client to /start the bot and provide their ID.")

    # Send via Telegram
    success = await send_telegram_message(contact.telegram_id, msg.content)
    if not success:
        raise HTTPException(status_code=502, detail="Failed to deliver message to Telegram")

    # Save to DB
    saved = crud.create_chat_message(
        db,
        contact_id=msg.contactId,
        deal_id=msg.dealId,
        sender_role="manager",
        sender_id=current_user.id,
        sender_name=current_user.name,
        content=msg.content,
    )
    return saved

class StartChatRequest(BaseModel):
    telegram_id: str
    message: Optional[str] = None


@app.post("/api/chat/start")
async def start_chat_by_telegram_id(
    req: StartChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    telegram_id = req.telegram_id.strip()
    
    # Simple validation: common mistake is entering @username
    if telegram_id.startswith("@"):
         raise HTTPException(status_code=400, detail="Please enter a numeric Telegram ID, not a username.")
    
    # Check if contact already exists with this telegram_id
    contact = crud.get_contact_by_telegram_id(db, telegram_id)
    
    if not contact:
        print(f">>> CRM: Starting chat with NEW telegram_id: {telegram_id}")
        # Try to get user info from Telegram
        tg_info = await get_telegram_user_info(telegram_id)
        tg_name = "Unknown"
        if tg_info:
            first = tg_info.get("first_name", "")
            last = tg_info.get("last_name", "")
            tg_name = f"{first} {last}".strip() or "Unknown"
        
        avatar = "".join(w[0] for w in tg_name.split()[:2]).upper() if tg_name != "Unknown" else "?"

        company_id = current_user.company_id
        if not company_id and current_user.role == "super_admin":
            default_company = db.query(models.Company).first()
            company_id = default_company.id if default_company else None

        # Create a draft contact
        import uuid
        contact = models.Contact(
            id=str(uuid.uuid4()),
            name=tg_name,
            email=f"tg_{telegram_id}@placeholder.crm",
            phone="",
            company="",
            role="Client",
            status="Prospect",
            avatar=avatar,
            telegram_id=telegram_id,
            companyId=company_id,
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
    else:
        print(f">>> CRM: Starting chat with EXISTING contact: {contact.name} (ID: {contact.id})")
        tenant_access.ensure_contact_access(db, current_user, contact.id)

    # Send greeting if message provided
    delivered = False
    if req.message:
        print(f">>> CRM: Sending greeting to {telegram_id}...")
        delivered = await send_telegram_message(telegram_id, req.message)
        # Always save to DB so manager sees it in chat history
        crud.create_chat_message(
            db,
            contact_id=contact.id,
            deal_id=None,
            sender_role="manager",
            sender_id=current_user.id,
            sender_name=current_user.name,
            content=req.message,
        )
    
    return {
        "status": "ok",
        "contactId": contact.id,
        "contactName": contact.name,
        "telegram_id": telegram_id,
        "is_new": contact.status == "Prospect",
        "delivered": delivered,
    }

@app.post("/api/chat/upload", response_model=schemas.ChatMessageOut)
async def upload_image_to_client(
    contactId: str = Form(...),
    dealId: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    contact = tenant_access.ensure_chat_contact_access(db, current_user, contactId, dealId)
    if not contact.telegram_id:
        raise HTTPException(status_code=400, detail="Contact has no Telegram linked")

    # Save uploaded file
    import uuid
    ext = os.path.splitext(file.filename or "img.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join("uploads", "chat", filename)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    image_url = f"/uploads/chat/{filename}"

    # Send to Telegram
    await send_telegram_photo(contact.telegram_id, save_path)

    # Save to DB
    saved = crud.create_chat_message(
        db,
        contact_id=contactId,
        deal_id=dealId or None,
        sender_role="manager",
        sender_id=current_user.id,
        sender_name=current_user.name,
        content=image_url,
        message_type="image",
    )
    return saved
