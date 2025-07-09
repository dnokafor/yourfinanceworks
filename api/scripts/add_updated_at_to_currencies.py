#!/usr/bin/env python3
"""
Script to add the missing updated_at column to the supported_currencies table.
"""

import sqlite3
import os
from datetime import datetime

def add_updated_at_column():
    # Get the database path
    db_path = os.path.join(os.path.dirname(__file__), '..', 'invoice_app.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if supported_currencies table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='supported_currencies'")
        if not cursor.fetchone():
            print("supported_currencies table not found. Please run the currency support migration first.")
            return
        
        # Check if updated_at column already exists
        cursor.execute("PRAGMA table_info(supported_currencies)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'updated_at' in columns:
            print("updated_at column already exists in supported_currencies table.")
            return
        
        # Add the updated_at column (SQLite doesn't support CURRENT_TIMESTAMP in ALTER TABLE)
        print("Adding updated_at column to supported_currencies table...")
        cursor.execute("ALTER TABLE supported_currencies ADD COLUMN updated_at TIMESTAMP")
        
        # Update existing records with current timestamp
        print("Updating existing records with current timestamp...")
        cursor.execute("UPDATE supported_currencies SET updated_at = created_at WHERE updated_at IS NULL")
        
        # Update any remaining NULL values with current timestamp
        cursor.execute("UPDATE supported_currencies SET updated_at = datetime('now') WHERE updated_at IS NULL")
        
        conn.commit()
        print("Successfully added updated_at column to supported_currencies table!")
        
        # Verify the change
        cursor.execute("PRAGMA table_info(supported_currencies)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns in supported_currencies table: {columns}")
        
    except Exception as e:
        print(f"Error adding updated_at column: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_updated_at_column() 