import sys
import os
import datetime
import uuid
sys.path.append(os.getcwd())

from app.database import engine, Base, SessionLocal
from app.models import Deal, Contact, Note, ChatMessage, Company, User, AIInsight, Activity
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

        # 3. Create Contacts (telegram_id can be set later by the user)
        contacts = [
            Contact(id=str(uuid.uuid4()), name="Elon Musk", email="elon@tesla.com", phone="+1-999-888-7777", company="Tesla", role="CEO", status="Active", avatar="EM", revenue=150000, companyId=company.id),
            Contact(id=str(uuid.uuid4()), name="Tim Cook", email="tim@apple.com", phone="+1-555-444-3333", company="Apple", role="CEO", status="Active", avatar="TC", revenue=200000, companyId=company.id),
            Contact(id=str(uuid.uuid4()), name="Sam Altman", email="sam@openai.com", phone="+1-111-222-3333", company="OpenAI", role="CEO", status="Prospect", avatar="SA", revenue=0, companyId=company.id),
        ]
        db.add_all(contacts)
        db.flush()

        # 4. Create Deals
        deals = [
            Deal(
                id=str(uuid.uuid4()), 
                title="Model S Fleet", 
                value=500000, 
                stage="Negotiation", 
                contactId=contacts[0].id, 
                userId=manager.id, 
                companyId=company.id,
                notes="Large fleet order for company staff."
            ),
            Deal(
                id=str(uuid.uuid4()), 
                title="Mobile Ad Campaign", 
                value=85000, 
                stage="Discovery", 
                contactId=contacts[1].id, 
                userId=manager.id, 
                companyId=company.id
            ),
            Deal(
                id=str(uuid.uuid4()), 
                title="Cloud Infrastructure", 
                value=120000, 
                stage="Closed Won", 
                contactId=contacts[2].id, 
                userId=admin.id, 
                companyId=company.id,
                closedAt=datetime.datetime.utcnow() - datetime.timedelta(days=2)
            ),
        ]
        db.add_all(deals)
        db.flush()

        # 5. Create Notes
        notes = [
            Note(id=str(uuid.uuid4()), dealId=deals[0].id, userId=manager.id, content="Sent the invoice yesterday.", createdAt=datetime.datetime.utcnow() - datetime.timedelta(hours=5)),
            Note(id=str(uuid.uuid4()), dealId=deals[0].id, userId=admin.id, content="Budget approved. Proceed with the contract.", createdAt=datetime.datetime.utcnow() - datetime.timedelta(hours=1)),
        ]
        db.add_all(notes)
        
        db.commit()
        print("Database reset and seeded successfully!")
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
