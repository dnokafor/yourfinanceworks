"""
Standalone script to initialize the database and run the API.
"""
import uvicorn
from models.database import Base, engine
from db_init import init_db
from main import app

def setup_and_run():
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize database with sample data
    init_db()
    
    # Run the API
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    setup_and_run() 