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


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _days_ago(days: int) -> dt.datetime:
    return _utc_now() - dt.timedelta(days=days)


def _month_shift(year: int, month: int, delta: int) -> tuple[int, int]:
    m = month + delta
    y = year
    while m < 1:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return y, m


def _last_day_of_month(year: int, month: int) -> int:
    y, m = _month_shift(year, month, 1)
    return (dt.datetime(y, m, 1, tzinfo=dt.timezone.utc) - dt.timedelta(days=1)).day


def _at_month_day(year: int, month: int, day: int, hour: int = 12) -> dt.datetime:
    day = max(1, min(day, _last_day_of_month(year, month)))
    return dt.datetime(year, month, day, hour, 0, 0, tzinfo=dt.timezone.utc)


def _current_month_day(day: int, hour: int = 12) -> dt.datetime:
    now = _utc_now()
    return _at_month_day(now.year, now.month, day, hour)


def _previous_month_day(day: int, hour: int = 12) -> dt.datetime:
    now = _utc_now()
    py, pm = _month_shift(now.year, now.month, -1)
    return _at_month_day(py, pm, day, hour)


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
        db.query(models.DealChangeHistory).filter(models.DealChangeHistory.deal_id.in_(deal_ids)).delete(
            synchronize_session=False
        )
        db.query(models.DealTask).filter(models.DealTask.dealId.in_(deal_ids)).delete(synchronize_session=False)
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
        {
            "name": "ТОО «Qazaq Pharma»",
            "email": "demo.contact.pharma@example.com",
            "phone": "+7 727 300 4400",
            "company": "Qazaq Pharma",
            "role": "Закупки",
            "status": "Active",
            "avatar": "QP",
            "revenue": 5_600_000.0,
            "tags": ["фарма", "B2B"],
            "telegram_id": "1000009003",
            "country_iso2": "KZ",
            "city": "Алматы",
        },
        {
            "name": "Nurlan Beketov",
            "email": "demo.contact.fintech@example.com",
            "phone": "+7 708 111 2233",
            "company": "SteppePay",
            "role": "Product Lead",
            "status": "Prospect",
            "avatar": "NB",
            "revenue": 0.0,
            "tags": ["fintech", "стартап"],
            "telegram_id": None,
            "country_iso2": "KZ",
            "city": "Астана",
        },
        {
            "name": "ГУ «Цифровизация»",
            "email": "demo.contact.gov@example.com",
            "phone": "+7 7172 900 1122",
            "company": "Госзакупки KZ",
            "role": "Специалист",
            "status": "Prospect",
            "avatar": "ГЦ",
            "revenue": 0.0,
            "tags": ["гос", "тендер"],
            "telegram_id": None,
            "country_iso2": "KZ",
            "city": "Астана",
        },
        {
            "name": "Maria Costa",
            "email": "demo.contact.costa@example.com",
            "phone": "+351 21 555 7788",
            "company": "Luso Retail",
            "role": "Operations",
            "status": "Active",
            "avatar": "MC",
            "revenue": 210_000.0,
            "tags": ["EU", "розница"],
            "telegram_id": None,
            "country_iso2": "PT",
            "city": "Lisbon",
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

    # Индексы контактов для читаемости
    c = contact_rows

    # period: "current" | "previous" — календарный месяц для createdAt (закрытые: closedAt в том же месяце)
    # owner None → сделка без ответственного (userId=NULL)
    deals_spec: list[tuple] = [
        # New Request — текущий месяц
        ("Входящая заявка — логистика WMS", 0, None, "New Request", 2_400_000.0, "Лид с сайта, не назначен менеджер.", "current", 3),
        ("SteppePay — пилот API", 6, sales2.id, "New Request", 180_000.0, "Первичный интерес к интеграции.", "current", 5),
        ("Госзакупки — справочник поставщиков", 7, None, "New Request", 950_000.0, "Тендер в Q3, ответственный не назначен.", "current", 7),
        # Qualified
        ("Retail Group — квалификация бюджета", 1, sales1.id, "Qualified", 520_000.0, "Бюджет подтверждён на 2025.", "current", 9),
        ("Luso Retail — омниканал", 8, None, "Qualified", 95_000.0, "Нужно назначить владельца сделки.", "current", 11),
        ("TechImport — расширение штата", 2, sales2.id, "Qualified", 64_000.0, None, "current", 13),
        # Discovery
        ("TechImport — лицензии Q2", 2, sales2.id, "Discovery", 120_000.0, "Техническое демо запланировано.", "current", 6),
        ("Qazaq Pharma — ERP-модуль", 5, sales1.id, "Discovery", 3_100_000.0, "Сбор требований у закупок.", "current", 10),
        ("Внутренняя сделка без контакта", None, None, "Discovery", 10_000.0, "Черновик, нет контакта и ответственного.", "current", 14),
        # Proposal
        ("Пилот Retail Group", 1, sales1.id, "Proposal", 450_000.0, "Презентация проведена.", "current", 8),
        ("Berlin GmbH — апгрейд тарифа", 3, sales2.id, "Proposal", 72_000.0, "КП отправлено на немецком.", "current", 12),
        ("СтройМонтаж — складской учёт", 4, None, "Proposal", 890_000.0, "Ждём согласования сметы, без owner.", "current", 15),
        # Negotiation
        ("Поставка оборудования — Астана Логистик", 0, sales1.id, "Negotiation", 8_500_000.0, "Ключевой клиент, ждём подпись.", "current", 4),
        ("Qazaq Pharma — годовой контракт", 5, sales2.id, "Negotiation", 4_800_000.0, "Юристы на финальной ревизии.", "current", 16),
        ("Астана Логистик — сервисный пакет", 0, None, "Negotiation", 620_000.0, "Допродажа, ответственный не назначен.", "current", 18),
        # Закрытые — прошлый месяц (демо переключения периода)
        ("Berlin GmbH — продление", 3, sales2.id, "Closed Won", 55_000.0, "Продление на год.", "previous", 8, 22),
        ("TechImport — onboarding", 2, sales2.id, "Closed Won", 38_000.0, None, "previous", 5, 25),
        ("СтройМонтаж — КП по складу", 4, sales1.id, "Closed Lost", 0.0, "Выбрали другого подрядчика.", "previous", 10, 26),
        ("SteppePay — корп. тариф", 6, None, "Closed Lost", 0.0, "Отказ по цене, без ответственного.", "previous", 12, 28),
        # Закрытые — текущий месяц
        ("Астана Логистик — пилот", 0, sales1.id, "Closed Won", 1_200_000.0, "Успешный пилот.", "current", 2, 20),
        ("Luso Retail — сезонная кампания", 8, sales1.id, "Closed Won", 42_000.0, None, "current", 6, 24),
        ("Госзакупки — пилот", 7, sales2.id, "Closed Lost", 0.0, "Тендер отменён.", "current", 17, 26),
    ]

    deal_rows: list[models.Deal] = []
    for row in deals_spec:
        title, cidx, owner, stage, value, notes, period, created_day = row[:8]
        closed_day = row[8] if len(row) > 8 else None
        contact_id = c[cidx].id if cidx is not None else None
        creator = owner or admin.id
        if period == "previous":
            created_at = _previous_month_day(created_day)
            closed_at = (
                _previous_month_day(closed_day)
                if closed_day is not None
                else (_previous_month_day(created_day + 5) if stage in ("Closed Won", "Closed Lost") else None)
            )
        else:
            created_at = _current_month_day(created_day)
            closed_at = (
                _current_month_day(closed_day)
                if closed_day is not None
                else (_current_month_day(created_day + 3) if stage in ("Closed Won", "Closed Lost") else None)
            )

        d = models.Deal(
            id=_uid(),
            contactId=contact_id,
            title=title,
            value=value,
            stage=stage,
            userId=owner,
            createdById=creator,
            companyId=company.id,
            notes=notes,
            createdAt=created_at,
            closedAt=closed_at,
        )
        db.add(d)
        deal_rows.append(d)
    db.flush()

    d0 = deal_rows[12]  # Поставка оборудования — Астана Логистик (Negotiation)
    t0 = _current_month_day(2)
    t2 = _current_month_day(6)
    for old_s, new_s, at, by in [
        ("Discovery", "Proposal", t0, sales1.id),
        ("Proposal", "Negotiation", t2, sales1.id),
    ]:
        db.add(
            models.DealStageHistory(
                id=_uid(),
                deal_id=d0.id,
                old_stage=old_s,
                new_stage=new_s,
                changed_at=at,
                changed_by=by,
            )
        )
        db.add(
            models.DealChangeHistory(
                id=_uid(),
                deal_id=d0.id,
                field="stage",
                old_value=old_s,
                new_value=new_s,
                changed_at=at,
                changed_by=by,
            )
        )

    # История стадий для ещё нескольких сделок (воронка / аналитика)
    funnel_samples = [
        (deal_rows[10], sales1.id, [("Qualified", "Discovery"), ("Discovery", "Proposal")]),
        (deal_rows[4], sales2.id, [("New Request", "Qualified")]),
        (deal_rows[19], sales1.id, [("Proposal", "Closed Won")]),
    ]
    for deal, actor, transitions in funnel_samples:
        base = _current_month_day(1)
        for i, (old_s, new_s) in enumerate(transitions):
            at = base + dt.timedelta(days=2 * (i + 1))
            db.add(
                models.DealStageHistory(
                    id=_uid(),
                    deal_id=deal.id,
                    old_stage=old_s,
                    new_stage=new_s,
                    changed_at=at,
                    changed_by=actor,
                )
            )

    # Заметки
    note_specs = [
        (d0.id, sales1.id, "Клиент запросил скидку 5% при оплате до 15 числа."),
        (deal_rows[10].id, sales1.id, "Отправили коммерческое на почту."),
        (deal_rows[15].id, sales2.id, "Подписан договор на продление."),
        (deal_rows[0].id, admin.id, "Назначить ответственного после квалификации."),
    ]
    for deal_id, uid, content in note_specs:
        db.add(models.Note(id=_uid(), dealId=deal_id, userId=uid, content=content))

    # Задачи по сделкам (карточка сделки + «Мои задачи»)
    def _due_in_days(days: int | None) -> dt.datetime | None:
        if days is None:
            return None
        base = _utc_now().replace(hour=10, minute=0, second=0, microsecond=0)
        return base + dt.timedelta(days=days)

    # (deal_idx, title, assignee, due_days, is_done, created_by)
    task_specs: list[tuple] = [
        (12, "Согласовать финальную скидку с закупками", sales1.id, -1, 0, sales1.id),
        (12, "Подготовить договор на подпись", sales1.id, 0, 0, sales1.id),
        (12, "Контроль оплаты аванса", sales1.id, 3, 0, admin.id),
        (0, "Назначить ответственного по лиду WMS", sales1.id, 0, 0, admin.id),
        (0, "Первичный звонок по заявке", None, 1, 0, admin.id),
        (10, "Отправить обновлённое КП (Berlin)", sales2.id, -2, 0, sales2.id),
        (9, "Демо для Retail Group", sales1.id, 2, 0, sales1.id),
        (7, "Сбор требований у Qazaq Pharma", sales1.id, 5, 0, sales1.id),
        (13, "Юридическая ревизия SLA", sales2.id, 1, 0, sales2.id),
        (14, "Назначить владельца допродажи", sales2.id, 0, 0, admin.id),
        (1, "Уточнить API-документацию SteppePay", sales2.id, 4, 0, sales2.id),
        (4, "Квалификация Luso Retail — бюджет", sales1.id, 7, 0, sales1.id),
        (19, "Архив: передать акт выполненных работ", sales1.id, None, 1, sales1.id),
        (15, "Архив: отправить благодарственное письмо", sales2.id, None, 1, sales2.id),
        (11, "Напомнить СтройМонтаж о смете", None, 2, 0, admin.id),
    ]
    open_tasks = 0
    for deal_idx, title, assignee, due_days, is_done, created_by in task_specs:
        deal = deal_rows[deal_idx]
        resolved_assignee = assignee or deal.userId or sales1.id
        db.add(
            models.DealTask(
                id=_uid(),
                dealId=deal.id,
                title=title,
                dueAt=_due_in_days(due_days),
                isDone=is_done,
                createdBy=created_by,
                createdAt=_current_month_day(5 + (deal_idx % 10)),
                assignedUserId=resolved_assignee,
            )
        )
        if not is_done:
            open_tasks += 1

    # Активности (разнообразие для ML: activity_count_30d, interaction_score)
    activity_types = ["call", "email", "meeting", "note", "telegram"]
    for ci, contact in enumerate(c):
        for j, typ in enumerate(activity_types[: 3 + (ci % 3)]):
            db.add(
                models.Activity(
                    id=_uid(),
                    type=typ,
                    entityType="contact",
                    entityId=contact.id,
                    description=f"Демо-активность ({typ}) — {contact.company}",
                    timestamp=_current_month_day(min(28, 2 + j + ci)).isoformat(),
                )
            )
    deal_activity_deals = [d0, deal_rows[10], deal_rows[15], deal_rows[0]]
    for di, deal in enumerate(deal_activity_deals):
        db.add(
            models.Activity(
                id=_uid(),
                type=["meeting", "email", "deal_won", "stage_changed"][di % 4],
                entityType="deal",
                entityId=deal.id,
                description=f"Событие по сделке: {deal.title[:40]}",
                timestamp=_current_month_day(3 + di).isoformat(),
            )
        )

    # Сообщения чата
    db.add(
        models.ChatMessage(
            id=_uid(),
            contactId=c[0].id,
            dealId=d0.id,
            senderRole="client",
            senderId=c[0].telegram_id,
            senderName=c[0].name,
            content="Добрый день! Пришлите, пожалуйста, счёт на оплату.",
            messageType="text",
        )
    )
    db.add(
        models.ChatMessage(
            id=_uid(),
            contactId=c[0].id,
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
            contactId=c[1].id,
            dealId=deal_rows[10].id,
            senderRole="client",
            senderId=c[1].telegram_id,
            senderName=c[1].name,
            content="Можем ли мы получить тестовый доступ?",
            messageType="text",
        )
    )
    db.add(
        models.ChatMessage(
            id=_uid(),
            contactId=c[5].id,
            dealId=deal_rows[13].id,
            senderRole="client",
            senderId=c[5].telegram_id,
            senderName=c[5].name,
            content="Нужны условия по SLA для фарма-склада.",
            messageType="text",
        )
    )

    # AI insights (демо ML / подсказок)
    insight_specs = [
        ("contact", c[1].id, "prediction", "Вероятность конверсии", 72, ["Назначить демо", "Отправить кейс"]),
        ("contact", c[5].id, "prediction", "Крупный контракт", 68, ["Подключить пресейл", "Юр. проверка"]),
        ("contact", c[6].id, "risk", "Низкая активность", 55, ["Исходящий звонок"]),
        ("deal", d0.id, "risk", "Риск задержки оплаты", 61, ["Запросить юр.лицо плательщика"]),
        ("deal", deal_rows[0].id, "action", "Нет ответственного", 80, ["Назначить sales1 или sales2"]),
    ]
    for et, eid, cat, title, conf, sugg in insight_specs:
        db.add(
            models.AIInsight(
                id=_uid(),
                entityType=et,
                entityId=eid,
                category=cat,
                title=title,
                content=f"Демо-подсказка для {title}.",
                confidence=conf,
                suggestions=sugg,
            )
        )

    # Журнал коммуникаций (аналитика / churn)
    for ci, contact in enumerate(c):
        for i in range(6):
            db.add(
                models.CommunicationLog(
                    id=_uid(),
                    type=["call", "email", "telegram", "meeting"][i % 4],
                    direction="outbound" if i % 2 == 0 else "inbound",
                    contact_id=contact.id,
                    user_id=sales1.id if i % 2 == 0 else sales2.id,
                    duration=120 + i * 30 if i % 4 == 0 else None,
                    status=["completed", "sent", "opened", "read"][i % 4],
                    timestamp=_current_month_day(min(28, 1 + i + ci)),
                    metadata_json={"seed": True, "contact_idx": ci, "idx": i},
                )
            )

    unassigned = sum(1 for d in deal_rows if d.userId is None)

    db.commit()
    print("Демо-данные успешно добавлены.")
    print()
    now = _utc_now()
    py, pm = _month_shift(now.year, now.month, -1)
    prev_closed = sum(
        1
        for d in deal_rows
        if d.stage in ("Closed Won", "Closed Lost")
        and d.createdAt
        and d.createdAt.year == py
        and d.createdAt.month == pm
    )
    print(f"  Сделок: {len(deal_rows)} (без ответственного: {unassigned})")
    print(f"  Задач по сделкам: {len(task_specs)} (открытых: {open_tasks})")
    print(f"  Закрытых в прошлом месяце ({py}-{pm:02d}): {prev_closed}")
    print(f"  Остальные — в текущем ({now.year}-{now.month:02d})")
    print(f"  Контактов: {len(contact_rows)}")
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
