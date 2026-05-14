from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey
from app.database import Base
import datetime
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
    userId = Column(String, nullable=True)
    createdById = Column(String, nullable=True)
    companyId = Column(String, nullable=True)
    notes = Column(String, nullable=True)

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
    companyId = Column(String, nullable=True)
    telegram_id = Column(String, nullable=True, unique=True)
    country_iso2 = Column(String(2), nullable=True, index=True)
    city = Column(String(128), nullable=True, index=True)



class Activity(Base):
    __tablename__ = "activities"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    type = Column(String) # call, email, meeting, deal_won, etc.
    entityType = Column(String) # contact, lead, deal, seller
    entityId = Column(String)
    description = Column(String)
    timestamp = Column(String)

class Note(Base):
    __tablename__ = "notes"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    dealId = Column(String, index=True)
    userId = Column(String, index=True)
    content = Column(String)
    createdAt = Column(DateTime, default=datetime.datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    contactId = Column(String, index=True)        # which contact this chat belongs to
    dealId = Column(String, nullable=True, index=True)  # optionally linked to a deal
    senderRole = Column(String)                    # 'manager' or 'client'
    senderId = Column(String, nullable=True)       # User.id for manager, telegram_id for client
    senderName = Column(String)
    content = Column(String)
    messageType = Column(String, default="text")  # 'text' or 'image'
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    entityType = Column(String)
    entityId = Column(String, nullable=True)
    category = Column(String)
    title = Column(String)
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

class DealStageHistory(Base):
    __tablename__ = "deal_stage_history"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    deal_id = Column(String, ForeignKey("deals.id", ondelete="CASCADE"), index=True)
    old_stage = Column(String)
    new_stage = Column(String)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)
    changed_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

class CommunicationLog(Base):
    __tablename__ = "communication_logs"
    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    type = Column(String, index=True)  # call, email, telegram, meeting
    direction = Column(String)  # inbound, outbound
    contact_id = Column(String, ForeignKey("contacts.id", ondelete="CASCADE"), index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    duration = Column(Integer, nullable=True) # seconds for calls
    status = Column(String) # completed, missed, sent, opened, bounced
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    metadata_json = Column(JSON, nullable=True) # extra details like email subject, record url
