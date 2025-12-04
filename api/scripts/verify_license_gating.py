"""
Verification script for license gating on Advanced Reporting and Advanced Search.

This script verifies that:
1. Feature configuration correctly marks reporting and advanced_search as commercial tier
2. The features are disabled by default
"""

import sys
sys.path.insert(0, '/app')

from core.services.feature_config_service import FeatureConfigService

def verify_feature_config():
    """Verify that reporting and advanced_search are configured as commercial features."""
    
    print("=" * 60)
    print("Feature Configuration Verification")
    print("=" * 60)
    
    # Check reporting feature
    reporting_config = FeatureConfigService.FEATURES.get('reporting')
    print("\n1. Reporting Feature Configuration:")
    print(f"   - Name: {reporting_config['name']}")
    print(f"   - License Tier: {reporting_config['license_tier']}")
    print(f"   - Default Enabled: {reporting_config['default']}")
    
    assert reporting_config['license_tier'] == 'commercial', \
        f"❌ FAIL: Reporting should be 'commercial' tier, got '{reporting_config['license_tier']}'"
    assert reporting_config['default'] == False, \
        f"❌ FAIL: Reporting should be disabled by default, got {reporting_config['default']}"
    print("   ✅ PASS: Reporting is correctly configured as commercial tier")
    
    # Check advanced_search feature
    search_config = FeatureConfigService.FEATURES.get('advanced_search')
    print("\n2. Advanced Search Feature Configuration:")
    print(f"   - Name: {search_config['name']}")
    print(f"   - License Tier: {search_config['license_tier']}")
    print(f"   - Default Enabled: {search_config['default']}")
    
    assert search_config['license_tier'] == 'commercial', \
        f"❌ FAIL: Advanced Search should be 'commercial' tier, got '{search_config['license_tier']}'"
    assert search_config['default'] == False, \
        f"❌ FAIL: Advanced Search should be disabled by default, got {search_config['default']}"
    print("   ✅ PASS: Advanced Search is correctly configured as commercial tier")
    
    print("\n" + "=" * 60)
    print("✅ All feature configuration checks passed!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        verify_feature_config()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
