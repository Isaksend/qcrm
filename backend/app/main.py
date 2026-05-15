from contextlib import asynccontextmanager
import logging
import os

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db, ensure_deals_created_by_column, ensure_deals_created_at_column
from app.services.ai_service import ai_service
from app.telegram_bot import start_polling, stop_polling
from app.routers import (
    ai_router,
    analytics_router,
    auth_router,
    users_router,
    deals_router,
    contacts_router,
    activities_router,
    insights_router,
    companies_router,
    chat_router,
)
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
        logging.StreamHandler(),
    ],
)
audit_logger = logging.getLogger("audit")

os.makedirs("uploads/chat", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    ensure_deals_created_by_column()
    ensure_deals_created_at_column()
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
        audit_logger.info("Action: %s %s - Status: %s", request.method, request.url.path, response.status_code)
    return response


app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

_settings_cors = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings_cors.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router.router)
app.include_router(analytics_router.router)
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(deals_router.router)
app.include_router(contacts_router.router)
app.include_router(activities_router.router)
app.include_router(insights_router.router)
app.include_router(companies_router.router)
app.include_router(chat_router.router)


@app.get("/")
def root():
    return {"message": "Welcome to Tiny CRM Backend!"}
