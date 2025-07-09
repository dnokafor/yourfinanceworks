#!/usr/bin/env python3
"""
Script to add the invoice_history table for tracking invoice changes.
"""

import sqlite3
import os
from datetime import datetime

def add_invoice_history_table():
    # Get the database path
    db_path = os.path.join(os.path.dirname(__file__), '..', 'invoice_app.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if invoice_history table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoice_history'")
        if cursor.fetchone():
            print("invoice_history table already exists.")
            return
        
        # Create the invoice_history table
        print("Creating invoice_history table...")
        cursor.execute("""
            CREATE TABLE invoice_history (
                id INTEGER PRIMARY KEY,
                invoice_id INTEGER NOT NULL,
                tenant_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                action VARCHAR NOT NULL,
                details VARCHAR,
                previous_values JSON,
                current_values JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE,
                FOREIGN KEY (tenant_id) REFERENCES tenants (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX idx_invoice_history_invoice_id ON invoice_history (invoice_id)")
        cursor.execute("CREATE INDEX idx_invoice_history_tenant_id ON invoice_history (tenant_id)")
        cursor.execute("CREATE INDEX idx_invoice_history_created_at ON invoice_history (created_at)")
        
        conn.commit()
        print("Successfully created invoice_history table!")
        
        # Verify the table was created
        cursor.execute("PRAGMA table_info(invoice_history)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Columns in invoice_history table: {columns}")
        
    except Exception as e:
        print(f"Error creating invoice_history table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_invoice_history_table() 