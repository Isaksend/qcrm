from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app import auth, models, schemas
from app.database import get_db
from app.services.chat_service import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/{contact_id}", response_model=List[schemas.ChatMessageOut])
def get_chat_history(
    contact_id: str,
    limit: int = 100,
    deal_id: Optional[str] = Query(None, alias="dealId"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return chat_service.get_history(db, current_user, contact_id, limit, deal_id)


@router.post("/send", response_model=schemas.ChatMessageOut)
async def send_message_to_client(
    msg: schemas.ChatMessageSend,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return await chat_service.send_message(db, current_user, msg)


@router.post("/start")
async def start_chat_by_telegram_id(
    req: schemas.ChatStartByTelegramRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return await chat_service.start_by_telegram_id(db, current_user, req)


@router.post("/upload", response_model=schemas.ChatMessageOut)
async def upload_image_to_client(
    contactId: str = Form(...),
    dealId: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return await chat_service.upload_image(db, current_user, contactId, dealId, file)
