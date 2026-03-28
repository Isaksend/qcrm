"""
Telegram Bot Bridge for Tiny CRM.
- Auto-registers new clients via a Q&A flow (name → phone → company).
- Receives messages from registered clients and saves them to CRM.
- Allows managers to reply from the CRM UI back to Telegram.
"""
import os
import asyncio
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

logger = logging.getLogger("telegram_bot")

_polling_task = None
_last_update_id = 0

# In-memory registration state machine
# Key: telegram_id (str), Value: dict with step info
_registration_state: dict[str, dict] = {}


async def send_telegram_message(chat_id: str, text: str) -> bool:
    """Send a message TO a Telegram user (client)."""
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{API_BASE}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
            if res.status_code == 200:
                return True
            else:
                logger.warning(f"Telegram sendMessage failed: {res.text}")
                return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


async def get_telegram_user_info(chat_id: str) -> dict | None:
    """Fetch user profile info from Telegram (for username, photo, etc.)."""
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{API_BASE}/getChat",
                json={"chat_id": chat_id},
                timeout=10,
            )
            if res.status_code == 200:
                return res.json().get("result")
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
    return None


async def download_telegram_file(file_id: str, save_dir: str = "uploads/chat") -> str | None:
    """Download a file from Telegram by file_id and save locally. Returns local path."""
    import uuid as _uuid
    os.makedirs(save_dir, exist_ok=True)
    try:
        async with httpx.AsyncClient() as client:
            # Step 1: Get file path from Telegram
            res = await client.post(
                f"{API_BASE}/getFile",
                json={"file_id": file_id},
                timeout=10,
            )
            if res.status_code != 200:
                return None
            file_path = res.json()["result"]["file_path"]
            ext = os.path.splitext(file_path)[1] or ".jpg"

            # Step 2: Download the file
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
            dl = await client.get(file_url, timeout=30)
            if dl.status_code != 200:
                return None

            # Step 3: Save locally
            filename = f"{_uuid.uuid4().hex}{ext}"
            local_path = os.path.join(save_dir, filename)
            with open(local_path, "wb") as f:
                f.write(dl.content)

            return f"/uploads/chat/{filename}"
    except Exception as e:
        logger.error(f"Failed to download Telegram file: {e}")
        return None


async def send_telegram_photo(chat_id: str, photo_path: str, caption: str = "") -> bool:
    """Send a photo TO a Telegram user."""
    try:
        abs_path = os.path.abspath(photo_path)
        async with httpx.AsyncClient() as client:
            with open(abs_path, "rb") as f:
                res = await client.post(
                    f"{API_BASE}/sendPhoto",
                    data={"chat_id": chat_id, "caption": caption},
                    files={"photo": ("image.jpg", f, "image/jpeg")},
                    timeout=30,
                )
                return res.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send Telegram photo: {e}")
        return False


