#!/usr/bin/env python3
"""
Script to fix the malformed currency.py file.
"""

import re

def fix_currency_router():
    """Fix the currency.py file"""
    
    with open('api/routers/currency.py', 'r') as f:
        content = f.read()
    
    # Fix function signatures that are missing db parameter
    functions_to_fix = [
        'get_supported_currencies',
        'get_currency_rates',
        'create_or_update_exchange_rate',
        'update_exchange_rate',
        'convert_currency',
        'delete_exchange_rate',
        'create_custom_currency',
        'update_custom_currency',
        'delete_custom_currency'
    ]
    
    for func_name in functions_to_fix:
        # Pattern to match function definition
        pattern = rf'async def {func_name}\([^)]*\):'
        
        def add_db_param(match):
            func_def = match.group(0)
            if 'db: Session = Depends(get_db)' not in func_def:
                # Add db parameter before the closing parenthesis
                func_def = func_def.replace('):', ', db: Session = Depends(get_db)):')
            return func_def
        
        content = re.sub(pattern, add_db_param, content)
    
    # Fix malformed try blocks
    content = re.sub(
        r'# Manually set tenant context and get tenant database    try:',
        'try:',
        content
    )
    
    # Fix malformed function endings
    content = re.sub(
        r'\)@router\.get\("/rates"',
        ')\n\n@router.get("/rates"',
        content
    )
    
    content = re.sub(
        r'\)@router\.post\("/rates"',
        ')\n\n@router.post("/rates"',
        content
    )
    
    content = re.sub(
        r'\)@router\.put\("/rates/\{rate_id\}"',
        ')\n\n@router.put("/rates/{rate_id}"',
        content
    )
    
    content = re.sub(
        r'\)@router\.get\("/convert"',
        ')\n\n@router.get("/convert"',
        content
    )
    
    content = re.sub(
        r'\)@router\.delete\("/rates/\{rate_id\}"',
        ')\n\n@router.delete("/rates/{rate_id}"',
        content
    )
    
    content = re.sub(
        r'\)@router\.post\("/supported"',
        ')\n\n@router.post("/supported"',
        content
    )
    
    content = re.sub(
        r'\)@router\.put\("/supported/\{currency_id\}"',
        ')\n\n@router.put("/supported/{currency_id}"',
        content
    )
    
    content = re.sub(
        r'\)@router\.delete\("/supported/\{currency_id\}"',
        ')\n\n@router.delete("/supported/{currency_id}"',
        content
    )
    
    with open('api/routers/currency.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed currency router")

if __name__ == "__main__":
    fix_currency_router() 