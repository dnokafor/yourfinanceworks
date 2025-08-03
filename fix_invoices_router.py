#!/usr/bin/env python3
"""
Script to fix the malformed invoices router.
"""

import re

def fix_invoices_router():
    """Fix the invoices router file"""
    
    with open('api/routers/invoices.py', 'r') as f:
        content = f.read()
    
    # Fix function signatures that are missing db parameter
    functions_to_fix = [
        'get_deleted_invoices',
        'empty_recycle_bin', 
        'restore_invoice',
        'permanently_delete_invoice',
        'read_invoice',
        'update_invoice',
        'delete_invoice',
        'send_invoice_email',
        'get_total_income',
        'calculate_discount',
        'get_invoice_history',
        'create_invoice_history_entry',
        'download_invoice_pdf'
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
        r'\)@router\.get\("/recycle-bin"',
        ')\n\n@router.get("/recycle-bin"',
        content
    )
    
    content = re.sub(
        r'\)@router\.post\("/recycle-bin/empty"',
        ')\n\n@router.post("/recycle-bin/empty"',
        content
    )
    
    content = re.sub(
        r'\)@router\.post\("/\{invoice_id\}/restore"',
        ')\n\n@router.post("/{invoice_id}/restore"',
        content
    )
    
    content = re.sub(
        r'\)@router\.delete\("/\{invoice_id\}/permanent"',
        ')\n\n@router.delete("/{invoice_id}/permanent"',
        content
    )
    
    content = re.sub(
        r'\)@router\.get\("/\{invoice_id\}"',
        ')\n\n@router.get("/{invoice_id}"',
        content
    )
    
    content = re.sub(
        r'\)@router\.put\("/\{invoice_id\}"',
        ')\n\n@router.put("/{invoice_id}"',
        content
    )
    
    content = re.sub(
        r'\)@router\.delete\("/\{invoice_id\}"',
        ')\n\n@router.delete("/{invoice_id}"',
        content
    )
    
    content = re.sub(
        r'\)@router\.post\("/\{invoice_id\}/send-email"',
        ')\n\n@router.post("/{invoice_id}/send-email"',
        content
    )
    
    content = re.sub(
        r'\)@router\.get\("/stats/total-income"',
        ')\n\n@router.get("/stats/total-income"',
        content
    )
    
    content = re.sub(
        r'\)@router\.post\("/calculate-discount"',
        ')\n\n@router.post("/calculate-discount"',
        content
    )
    
    content = re.sub(
        r'\)@router\.get\("/\{invoice_id\}/history"',
        ')\n\n@router.get("/{invoice_id}/history"',
        content
    )
    
    content = re.sub(
        r'\)@router\.post\("/\{invoice_id\}/history"',
        ')\n\n@router.post("/{invoice_id}/history"',
        content
    )
    
    content = re.sub(
        r'\)@router\.get\("/\{invoice_id\}/pdf"',
        ')\n\n@router.get("/{invoice_id}/pdf"',
        content
    )
    
    with open('api/routers/invoices.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed invoices router")

if __name__ == "__main__":
    fix_invoices_router() 