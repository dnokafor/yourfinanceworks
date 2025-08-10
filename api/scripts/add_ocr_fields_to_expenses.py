from sqlalchemy import create_engine, inspect, text
import os


def run():
    db_url_template = os.environ.get("TENANT_DB_URL_TEMPLATE", "postgresql://postgres:password@postgres-master:5432/tenant_{tenant_id}")
    # Discover tenants from master DB
    master_url = os.environ.get("DATABASE_URL", "postgresql://postgres:password@postgres-master:5432/invoice_master")
    master_engine = create_engine(master_url)
    tenants = []
    with master_engine.connect() as conn:
        res = conn.execute(text("SELECT id FROM tenants"))
        tenants = [row[0] for row in res]

    for tenant_id in tenants:
        tenant_db_url = db_url_template.format(tenant_id=tenant_id)
        engine = create_engine(tenant_db_url)
        inspector = inspect(engine)
        if 'expenses' not in inspector.get_table_names():
            continue
        columns = [c['name'] for c in inspector.get_columns('expenses')]
        with engine.connect() as conn:
            if 'imported_from_attachment' not in columns:
                conn.execute(text("ALTER TABLE expenses ADD COLUMN imported_from_attachment BOOLEAN DEFAULT FALSE NOT NULL"))
            if 'analysis_status' not in columns:
                conn.execute(text("ALTER TABLE expenses ADD COLUMN analysis_status VARCHAR(50) DEFAULT 'not_started' NOT NULL"))
            if 'analysis_result' not in columns:
                conn.execute(text("ALTER TABLE expenses ADD COLUMN analysis_result JSON"))
            if 'analysis_error' not in columns:
                conn.execute(text("ALTER TABLE expenses ADD COLUMN analysis_error TEXT"))
            if 'manual_override' not in columns:
                conn.execute(text("ALTER TABLE expenses ADD COLUMN manual_override BOOLEAN DEFAULT FALSE NOT NULL"))
            if 'analysis_updated_at' not in columns:
                conn.execute(text("ALTER TABLE expenses ADD COLUMN analysis_updated_at TIMESTAMPTZ NULL"))
            conn.commit()

if __name__ == "__main__":
    run()


