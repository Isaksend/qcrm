from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DealBase(BaseModel):
    title: str
    contactId: Optional[str] = None
    leadId: Optional[str] = None
    value: float = 0.0
    currency: str = "KTZ"
    stage: str
    userId: Optional[str] = None
    createdById: Optional[str] = None
    companyId: Optional[str] = None
    notes: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.now)
    closedAt: Optional[datetime] = None

class DealCreate(DealBase):
    pass

class DealUpdate(BaseModel):
    title: Optional[str] = None
    stage: Optional[str] = None
    value: Optional[float] = None
    contactId: Optional[str] = None
    leadId: Optional[str] = None
    notes: Optional[str] = None
    userId: Optional[str] = None

class Deal(DealBase):
    id: str

    class Config:
        from_attributes = True


class DealHistoryEntry(BaseModel):
    """Запись истории изменений сделки."""

    id: str
    deal_id: str
    field: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_at: datetime
    changed_by_id: Optional[str] = None
    changed_by_name: Optional[str] = None

    class Config:
        from_attributes = True


class DealTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    dueAt: Optional[datetime] = None
    """Исполнитель; по умолчанию на бэкенде — ответственный по сделке или текущий пользователь."""
    assignedUserId: Optional[str] = None


class DealTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    dueAt: Optional[datetime] = None
    isDone: Optional[int] = Field(None, ge=0, le=1)
    assignedUserId: Optional[str] = None


class DealTask(BaseModel):
    id: str
    dealId: str
    title: str
    dueAt: Optional[datetime] = None
    isDone: int
    createdBy: Optional[str] = None
    createdAt: datetime
    assignedUserId: Optional[str] = None

    class Config:
        from_attributes = True


class MyDealTaskItem(BaseModel):
    id: str
    dealId: str
    dealTitle: str
    title: str
    dueAt: Optional[datetime] = None
    assignedUserId: Optional[str] = None
    createdAt: datetime


class MyDealTasksResponse(BaseModel):
    openCount: int
    items: List[MyDealTaskItem]


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
    telegram_id: Optional[str] = None
    country_iso2: Optional[str] = None
    city: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class Contact(ContactBase):
    id: str

    class Config:
        from_attributes = True


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    avatar: Optional[str] = None
    revenue: Optional[float] = None
    lastContact: Optional[str] = None
    tags: Optional[List[str]] = None
    companyId: Optional[str] = None
    telegram_id: Optional[str] = None
    country_iso2: Optional[str] = None
    city: Optional[str] = None

class MLPredictionBase(BaseModel):
    contactId: str
    modelType: str
    score: float
    riskTier: str
    predictedAt: datetime = Field(default_factory=datetime.now)

class MLPrediction(MLPredictionBase):
    id: str
    userId: str

    class Config:
        from_attributes = True

class MLPredictionCreate(MLPredictionBase):
	pass

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


class ActivityOut(Activity):
    """Activity with display metadata for timeline UI."""

    entityLabel: Optional[str] = None
    entityLink: Optional[str] = None
    isSystem: bool = False


class ActivityUpdate(BaseModel):
    type: Optional[str] = None
    entityType: Optional[str] = None
    entityId: Optional[str] = None
    description: Optional[str] = None
    timestamp: Optional[str] = None

class NoteBase(BaseModel):
    dealId: str
    content: str

class NoteCreate(NoteBase):
    pass

class Note(NoteBase):
    id: str
    userId: str
    createdAt: datetime
    authorName: Optional[str] = None

    class Config:
        from_attributes = True

class ChatMessageBase(BaseModel):
    contactId: str
    dealId: Optional[str] = None
    content: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageOut(ChatMessageBase):
    id: str
    senderRole: str
    senderId: Optional[str] = None
    senderName: str
    messageType: str = "text"
    timestamp: datetime

    class Config:
        from_attributes = True

class ChatMessageSend(BaseModel):
    contactId: str
    dealId: Optional[str] = None
    content: str


class ChatStartByTelegramRequest(BaseModel):
    telegram_id: str
    message: Optional[str] = None


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


class CompanyBase(BaseModel):
    name: str
    industry: Optional[str] = ""
    size: Optional[int] = 1
    country: str
    website: str
    timezone: str = Field(default="UTC", description="IANA, e.g. Europe/Moscow")
    created_at: datetime = Field(default_factory=datetime.now)

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: str
    class Config:
        from_attributes = True


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    timezone: Optional[str] = None

class UserBase(BaseModel):
    name: str
    email: str
    role: str = "sales_representative"
    company_id: Optional[str] = None

class UserCreate(UserBase):
    password: str


class UserAdminUpdate(BaseModel):
    """Частичное обновление пользователя (только super_admin)."""

    name: Optional[str] = None
    role: Optional[str] = None
    company_id: Optional[str] = None
    is_active: Optional[int] = None


class UserResponse(UserBase):
    id: str
    is_active: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    email: Optional[str] = None
