from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DealBase(BaseModel):
    title: str
    contactId: Optional[str] = None
    leadId: Optional[str] = None
    value: float = 0.0
    stage: str
    userId: Optional[str] = None
    companyId: Optional[str] = None
    notes: Optional[str] = None
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

class ContactBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    status: str = "Active"
    avatar: Optional[str] = None
    revenue: float = 0.0
    lastContact: Optional[str] = None
    tags: Optional[List[str]] = None
    companyId: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class Contact(ContactBase):
    id: str

    class Config:
        from_attributes = True



class ActivityBase(BaseModel):
    type: str
    entityType: str
    entityId: str
    description: str
    timestamp: str

class ActivityCreate(ActivityBase):
    pass

class Activity(ActivityBase):
    id: str

    class Config:
        from_attributes = True

class NoteBase(BaseModel):
    dealId: str
    content: str

class NoteCreate(NoteBase):
    pass

class Note(NoteBase):
    id: str
    userId: str
    createdAt: datetime

    class Config:
        from_attributes = True

class AIInsightBase(BaseModel):
    entityType: str
    entityId: Optional[str] = None
    category: str
    title: str
    content: str
    confidence: int
    suggestions: List[str] = []

class AIInsightCreate(AIInsightBase):
    pass

class AIInsight(AIInsightBase):
    id: str

    class Config:
        from_attributes = True

# --- Users, Auth & Companies ---

class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    name: str
    email: str
    role: str = "user"
    company_id: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    is_active: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
