import sys
import os
import datetime
import random

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app import models

def seed_data():
    db = SessionLocal()
    try:
        # 1. Get some existing data
        deals = db.query(models.Deal).limit(5).all()
        contacts = db.query(models.Contact).limit(10).all()
        users = db.query(models.User).limit(5).all()

        if not deals or not contacts or not users:
            print("Error: Please make sure you have deals, contacts and users in the database first.")
            return

        print(f"Found {len(deals)} deals and {len(contacts)} contacts. Generating history...")

        # 2. Seed Deal Stage History
        stages = ["Discovery", "Proposal", "Negotiation", "Closed Won"]
        
        for deal in deals:
            # Simulate a deal moving through stages over the last 30 days
            current_date = datetime.datetime.utcnow() - datetime.timedelta(days=30)
            
            for i in range(len(stages) - 1):
                current_date += datetime.timedelta(days=random.randint(2, 7))
                if current_date > datetime.datetime.utcnow():
                    break
                    
                history = models.DealStageHistory(
                    deal_id=deal.id,
                    old_stage=stages[i],
                    new_stage=stages[i+1],
                    changed_at=current_date,
                    changed_by=random.choice(users).id
                )
                db.add(history)
            
        # 3. Seed Communication Logs
        comm_types = [
            ("call", ["completed", "missed", "busy"]),
            ("email", ["sent", "opened", "bounced"]),
            ("telegram", ["sent", "read"]),
            ("meeting", ["completed", "cancelled"])
        ]

        for contact in contacts:
            for _ in range(random.randint(5, 15)):
                c_type, statuses = random.choice(comm_types)
                timestamp = datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(0, 45))
                
                log = models.CommunicationLog(
                    type=c_type,
                    direction=random.choice(["inbound", "outbound"]),
                    contact_id=contact.id,
                    user_id=random.choice(users).id,
                    duration=random.randint(30, 600) if c_type == "call" else None,
                    status=random.choice(statuses),
                    timestamp=timestamp,
                    metadata_json={
                        "subject": f"Demo {c_type} subject" if c_type == "email" else None,
                        "notes": "Automated seed data for business analysis demonstration"
                    }
                )
                db.add(log)

        db.commit()
        print("Successfully seeded business logging tables with demo data!")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
