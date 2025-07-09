#!/usr/bin/env python3
"""
Comprehensive setup script for the custom currency feature.
This script will run all necessary migrations and add example currencies.
"""

import os
import sys

def run_script(script_name):
    """Run a Python script and return success status"""
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    if not os.path.exists(script_path):
        print(f"Script {script_name} not found")
        return False
    
    print(f"\n{'='*50}")
    print(f"Running {script_name}...")
    print(f"{'='*50}")
    
    try:
        # Import and run the script
        import importlib.util
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Call the main function if it exists
        if hasattr(module, 'migrate_currency_support'):
            module.migrate_currency_support()
        elif hasattr(module, 'add_updated_at_column'):
            module.add_updated_at_column()
        elif hasattr(module, 'add_traditional_currencies'):
            module.add_traditional_currencies()
        elif hasattr(module, 'add_custom_currencies'):
            module.add_custom_currencies()
        elif hasattr(module, 'cleanup_currencies'):
            module.cleanup_currencies()
        elif hasattr(module, 'main'):
            module.main()
        else:
            print(f"No main function found in {script_name}")
            return False
            
        return True
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def main():
    print("Setting up Custom Currency Feature")
    print("=" * 50)
    
    # List of scripts to run in order
    scripts = [
        'add_currency_support.py',
        'add_updated_at_to_currencies.py',
        'add_traditional_currencies.py',
        'add_custom_currencies.py',
        'cleanup_currencies.py'
    ]
    
    success_count = 0
    
    for script in scripts:
        if run_script(script):
            success_count += 1
            print(f"✅ {script} completed successfully")
        else:
            print(f"❌ {script} failed")
    
    print(f"\n{'='*50}")
    print(f"Setup Summary: {success_count}/{len(scripts)} scripts completed successfully")
    print(f"{'='*50}")
    
    if success_count == len(scripts):
        print("🎉 Custom currency feature setup completed successfully!")
        print("\nYou can now:")
        print("1. Restart your application")
        print("2. Go to Settings → Currencies to manage custom currencies")
        print("3. Create invoices with Bitcoin, Ethereum, or other custom currencies")
    else:
        print("⚠️  Some setup steps failed. Please check the errors above.")
        print("You may need to run the failed scripts manually.")

if __name__ == "__main__":
    main() 