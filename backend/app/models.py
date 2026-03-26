from sqlalchemy import Column, String, Integer, Float, DateTime
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
