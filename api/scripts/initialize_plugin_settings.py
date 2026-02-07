#!/usr/bin/env python3
"""
Initialize plugin settings for all existing tenants.
Run this after the database migration to create default plugin settings.

Usage:
    python api/scripts/initialize_plugin_settings.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models.models import Tenant, TenantPluginSettings
from core.models.database import SessionLocal
from datetime import datetime, timezone

def initialize_plugin_settings():
    """Create default plugin settings for all tenants that don't have them."""
    db = SessionLocal()

    try:
        # Get all tenants
        tenants = db.query(Tenant).all()
        print(f"Found {len(tenants)} tenants")

        created_count = 0
        skipped_count = 0

        for tenant in tenants:
            # Check if settings already exist
            existing = db.query(TenantPluginSettings).filter_by(tenant_id=tenant.id).first()

            if existing:
                print(f"  ✓ Tenant '{tenant.name}' (ID: {tenant.id}) - already has settings")
                skipped_count += 1
            else:
                # Create default settings (no plugins enabled by default)
                settings = TenantPluginSettings(
                    tenant_id=tenant.id,
                    enabled_plugins=[],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(settings)
                print(f"  ✓ Tenant '{tenant.name}' (ID: {tenant.id}) - created default settings")
                created_count += 1

        # Commit all changes
        db.commit()

        print(f"\n✅ Initialization complete!")
        print(f"   Created: {created_count} new settings")
        print(f"   Skipped: {skipped_count} existing settings")

        return True

    except Exception as e:
        print(f"❌ Error during initialization: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = initialize_plugin_settings()
    sys.exit(0 if success else 1)
