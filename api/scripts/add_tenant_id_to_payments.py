import sqlite3
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the database file, which is in the parent directory of the 'scripts' folder
db_path = os.path.join(script_dir, '..', 'invoice_app.db')

def add_tenant_id_to_payments():
    """
    Adds the tenant_id column to the payments table if it doesn't exist.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the column already exists
        cursor.execute("PRAGMA table_info(payments)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'tenant_id' not in columns:
            print("Adding 'tenant_id' column to 'payments' table...")
            # Add the tenant_id column. We allow NULL temporarily to add it to existing rows.
            # We'll need to populate it afterwards.
            cursor.execute("ALTER TABLE payments ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)")

            # For existing payments, we can try to associate them with a tenant.
            # A simple approach is to assign them to the first tenant (tenant_id=1).
            # This is a reasonable assumption for a single-tenant system being migrated.
            print("Populating 'tenant_id' for existing payments...")
            cursor.execute("UPDATE payments SET tenant_id = (SELECT id FROM tenants ORDER BY id LIMIT 1) WHERE tenant_id IS NULL")

            # Now, if you have a NOT NULL constraint in your model (which you do),
            # you would ideally alter the table again to add it, but that's complex in SQLite.
            # For now, we will rely on the application layer to enforce this for new records.
            # The UPDATE above should handle existing records.
            
            conn.commit()
            print("'tenant_id' column added and populated successfully.")
        else:
            print("'tenant_id' column already exists in 'payments' table.")

        # Close the connection
        conn.close()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    add_tenant_id_to_payments() 