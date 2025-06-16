"""
Run this script to initialize the database with sample data.
"""
import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_init import init_db

if __name__ == "__main__":
    init_db()
    print("Database initialized with sample data.") 