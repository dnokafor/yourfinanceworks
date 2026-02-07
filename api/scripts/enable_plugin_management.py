#!/usr/bin/env python3
"""
Enable Plugin Management Feature

This script enables the plugin_management feature by either:
1. Starting a trial (enables all features)
2. Adding plugin_management to your licensed features

Usage:
    python api/scripts/enable_plugin_management.py --trial
    python api/scripts/enable_plugin_management.py --license
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# Add the parent directory to the path so we can import from api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_tenant_db_session
from core.models import Installation
from core.services.license_service import LicenseService


def enable_trial(tenant_id: int = 1):
    """Enable trial mode which enables all features including plugin_management."""
    print(f"\n🚀 Starting trial mode for tenant {tenant_id}...")
    print("-" * 60)

    db = get_tenant_db_session(tenant_id)
    try:
        installation = db.query(Installation).filter(Installation.tenant_id == tenant_id).first()
        if not installation:
            print(f"❌ No installation found for tenant {tenant_id}")
            return False

        # Set trial period
        installation.trial_started_at = datetime.now(timezone.utc)
        installation.trial_expires_at = datetime.now(timezone.utc) + timedelta(days=14)
        installation.license_status = "trial"
        installation.usage_type = "trial"

        db.commit()
        print(f"   ✅ Trial started - expires in 14 days")

        # Verify plugin management is enabled
        license_service = LicenseService(db)
        has_plugin_mgmt = license_service.has_feature("plugin_management")

        print(f"\n📋 Plugin Management Feature:")
        print(f"   Enabled: {'✅ Yes' if has_plugin_mgmt else '❌ No'}")

        if has_plugin_mgmt:
            print(f"\n🎉 Plugin Management is now enabled!")
            print(f"   You can now manage plugins through the Settings > Plugins tab")

        return True

    except Exception as e:
        print(f"❌ Error enabling trial: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def enable_plugin_management_via_license(tenant_id: int = 1):
    """Enable plugin management by adding it to licensed features."""
    print(f"\n🔧 Adding plugin_management to licensed features...")
    print("-" * 60)

    db = get_tenant_db_session(tenant_id)
    try:
        installation = db.query(Installation).filter(Installation.tenant_id == tenant_id).first()
        if not installation:
            print(f"❌ No installation found for tenant {tenant_id}")
            return False

        # Get current licensed features
        current_features = installation.licensed_features or []

        print(f"   Current features: {current_features}")

        # Add plugin_management if not already present
        if "plugin_management" not in current_features:
            current_features.append("plugin_management")
            installation.licensed_features = current_features
            db.commit()
            print(f"   ✅ Added plugin_management to licensed features")
        else:
            print(f"   ℹ️  plugin_management already in licensed features")

        # Verify
        from core.services.license_service import LicenseService
        license_service = LicenseService(db)
        has_plugin_mgmt = license_service.has_feature("plugin_management")

        print(f"\n📋 Plugin Management Feature:")
        print(f"   Enabled: {'✅ Yes' if has_plugin_mgmt else '❌ No'}")

        if has_plugin_mgmt:
            print(f"\n🎉 Plugin Management is now enabled!")
            print(f"   You can now manage plugins through the Settings > Plugins tab")

        return True

    except Exception as e:
        print(f"❌ Error enabling plugin management: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Enable Plugin Management Feature")
    parser.add_argument("--trial", action="store_true", help="Enable trial mode (all features)")
    parser.add_argument("--license", action="store_true", help="Add to licensed features")
    parser.add_argument("--tenant-id", type=int, default=1, help="Tenant ID (default: 1)")

    args = parser.parse_args()

    if not args.trial and not args.license:
        print("❌ Please specify either --trial or --license")
        parser.print_help()
        return

    print("🔧 Plugin Management Feature Enabler")
    print("=" * 60)

    if args.trial:
        success = enable_trial(args.tenant_id)
    else:
        success = enable_plugin_management_via_license(args.tenant_id)

    if success:
        print("\n✅ Plugin Management feature has been enabled successfully!")
        print("\nNext steps:")
        print("1. Restart your application if needed")
        print("2. Navigate to Settings > Plugins to manage your plugins")
        print("3. Enable/disable plugins as needed")
    else:
        print("\n❌ Failed to enable Plugin Management feature")
        sys.exit(1)


if __name__ == "__main__":
    main()
