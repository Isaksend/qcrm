from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# We will use SQLite by default if POSTGRES_URL is not set for easier local development testing,
# but it's meant for PostgreSQL: "postgresql://user:password@localhost/dbname"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tinycrm.db")

# check if sqlite vs postgres
if DATABASE_URL.startswith("sqlite"):
	connect_args = {"check_same_thread": False}
	print("Using sqlite")
else:
	connect_args = {}
	print("Using postgres")

engine = create_engine(
    DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_deals_created_at_column() -> None:
    """Add deals.createdAt when migration was not applied yet."""
    try:
        insp = inspect(engine)
        if not insp.has_table("deals"):
            return
        names = {c["name"] for c in insp.get_columns("deals")}
        has_created = "createdAt" in names or any(n.lower() == "createdat" for n in names)
        if not has_created:
            with engine.begin() as conn:
                if DATABASE_URL.startswith("sqlite"):
                    conn.execute(text('ALTER TABLE deals ADD COLUMN "createdAt" DATETIME'))
                else:
                    conn.execute(
                        text('ALTER TABLE deals ADD COLUMN IF NOT EXISTS "createdAt" TIMESTAMP')
                    )
        with engine.begin() as conn:
            if DATABASE_URL.startswith("sqlite"):
                conn.execute(
                    text('UPDATE deals SET "createdAt" = CURRENT_TIMESTAMP WHERE "createdAt" IS NULL')
                )
            else:
                conn.execute(text('UPDATE deals SET "createdAt" = NOW() WHERE "createdAt" IS NULL'))
    except Exception as exc:
        logging.getLogger("uvicorn.error").warning("ensure_deals_created_at_column: %s", exc)


def ensure_deals_created_by_column() -> None:
    """Если колонка deals.createdById ещё не создана (миграция не прогонялась), добавляем — иначе SELECT по Deal падает с 500."""
    try:
        insp = inspect(engine)
        if not insp.has_table("deals"):
            return
        names = {c["name"] for c in insp.get_columns("deals")}
        if "createdById" in names:
            return
        # PostgreSQL без кавычек мог дать lowercase
        if any(n.lower() == "createdbyid" for n in names):
            return
        with engine.begin() as conn:
            if DATABASE_URL.startswith("sqlite"):
                conn.execute(text('ALTER TABLE deals ADD COLUMN "createdById" TEXT'))
            else:
                conn.execute(text('ALTER TABLE deals ADD COLUMN IF NOT EXISTS "createdById" VARCHAR'))
    except Exception as exc:
        logging.getLogger("uvicorn.error").warning("ensure_deals_created_by_column: %s", exc)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
