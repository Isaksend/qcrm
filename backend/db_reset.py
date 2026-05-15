import sys
import os
import datetime
import uuid
sys.path.append(os.getcwd())

from app.database import engine, Base, SessionLocal
from app.models import (
    Deal,
    Contact,
    Note,
    ChatMessage,
    Company,
    User,
    AIInsight,
    Activity,
    DealStageHistory,
    DealChangeHistory,
    CommunicationLog,
    DealTask,
)
from app.auth import get_password_hash

def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Seeding mock data...")
        
        # 1. Create Company
        company = Company(id=str(uuid.uuid4()), name="Tiny Corp", created_at=datetime.datetime.utcnow().isoformat())
        db.add(company)
        db.flush()
        
        # 2. Create Users
        admin = User(
            id=str(uuid.uuid4()),
            name="Admin User",
            email="admin@tinycrm.com",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            company_id=company.id
        )
        manager = User(
            id=str(uuid.uuid4()),
            name="Jane Sales",
            email="jane@tinycrm.com",
            hashed_password=get_password_hash("pass123"),
            role="user",
            company_id=company.id
        )
        super_admin = User(
            id=str(uuid.uuid4()),
            name="Super Admin",
            email="super@tinycrm.com",
            hashed_password=get_password_hash("super123"),
            role="super_admin"
        )
        db.add_all([admin, manager, super_admin])
        db.flush()

        now = datetime.datetime.utcnow()

        # 3. Contacts
        contacts = [
            Contact(id=str(uuid.uuid4()), name="Elon Musk", email="elon@tesla.com", phone="+1-999-888-7777", company="Tesla", role="CEO", status="Active", avatar="EM", revenue=150000, companyId=company.id, telegram_id="900001"),
            Contact(id=str(uuid.uuid4()), name="Tim Cook", email="tim@apple.com", phone="+1-555-444-3333", company="Apple", role="CEO", status="Active", avatar="TC", revenue=200000, companyId=company.id, telegram_id="900002"),
            Contact(id=str(uuid.uuid4()), name="Sam Altman", email="sam@openai.com", phone="+1-111-222-3333", company="OpenAI", role="CEO", status="Prospect", avatar="SA", revenue=0, companyId=company.id),
            Contact(id=str(uuid.uuid4()), name="Lisa Su", email="lisa@amd.com", phone="+1-222-333-4444", company="AMD", role="CEO", status="Active", avatar="LS", revenue=90000, companyId=company.id),
            Contact(id=str(uuid.uuid4()), name="Satya Nadella", email="satya@microsoft.com", phone="+1-333-444-5555", company="Microsoft", role="CEO", status="Prospect", avatar="SN", revenue=0, companyId=company.id),
        ]
        db.add_all(contacts)
        db.flush()

        def _deal(title, contact, owner, stage, value, notes=None, days_created=10, closed_days=None):
            created = now - datetime.timedelta(days=days_created)
            closed = (now - datetime.timedelta(days=closed_days)) if closed_days is not None else None
            if stage in ("Closed Won", "Closed Lost") and closed is None:
                closed = now - datetime.timedelta(days=max(1, days_created // 3))
            return Deal(
                id=str(uuid.uuid4()),
                title=title,
                value=value,
                stage=stage,
                contactId=contact.id if contact else None,
                userId=owner.id if owner else None,
                createdById=(owner or admin).id,
                companyId=company.id,
                notes=notes,
                createdAt=created,
                closedAt=closed,
            )

        # 4. Deals — все стадии воронки + без ответственного
        deals = [
            _deal("Inbound lead — fleet inquiry", contacts[2], None, "New Request", 75000, "Unassigned web lead.", 2),
            _deal("AMD GPU supply deal", contacts[3], None, "New Request", 210000, None, 4),
            _deal("Apple Vision Pro rollout", contacts[1], manager, "Qualified", 320000, None, 8),
            _deal("Microsoft Copilot enterprise", contacts[4], None, "Qualified", 480000, "Awaiting owner assignment.", 11),
            _deal("OpenAI API partnership", contacts[2], manager, "Discovery", 95000, None, 14),
            _deal("Tesla charging network", contacts[0], admin, "Discovery", 890000, None, 16),
            _deal("Internal R&D pilot", None, None, "Discovery", 15000, "No contact, no owner.", 18),
            _deal("Apple services bundle", contacts[1], manager, "Proposal", 125000, "Proposal sent.", 20),
            _deal("AMD EPYC upgrade", contacts[3], admin, "Proposal", 67000, None, 22),
            _deal("Model S Fleet", contacts[0], manager, "Negotiation", 500000, "Large fleet order.", 25),
            _deal("Microsoft Azure commit", contacts[4], None, "Negotiation", 540000, "Legal review; unassigned.", 12),
            _deal("OpenAI training credits", contacts[2], manager, "Closed Won", 120000, None, 40, 5),
            _deal("Tesla service contract", contacts[0], admin, "Closed Won", 88000, None, 55, 10),
            _deal("Apple ad trial", contacts[1], manager, "Closed Lost", 0, "Budget freeze.", 35, 7),
            _deal("AMD support renewal", contacts[3], None, "Closed Lost", 0, "Lost to competitor; no owner.", 30, 9),
        ]
        db.add_all(deals)
        db.flush()

        # Stage history for analytics
        main = deals[9]
        t0 = now - datetime.timedelta(days=20)
        t1 = now - datetime.timedelta(days=12)
        for old_s, new_s, at in [("Discovery", "Proposal", t0), ("Proposal", "Negotiation", t1)]:
            db.add(DealStageHistory(deal_id=main.id, old_stage=old_s, new_stage=new_s, changed_at=at, changed_by=manager.id))
            db.add(DealChangeHistory(deal_id=main.id, field="stage", old_value=old_s, new_value=new_s, changed_at=at, changed_by=manager.id))

        # Notes
        db.add_all([
            Note(id=str(uuid.uuid4()), dealId=deals[9].id, userId=manager.id, content="Sent the invoice yesterday.", createdAt=now - datetime.timedelta(hours=5)),
            Note(id=str(uuid.uuid4()), dealId=deals[9].id, userId=admin.id, content="Budget approved. Proceed with the contract.", createdAt=now - datetime.timedelta(hours=1)),
            Note(id=str(uuid.uuid4()), dealId=deals[0].id, userId=admin.id, content="Assign owner after qualification.", createdAt=now - datetime.timedelta(hours=3)),
        ])

        # Deal tasks
        task_due = lambda days: (now + datetime.timedelta(days=days)).replace(hour=10, minute=0, second=0, microsecond=0)
        db.add_all([
            DealTask(dealId=deals[9].id, title="Send revised contract", dueAt=task_due(-1), isDone=0, createdBy=manager.id, assignedUserId=manager.id),
            DealTask(dealId=deals[9].id, title="Schedule signing call", dueAt=task_due(1), isDone=0, createdBy=manager.id, assignedUserId=manager.id),
            DealTask(dealId=deals[0].id, title="Assign owner to inbound lead", dueAt=task_due(0), isDone=0, createdBy=admin.id, assignedUserId=manager.id),
            DealTask(dealId=deals[7].id, title="Send proposal deck", dueAt=task_due(2), isDone=0, createdBy=manager.id, assignedUserId=manager.id),
            DealTask(dealId=deals[11].id, title="Archive: upload signed order", dueAt=None, isDone=1, createdBy=admin.id, assignedUserId=manager.id),
        ])

        # Activities (ML features)
        for ci, contact in enumerate(contacts):
            for j, typ in enumerate(["call", "email", "meeting", "telegram"][: 2 + ci % 3]):
                db.add(Activity(
                    type=typ,
                    entityType="contact",
                    entityId=contact.id,
                    description=f"Mock {typ} with {contact.company}",
                    timestamp=(now - datetime.timedelta(days=j + ci)).isoformat(),
                ))
        for di, deal in enumerate(deals[:4]):
            db.add(Activity(type="stage_changed", entityType="deal", entityId=deal.id, description=deal.title, timestamp=(now - datetime.timedelta(days=di)).isoformat()))

        # Communication logs
        for ci, contact in enumerate(contacts):
            for i in range(5):
                db.add(CommunicationLog(
                    type=["call", "email", "telegram"][i % 3],
                    direction="inbound" if i % 2 else "outbound",
                    contact_id=contact.id,
                    user_id=manager.id,
                    duration=90 if i % 3 == 0 else None,
                    status=["completed", "sent", "opened"][i % 3],
                    timestamp=now - datetime.timedelta(days=i + ci),
                    metadata_json={"mock": True},
                ))

        # Chat + AI insight samples
        db.add(ChatMessage(contactId=contacts[0].id, dealId=deals[9].id, senderRole="client", senderId=contacts[0].telegram_id, senderName=contacts[0].name, content="Please send updated pricing.", messageType="text"))
        db.add(AIInsight(entityType="contact", entityId=contacts[2].id, category="prediction", title="Conversion probability", content="High engagement in last 14 days.", confidence=74, suggestions=["Schedule demo"]))

        unassigned = sum(1 for d in deals if d.userId is None)
        db.commit()
        print("Database reset and seeded successfully!")
        print(f"  Deals: {len(deals)} (unassigned: {unassigned})")
        print(f"  Deal tasks: 5")
        print(f"  Contacts: {len(contacts)}")
        print("-" * 40)
        print("Login Info:")
        print(f"  Admin:   {admin.email} / admin123")
        print(f"  Manager: {manager.email} / pass123")
        print(f"  Super:   {super_admin.email} / super123")
        print("-" * 40)
        print()
        print("TELEGRAM SETUP:")
        print("  1. Ask your client to open your bot in Telegram")
        print("  2. The client sends /start to get their Telegram ID")  
        print("  3. Edit a Contact in the CRM and paste the Telegram ID")
        print("  4. Now you can chat with the client from the Messages page!")
        print("-" * 40)

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    confirm = input("This will DELETE ALL DATA and SEED NEW MOCK DATA. Are you sure? (y/N): ")
    if confirm.lower() == 'y':
        reset_database()
    else:
        print("Reset aborted.")
