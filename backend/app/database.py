from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
