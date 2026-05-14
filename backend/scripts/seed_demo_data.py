#!/usr/bin/env python3
"""
Заполнение БД демонстрационными данными для Tiny CRM.

Использование (из каталога backend):
  python scripts/seed_demo_data.py
  python scripts/seed_demo_data.py --force   # удалить предыдущий демо-набор и создать заново

Подключение к БД — через DATABASE_URL в .env (как у приложения).
Логины после сида (пароль одинаковый, см. DEMO_PASSWORD в скрипте):
  superadmin@demo.tinycrm.local — super_admin (без привязки к компании, глобальный доступ)
  admin@demo.tinycrm.local — admin
  sales1@demo.tinycrm.local, sales2@demo.tinycrm.local — sales_representative
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import uuid

# Корень backend в PYTHONPATH
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.chdir(_BACKEND_ROOT)

from sqlalchemy.orm import Session

from app import models
from app.auth import get_password_hash
from app.database import SessionLocal

DEMO_COMPANY_NAME = "Демо: Tiny CRM"
# Вторая запись без пользователей — чтобы в UI «Компании» было что показать и что безопасно удалить.
DEMO_ORPHAN_COMPANY_NAME = "Демо: Пустая организация"
DEMO_PASSWORD = "demo1234"
DEMO_USERS = [
    ("Админ Демо", "admin@demo.tinycrm.local", "admin"),
    ("Иван Продажи", "sales1@demo.tinycrm.local", "sales_representative"),
    ("Мария Продажи", "sales2@demo.tinycrm.local", "sales_representative"),
]
DEMO_SUPER_EMAIL = "superadmin@demo.tinycrm.local"
DEMO_SUPER_NAME = "Супер-админ Демо"


def _uid() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _clear_demo_bundle(db: Session) -> None:
    comp = db.query(models.Company).filter(models.Company.name == DEMO_COMPANY_NAME).first()
    if not comp:
        return
    cid = comp.id
    user_ids = [u.id for u in db.query(models.User).filter(models.User.company_id == cid).all()]
    contact_ids = [c.id for c in db.query(models.Contact).filter(models.Contact.companyId == cid).all()]
    deal_ids = [d.id for d in db.query(models.Deal).filter(models.Deal.companyId == cid).all()]

    if contact_ids:
        db.query(models.ChatMessage).filter(models.ChatMessage.contactId.in_(contact_ids)).delete(
            synchronize_session=False
        )
        db.query(models.CommunicationLog).filter(models.CommunicationLog.contact_id.in_(contact_ids)).delete(
            synchronize_session=False
        )
        db.query(models.Activity).filter(
            models.Activity.entityType == "contact", models.Activity.entityId.in_(contact_ids)
        ).delete(synchronize_session=False)
        db.query(models.AIInsight).filter(
            models.AIInsight.entityType == "contact", models.AIInsight.entityId.in_(contact_ids)
        ).delete(synchronize_session=False)
    if deal_ids:
        db.query(models.DealStageHistory).filter(models.DealStageHistory.deal_id.in_(deal_ids)).delete(
            synchronize_session=False
        )
        db.query(models.Note).filter(models.Note.dealId.in_(deal_ids)).delete(synchronize_session=False)
        db.query(models.Activity).filter(
            models.Activity.entityType == "deal", models.Activity.entityId.in_(deal_ids)
        ).delete(synchronize_session=False)
        db.query(models.AIInsight).filter(
            models.AIInsight.entityType == "deal", models.AIInsight.entityId.in_(deal_ids)
        ).delete(synchronize_session=False)

    db.query(models.Deal).filter(models.Deal.companyId == cid).delete(synchronize_session=False)
    db.query(models.Contact).filter(models.Contact.companyId == cid).delete(synchronize_session=False)
    for uid in user_ids:
        db.query(models.User).filter(models.User.id == uid).delete(synchronize_session=False)
    db.query(models.Company).filter(models.Company.id == cid).delete(synchronize_session=False)
    oc = db.query(models.Company).filter(models.Company.name == DEMO_ORPHAN_COMPANY_NAME).first()
    if oc:
        db.delete(oc)
    su = db.query(models.User).filter(models.User.email == DEMO_SUPER_EMAIL).first()
    if su:
        db.delete(su)
    db.commit()
    print("Удалён предыдущий демо-набор (включая демо super_admin).")


def _demo_exists(db: Session) -> bool:
    return (
        db.query(models.Company).filter(models.Company.name == DEMO_COMPANY_NAME).first() is not None
    )


def _ensure_demo_super_admin(db: Session) -> bool:
    """Если демо-компания уже сидилась раньше без super_admin — добавляет только его."""
    if db.query(models.User).filter(models.User.email == DEMO_SUPER_EMAIL).first():
        return False
    db.add(
        models.User(
            id=_uid(),
            name=DEMO_SUPER_NAME,
            email=DEMO_SUPER_EMAIL,
            hashed_password=get_password_hash(DEMO_PASSWORD),
            role="super_admin",
            company_id=None,
            is_active=1,
        )
    )
    db.commit()
    return True


def seed_demo_data(db: Session, *, force: bool) -> None:
    if force:
        _clear_demo_bundle(db)
    elif _demo_exists(db):
        if _ensure_demo_super_admin(db):
            print(
                "Демо-компания уже была; добавлен отсутствующий super_admin.\n"
                f"  {DEMO_SUPER_EMAIL} (super_admin) / {DEMO_PASSWORD}"
            )
        else:
            print(
                f"Демо-данные уже есть (компания «{DEMO_COMPANY_NAME}», super_admin — {DEMO_SUPER_EMAIL}). "
                "Запустите с --force для пересоздания."
            )
        return

    company = models.Company(id=_uid(), name=DEMO_COMPANY_NAME, created_at=_now_iso())
    db.add(company)
    orphan = models.Company(id=_uid(), name=DEMO_ORPHAN_COMPANY_NAME, created_at=_now_iso())
    db.add(orphan)
    db.flush()

    users: list[models.User] = []
    for name, email, role in DEMO_USERS:
        u = models.User(
            id=_uid(),
            name=name,
            email=email,
            hashed_password=get_password_hash(DEMO_PASSWORD),
            role=role,
            company_id=company.id,
            is_active=1,
        )
        db.add(u)
        users.append(u)
    db.add(
        models.User(
            id=_uid(),
            name=DEMO_SUPER_NAME,
            email=DEMO_SUPER_EMAIL,
            hashed_password=get_password_hash(DEMO_PASSWORD),
            role="super_admin",
            company_id=None,
            is_active=1,
        )
    )
    db.flush()

    admin = users[0]
    sales1, sales2 = users[1], users[2]

    contacts_spec = [
        {
            "name": "ТОО «Астана Логистик»",
            "email": "demo.contact.astana@example.com",
            "phone": "+7 7172 555 0101",
            "company": "Астана Логистик",
            "role": "Директор по закупкам",
            "status": "Active",
            "avatar": "АЛ",
            "revenue": 12_500_000.0,
            "tags": ["B2B", "логистика"],
            "telegram_id": "1000009001",
            "country_iso2": "KZ",
            "city": "Астана",
        },
        {
            "name": "Алия Касымова",
            "email": "demo.contact.aliya@example.com",
            "phone": "+7 707 222 3344",
            "company": "Retail Group",
            "role": "Менеджер",
            "status": "Prospect",
            "avatar": "АК",
            "revenue": 0.0,
            "tags": ["розница", "холодный"],
            "telegram_id": "1000009002",
            "country_iso2": "KZ",
            "city": "Алматы",
        },
        {
            "name": "John Smith",
            "email": "demo.contact.jsmith@example.com",
            "phone": "+1 415 555 0199",
            "company": "TechImport LLC",
            "role": "VP Sales",
            "status": "Active",
            "avatar": "JS",
            "revenue": 420_000.0,
            "tags": ["export", "SaaS"],
            "telegram_id": None,
            "country_iso2": "US",
            "city": "San Francisco",
        },
        {
            "name": "Berlin GmbH — отдел продаж",
            "email": "demo.contact.berlin@example.com",
            "phone": "+49 30 12345678",
            "company": "Berlin GmbH",
            "role": "Einkauf",
            "status": "Inactive",
            "avatar": "BG",
            "revenue": 88_000.0,
            "tags": ["EU", "партнёр"],
            "telegram_id": None,
            "country_iso2": "DE",
            "city": "Berlin",
        },
        {
            "name": "Данияр Ермеков",
            "email": "demo.contact.daniyar@example.com",
            "phone": "+7 701 888 7766",
            "company": "СтройМонтаж",
            "role": "Главный инженер",
            "status": "Active",
            "avatar": "ДЕ",
            "revenue": 3_200_000.0,
            "tags": ["стройка", "тендер"],
            "telegram_id": None,
            "country_iso2": "KZ",
            "city": "Шымкент",
        },
    ]

    contact_rows: list[models.Contact] = []
    for spec in contacts_spec:
        c = models.Contact(
            id=_uid(),
            name=spec["name"],
            email=spec["email"],
            phone=spec["phone"],
            company=spec["company"],
            role=spec["role"],
            status=spec["status"],
            avatar=spec["avatar"],
            revenue=spec["revenue"],
            lastContact="2025-04-01",
            tags=spec["tags"],
            companyId=company.id,
            telegram_id=spec["telegram_id"],
            country_iso2=spec["country_iso2"],
            city=spec["city"],
        )
        db.add(c)
        contact_rows.append(c)
    db.flush()

    c0, c1, c2 = contact_rows[0], contact_rows[1], contact_rows[2]

    deals_spec = [
        ("Поставка оборудования — Астана Логистик", c0.id, sales1.id, "Negotiation", 8_500_000.0, "Ключевой клиент, ждём подпись."),
        ("Пилот Retail Group", c1.id, sales1.id, "Proposal", 450_000.0, "Презентация проведена."),
        ("TechImport — лицензии Q2", c2.id, sales2.id, "Discovery", 120_000.0, None),
        ("Berlin GmbH — продление", contact_rows[3].id, sales2.id, "Closed Won", 55_000.0, "Продление на год."),
        ("СтройМонтаж — КП по складу", contact_rows[4].id, sales1.id, "Closed Lost", 0.0, "Выбрали другого подрядчика."),
        ("Внутренняя сделка без контакта", None, admin.id, "Discovery", 10_000.0, "Черновик для обучения."),
    ]

    deal_rows: list[models.Deal] = []
    for title, contact_id, owner_id, stage, value, notes in deals_spec:
        d = models.Deal(
            id=_uid(),
            contactId=contact_id,
            title=title,
            value=value,
            stage=stage,
            userId=owner_id,
            createdById=owner_id,
            companyId=company.id,
            notes=notes,
        )
        db.add(d)
        deal_rows.append(d)
    db.flush()

    # История стадий для первой сделки (аналитика «скорость продаж»)
    d0 = deal_rows[0]
    t0 = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=21)
    t1 = t0 + dt.timedelta(days=5)
    t2 = t1 + dt.timedelta(days=7)
    db.add(
        models.DealStageHistory(
            id=_uid(),
            deal_id=d0.id,
            old_stage="Discovery",
            new_stage="Proposal",
            changed_at=t0,
            changed_by=sales1.id,
        )
    )
    db.add(
        models.DealStageHistory(
            id=_uid(),
            deal_id=d0.id,
            old_stage="Proposal",
            new_stage="Negotiation",
            changed_at=t2,
            changed_by=sales1.id,
        )
    )

    # Заметки к сделке
    db.add(
        models.Note(
            id=_uid(),
            dealId=d0.id,
            userId=sales1.id,
            content="Клиент запросил скидку 5% при оплате до 15 числа.",
        )
    )
    db.add(
        models.Note(
            id=_uid(),
            dealId=deal_rows[1].id,
            userId=sales1.id,
            content="Отправили коммерческое на почту.",
        )
    )

    # Активности
    acts = [
        ("call", "contact", c0.id, "Исходящий звонок: согласовали встречу"),
        ("email", "contact", c1.id, "Отправлено КП"),
        ("meeting", "deal", d0.id, "Демо продукта для закупок"),
        ("email", "deal", deal_rows[3].id, "Подписан договор на продление"),
    ]
    for typ, et, eid, desc in acts:
        db.add(
            models.Activity(
                id=_uid(),
                type=typ,
                entityType=et,
                entityId=eid,
                description=desc,
                timestamp=dt.datetime.now(dt.timezone.utc).isoformat(),
            )
        )

    # Сообщения чата (контакт с telegram_id)
    db.add(
        models.ChatMessage(
            id=_uid(),
            contactId=c0.id,
            dealId=d0.id,
            senderRole="client",
            senderId=c0.telegram_id,
            senderName=c0.name,
            content="Добрый день! Пришлите, пожалуйста, счёт на оплату.",
            messageType="text",
        )
    )
    db.add(
        models.ChatMessage(
            id=_uid(),
            contactId=c0.id,
            dealId=d0.id,
            senderRole="manager",
            senderId=sales1.id,
            senderName=sales1.name,
            content="Здравствуйте! Счёт во вложении, срок оплаты — 10 рабочих дней.",
            messageType="text",
        )
    )
    db.add(
        models.ChatMessage(
            id=_uid(),
            contactId=c1.id,
            dealId=None,
            senderRole="client",
            senderId=c1.telegram_id,
            senderName=c1.name,
            content="Можем ли мы получить тестовый доступ?",
            messageType="text",
        )
    )

    # AI insights
    db.add(
        models.AIInsight(
            id=_uid(),
            entityType="contact",
            entityId=c1.id,
            category="prediction",
            title="Вероятность конверсии",
            content="Контакт на стадии Prospect; рекомендуется назначить демо в течение недели.",
            confidence=72,
            suggestions=["Назначить демо", "Отправить кейс из логистики"],
        )
    )
    db.add(
        models.AIInsight(
            id=_uid(),
            entityType="deal",
            entityId=d0.id,
            category="risk",
            title="Риск задержки оплаты",
            content="Крупная сумма сделки — уточните процесс согласования у контрагента.",
            confidence=61,
            suggestions=["Запросить юр.лицо плательщика"],
        )
    )

    # Журнал коммуникаций (аналитика)
    for i in range(8):
        db.add(
            models.CommunicationLog(
                id=_uid(),
                type=["call", "email", "telegram"][i % 3],
                direction="outbound" if i % 2 == 0 else "inbound",
                contact_id=c0.id if i % 2 == 0 else c1.id,
                user_id=sales1.id,
                duration=180 if i % 3 == 0 else None,
                status=["completed", "sent", "opened"][i % 3],
                timestamp=dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=i * 3),
                metadata_json={"seed": True, "idx": i},
            )
        )

    db.commit()
    print("Демо-данные успешно добавлены.")
    print()
    print(f"  Компания (с данными): {DEMO_COMPANY_NAME} (id={company.id})")
    print(f"  Доп. компания без сотрудников: {DEMO_ORPHAN_COMPANY_NAME}")
    print(f"  Пароль для всех демо-пользователей: {DEMO_PASSWORD}")
    print(f"  — {DEMO_SUPER_EMAIL} (super_admin, без компании) — {DEMO_SUPER_NAME}")
    for name, email, role in DEMO_USERS:
        print(f"  — {email} ({role}) — {name}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    parser = argparse.ArgumentParser(description="Сид демо-данных Tiny CRM")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Удалить существующий демо-набор (по имени компании) и создать заново",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        seed_demo_data(db, force=args.force)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
