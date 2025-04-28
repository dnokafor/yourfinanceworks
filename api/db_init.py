import datetime
from sqlalchemy.orm import Session

from models.database import SessionLocal, engine
from models.models import Base, Client, Invoice, Item, Payment

# Create the database tables
def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if we already have data
    if db.query(Client).first():
        db.close()
        return
    
    # Add sample clients
    clients = [
        Client(
            name="Acme Corporation",
            email="billing@acme.com",
            phone="(555) 123-4567",
            address="123 Main Street, Anytown, CA 12345",
            balance=1250.75
        ),
        Client(
            name="Globex Industries",
            email="accounts@globex.com",
            phone="(555) 987-6543",
            address="456 Tech Avenue, Silicon Valley, CA 94024",
            balance=3540.20
        ),
        Client(
            name="Stark Enterprises",
            email="finance@stark.com",
            phone="(555) 333-2222",
            address="789 Innovation Drive, Future City, NY 10001",
            balance=0
        ),
        Client(
            name="Wayne Industries",
            email="accounts@wayne.com",
            phone="(555) 888-9999",
            address="1 Wayne Tower, Gotham City, NJ 07101",
            balance=5250.00
        ),
        Client(
            name="Daily Planet",
            email="billing@dailyplanet.com",
            phone="(555) 111-7890",
            address="42 Press Street, Metropolis, IL 60007",
            balance=825.50
        )
    ]
    
    db.add_all(clients)
    db.commit()
    
    # Refresh to get the IDs
    for client in clients:
        db.refresh(client)
    
    # Add sample invoices and items
    invoice1 = Invoice(
        number="INV-001",
        client_id=clients[0].id,  # Acme Corporation
        date=datetime.date(2025, 4, 1),
        due_date=datetime.date(2025, 5, 1),
        amount=750.00,
        status="paid"
    )
    
    item1 = Item(
        description="Website Development",
        quantity=1,
        price=750.00,
        invoice=invoice1
    )
    
    invoice2 = Invoice(
        number="INV-002",
        client_id=clients[0].id,  # Acme Corporation
        date=datetime.date(2025, 4, 15),
        due_date=datetime.date(2025, 5, 15),
        amount=500.75,
        status="pending"
    )
    
    item2_1 = Item(
        description="Hosting Services (Annual)",
        quantity=1,
        price=420.00,
        invoice=invoice2
    )
    
    item2_2 = Item(
        description="SSL Certificate",
        quantity=1,
        price=80.75,
        invoice=invoice2
    )
    
    invoice3 = Invoice(
        number="INV-003",
        client_id=clients[1].id,  # Globex Industries
        date=datetime.date(2025, 4, 10),
        due_date=datetime.date(2025, 5, 10),
        amount=3540.20,
        status="pending"
    )
    
    item3 = Item(
        description="Custom Software Development",
        quantity=40,
        price=85.00,
        invoice=invoice3
    )
    
    item3_2 = Item(
        description="Project Management",
        quantity=5,
        price=75.00,
        invoice=invoice3
    )
    
    # Add more invoices as needed...
    
    db.add_all([invoice1, invoice2, invoice3])
    db.add_all([item1, item2_1, item2_2, item3, item3_2])
    db.commit()
    
    # Add sample payments
    payment1 = Payment(
        invoice_id=invoice1.id,
        amount=750.00,
        date=datetime.date(2025, 4, 20),
        method="Credit Card"
    )
    
    db.add(payment1)
    db.commit()
    
    db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized with sample data.") 