"""
Run this script to initialize the database with sample data.
"""
from api.db_init import init_db

if __name__ == "__main__":
    init_db()
    print("Database initialized with sample data.") 