async def _handle_registration(telegram_id: str, text: str, first_name: str):
    """Handle multi-step registration flow for a new client."""
    state = _registration_state.get(telegram_id)

    if not state:
        # Step 1: Ask for full name
        _registration_state[telegram_id] = {"step": "name", "first_name": first_name}
        await send_telegram_message(
            telegram_id,
            "👋 Добро пожаловать! Я бот компании.\n\n"
            "Давайте познакомимся, чтобы ваш менеджер мог связаться с вами.\n\n"
            "📝 <b>Как вас зовут?</b> (Имя и Фамилия)"
        )
        return True

    step = state["step"]

    if step == "name":
        state["name"] = text.strip()
        state["step"] = "phone"
        await send_telegram_message(
            telegram_id,
            f"Приятно познакомиться, <b>{state['name']}</b>! 🤝\n\n"
            "📱 <b>Ваш номер телефона?</b>\n"
            "(или напишите «пропустить»)"
        )
        return True

    elif step == "phone":
        phone = text.strip()
        if phone.lower() in ("пропустить", "skip", "-"):
            phone = ""
        state["phone"] = phone
        state["step"] = "company"
        await send_telegram_message(
            telegram_id,
            "🏢 <b>Название вашей компании?</b>\n"
            "(или напишите «пропустить»)"
        )
        return True

    elif step == "company":
        company = text.strip()
        if company.lower() in ("пропустить", "skip", "-"):
            company = ""
        state["company"] = company

        # Registration complete — create contact in CRM
        from app.database import SessionLocal
        from app import crud, models

        db = SessionLocal()
        try:
            name = state.get("name", first_name)
            avatar = "".join(w[0] for w in name.split()[:2]).upper() if name else "?"

            # Check if already exists (race condition guard)
            existing = crud.get_contact_by_telegram_id(db, telegram_id)
            if existing:
                del _registration_state[telegram_id]
                await send_telegram_message(telegram_id, "✅ Вы уже зарегистрированы! Можете писать сообщения менеджеру.")
                return True

            # Get default company for auto-registration
            default_company = db.query(models.Company).first()
            company_id = default_company.id if default_company else None

            # Create contact
            import uuid
            db_contact = models.Contact(
                id=str(uuid.uuid4()),
                name=name,
                email=f"tg_{telegram_id}@placeholder.crm",
                phone=state.get("phone", ""),
                company=state.get("company", ""),
                role="Client",
                status="Prospect",
                avatar=avatar,
                telegram_id=telegram_id,
                companyId=company_id,
            )
            db.add(db_contact)
            db.commit()

            logger.info(f"Auto-registered contact: {name} (tg: {telegram_id})")

            await send_telegram_message(
                telegram_id,
                f"✅ <b>Регистрация завершена!</b>\n\n"
                f"👤 {name}\n"
                f"📱 {state.get('phone') or '—'}\n"
                f"🏢 {state.get('company') or '—'}\n\n"
                "Теперь вы можете писать сюда — ваш менеджер увидит сообщения в CRM. 💬"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to auto-register contact: {e}")
            await send_telegram_message(telegram_id, "⚠️ Произошла ошибка при регистрации. Попробуйте позже.")
        finally:
            db.close()
            del _registration_state[telegram_id]

        return True

    return False


async def _process_update(update: dict):
    """Process a single Telegram update."""
    message = update.get("message")
    if not message:
        return

    # Handle contact sharing (phone number button)
    if message.get("contact"):
        telegram_id = str(message["from"]["id"])
        phone = message["contact"].get("phone_number", "")
        if telegram_id in _registration_state and _registration_state[telegram_id]["step"] == "phone":
            _registration_state[telegram_id]["phone"] = phone
            _registration_state[telegram_id]["step"] = "company"
            await send_telegram_message(
                telegram_id,
                f"📱 Телефон сохранён: <b>{phone}</b>\n\n"
                "🏢 <b>Название вашей компании?</b>\n"
                "(или напишите «пропустить»)"
            )
        return

    text = message.get("text", "")

    telegram_id = str(message["from"]["id"])
    first_name = message["from"].get("first_name", "Unknown")
    last_name = message["from"].get("last_name", "")
    sender_name = f"{first_name} {last_name}".strip()

    # Handle photo messages from clients
    if message.get("photo"):
        from app.database import SessionLocal
        from app import crud

        db = SessionLocal()
        try:
            contact = crud.get_contact_by_telegram_id(db, telegram_id)
            if not contact:
                await send_telegram_message(telegram_id, "Сначала зарегистрируйтесь — отправьте /start")
                return
            # Download largest photo
            photo = message["photo"][-1]
            local_url = await download_telegram_file(photo["file_id"])
            if local_url:
                caption = message.get("caption", "")
                crud.create_chat_message(
                    db,
                    contact_id=contact.id,
                    deal_id=None,
                    sender_role="client",
                    sender_id=telegram_id,
                    sender_name=contact.name,
                    content=local_url,
                    message_type="image",
                )
                if caption:
                    crud.create_chat_message(
                        db,
                        contact_id=contact.id,
                        deal_id=None,
                        sender_role="client",
                        sender_id=telegram_id,
                        sender_name=contact.name,
                        content=caption,
                    )
                logger.info(f"Saved photo from {contact.name}")
        finally:
            db.close()
        return

    if not text:
        return

    # Handle /start — always restart registration if not registered
    if text.startswith("/start"):
        from app.database import SessionLocal
        from app import crud

        db = SessionLocal()
        try:
            contact = crud.get_contact_by_telegram_id(db, telegram_id)
            if contact:
                await send_telegram_message(
                    telegram_id,
                    f"👋 Здравствуйте, <b>{contact.name}</b>!\n\n"
                    "Вы уже зарегистрированы. Просто пишите сюда — менеджер увидит ваше сообщение в CRM. 💬"
                )
                return
        finally:
            db.close()

        # Start registration
        if telegram_id in _registration_state:
            del _registration_state[telegram_id]
        await _handle_registration(telegram_id, text, first_name)
        return

    # Check if user is in registration flow
    if telegram_id in _registration_state:
        await _handle_registration(telegram_id, text, first_name)
        return

    # Regular message — save to DB if contact exists
    from app.database import SessionLocal
    from app import crud

    db = SessionLocal()
    try:
        contact = crud.get_contact_by_telegram_id(db, telegram_id)
        if not contact:
            # Not registered — start registration flow
            await _handle_registration(telegram_id, text, first_name)
            return

        # Save message from client
        crud.create_chat_message(
            db,
            contact_id=contact.id,
            deal_id=None,
            sender_role="client",
            sender_id=telegram_id,
            sender_name=contact.name,
            content=text,
        )
        logger.info(f"Saved message from {contact.name}")
    finally:
        db.close()


async def _poll_updates():
    """Long-polling loop to fetch updates from Telegram."""
    global _last_update_id
    print(">>> Telegram: Polling started...")
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                res = await client.get(
                    f"{API_BASE}/getUpdates",
                    params={
                        "offset": _last_update_id + 1,
                        "timeout": 30,
                    },
                    timeout=40,
                )
                if res.status_code == 200:
                    data = res.json()
                    for update in data.get("result", []):
                        _last_update_id = update["update_id"]
                        try:
                            await _process_update(update)
                        except Exception as e:
                            print(f">>> Telegram: Error processing update: {e}")
                            logger.error(f"Error processing update: {e}")
                else:
                    print(f">>> Telegram: API returned {res.status_code}")
                    await asyncio.sleep(5)
            except httpx.ReadTimeout:
                continue
            except Exception as e:
                print(f">>> Telegram: Polling loop error: {e}")
                await asyncio.sleep(5)


def start_polling():
    """Start the background polling task (called from FastAPI startup)."""
    global _polling_task
    if not BOT_TOKEN:
        print(">>> Telegram: Bot token missing! Integration disabled.")
        return
    
    # Check if we are in an event loop
    try:
        loop = asyncio.get_running_loop()
        _polling_task = loop.create_task(_poll_updates())
        print(">>> Telegram: Background task created on current loop.")
    except RuntimeError:
        # No running loop, create one manually (for CLI use cases etc)
        loop = asyncio.get_event_loop()
        _polling_task = loop.create_task(_poll_updates())
        print(">>> Telegram: Background task created on event loop.")


def stop_polling():
    """Cancel the polling task (called from FastAPI shutdown)."""
    global _polling_task
    if _polling_task:
        _polling_task.cancel()
        print(">>> Telegram: Polling stopped.")
