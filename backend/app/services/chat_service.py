"""Telegram-чат: история, отправка, старт, загрузка файлов."""

import os
import uuid as uuid_lib
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile

from app import crud, models, schemas, tenant_access
from app.telegram_bot import send_telegram_message, get_telegram_user_info, send_telegram_photo


class ChatService:
    def get_history(self, db: Session, user: models.User, contact_id: str, limit: int, deal_id: Optional[str]):
        tenant_access.ensure_chat_contact_access(db, user, contact_id, deal_id)
        return crud.get_chat_messages(db, contact_id=contact_id, limit=limit)

    async def send_message(self, db: Session, user: models.User, msg: schemas.ChatMessageSend) -> models.ChatMessage:
        contact = db.query(models.Contact).filter(models.Contact.id == msg.contactId).first()
        if not contact:
            raise HTTPException(status_code=404, detail=f"Contact with ID {msg.contactId} not found")
        tenant_access.ensure_chat_contact_access(db, user, contact.id, msg.dealId)
        if not contact.telegram_id:
            raise HTTPException(
                status_code=400,
                detail="Contact has no Telegram ID linked. Ask the client to /start the bot and provide their ID.",
            )
        success = await send_telegram_message(contact.telegram_id, msg.content)
        if not success:
            raise HTTPException(status_code=502, detail="Failed to deliver message to Telegram")
        return crud.create_chat_message(
            db,
            contact_id=msg.contactId,
            deal_id=msg.dealId,
            sender_role="manager",
            sender_id=user.id,
            sender_name=user.name,
            content=msg.content,
        )

    async def start_by_telegram_id(
        self,
        db: Session,
        user: models.User,
        req: schemas.ChatStartByTelegramRequest,
    ) -> dict:
        telegram_id = req.telegram_id.strip()
        if telegram_id.startswith("@"):
            raise HTTPException(status_code=400, detail="Please enter a numeric Telegram ID, not a username.")

        contact = crud.get_contact_by_telegram_id(db, telegram_id)

        if not contact:
            tg_info = await get_telegram_user_info(telegram_id)
            tg_name = "Unknown"
            if tg_info:
                first = tg_info.get("first_name", "")
                last = tg_info.get("last_name", "")
                tg_name = f"{first} {last}".strip() or "Unknown"

            avatar = "".join(w[0] for w in tg_name.split()[:2]).upper() if tg_name != "Unknown" else "?"

            company_id = user.company_id
            if not company_id and user.role == "super_admin":
                default_company = db.query(models.Company).first()
                company_id = default_company.id if default_company else None

            contact = models.Contact(
                id=str(uuid_lib.uuid4()),
                name=tg_name,
                email=f"tg_{telegram_id}@placeholder.crm",
                phone="",
                company="",
                role="Client",
                status="Prospect",
                avatar=avatar,
                telegram_id=telegram_id,
                companyId=company_id,
            )
            db.add(contact)
            db.commit()
            db.refresh(contact)
        else:
            tenant_access.ensure_contact_access(db, user, contact.id)

        delivered = False
        if req.message:
            delivered = await send_telegram_message(telegram_id, req.message)
            crud.create_chat_message(
                db,
                contact_id=contact.id,
                deal_id=None,
                sender_role="manager",
                sender_id=user.id,
                sender_name=user.name,
                content=req.message,
            )

        return {
            "status": "ok",
            "contactId": contact.id,
            "contactName": contact.name,
            "telegram_id": telegram_id,
            "is_new": contact.status == "Prospect",
            "delivered": delivered,
        }

    async def upload_image(
        self,
        db: Session,
        user: models.User,
        contact_id: str,
        deal_id: Optional[str],
        file: UploadFile,
    ) -> models.ChatMessage:
        contact = tenant_access.ensure_chat_contact_access(db, user, contact_id, deal_id)
        if not contact.telegram_id:
            raise HTTPException(status_code=400, detail="Contact has no Telegram linked")

        ext = os.path.splitext(file.filename or "img.jpg")[1] or ".jpg"
        filename = f"{uuid_lib.uuid4().hex}{ext}"
        save_path = os.path.join("uploads", "chat", filename)
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        image_url = f"/uploads/chat/{filename}"
        await send_telegram_photo(contact.telegram_id, save_path)

        return crud.create_chat_message(
            db,
            contact_id=contact_id,
            deal_id=deal_id or None,
            sender_role="manager",
            sender_id=user.id,
            sender_name=user.name,
            content=image_url,
            message_type="image",
        )


chat_service = ChatService()

os.makedirs("uploads/chat", exist_ok=True)
