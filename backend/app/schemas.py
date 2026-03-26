from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DealBase(BaseModel):
    title: str
    contactId: Optional[str] = None
    leadId: Optional[str] = None
    value: float = 0.0
    stage: str
    sellerId: Optional[str] = None
    closedAt: Optional[datetime] = None

class DealCreate(DealBase):
    pass

class DealUpdate(BaseModel):
    title: Optional[str] = None
    stage: Optional[str] = None
    value: Optional[float] = None

class Deal(DealBase):
    id: str

    class Config:
        from_attributes = True
