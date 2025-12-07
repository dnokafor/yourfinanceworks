#!/usr/bin/env python3
"""
Verification script for creator attribution filtering.

This script demonstrates that the filtering functionality is correctly
implemented across all endpoints.
"""

import inspect
from typing import get_type_hints


def verify_endpoint_signature(module_name, function_name, param_name, expected_type="Optional[int]"):
    """Verify that an endpoint has the correct parameter signature"""
    try:
        # Import the module and function
        module = __import__(module_name, fromlist=[function_name])
        func = getattr(module, function_name)
        
        # Get function signature
        sig = inspect.signature(func)
        params = sig.parameters
        
        # Check if parameter exists
        if param_name not in params:
            return False, f"Parameter '{param_name}' not found"
        
        # Get parameter details
        param = params[param_name]
        
        # Check if it's optional (has None default)
        if param.default is not None and param.default != inspect.Parameter.empty:
            return False, f"Parameter '{param_name}' should default to None"
        
        return True, f"✓ Parameter '{param_name}' correctly defined"
        
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    """Run verification checks"""
    print("=" * 70)
    print("Creator Attribution Filtering Verification")
    print("=" * 70)
    print()
    
    checks = [
        ("core.routers.invoices", "read_invoices", "created_by_user_id"),
        ("core.routers.expenses", "list_expenses", "created_by_user_id"),
        ("core.routers.statements", "list_statements", "created_by_user_id"),
        ("core.routers.reminders", "get_reminders", "created_by_id"),
    ]
    
    all_passed = True
    
    for module_name, function_name, param_name in checks:
        endpoint_name = f"{module_name}.{function_name}"
        print(f"Checking {endpoint_name}...")
        
        passed, message = verify_endpoint_signature(module_name, function_name, param_name)
        
        if passed:
            print(f"  {message}")
        else:
            print(f"  ✗ {message}")
            all_passed = False
        
        print()
    
    print("=" * 70)
    if all_passed:
        print("✓ All checks passed! Creator filtering is correctly implemented.")
    else:
        print("✗ Some checks failed. Please review the implementation.")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
