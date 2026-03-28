from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from app.database import Base
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Deal(Base):
    __tablename__ = "deals"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    leadId = Column(String, nullable=True)
    contactId = Column(String, nullable=True)
    title = Column(String, index=True)
    value = Column(Float, default=0.0)
    stage = Column(String, index=True) # Discovery, Proposal, Negotiation, Closed Won, Closed Lost
    closedAt = Column(DateTime, nullable=True)
    sellerId = Column(String, nullable=True)

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    role = Column(String, nullable=True)
    status = Column(String, default="Active") # Active | Inactive | Prospect
    avatar = Column(String, nullable=True)
    revenue = Column(Float, default=0.0)
    lastContact = Column(String, nullable=True)
    tags = Column(JSON, default=[])

class Seller(Base):
    __tablename__ = "sellers"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    avatar = Column(String, nullable=True)
    role = Column(String, nullable=True)
    dealsWon = Column(Integer, default=0)
    dealsClosed = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    conversionRate = Column(Float, default=0.0)
    activeLeads = Column(Integer, default=0)

class Activity(Base):
    __tablename__ = "activities"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    type = Column(String) # call, email, meeting, deal_won, etc.
    entityType = Column(String) # contact, lead, deal, seller
    entityId = Column(String)
    description = Column(String)
    timestamp = Column(String)

class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    entityType = Column(String)
    entityId = Column(String, nullable=True)
    category = Column(String)
    title = Column(String)
    content = Column(String)
    content = Column(String)
    confidence = Column(Integer)
    suggestions = Column(JSON, default=[])

class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, index=True)
    created_at = Column(String) # simple string timestamp

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user") # super_admin, admin, user
    company_id = Column(String, nullable=True) # string without explicit FK for now to avoid DB lock issues on live dev
    is_active = Column(Integer, default=1)
