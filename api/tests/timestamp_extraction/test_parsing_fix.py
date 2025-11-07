#!/usr/bin/env python3
"""
Quick test for the improved timestamp parsing
"""
import sys
import os
import re
from typing import Dict, Any, Optional

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def _heuristic_parse_text(text: str) -> Optional[Dict[str, Any]]:
    """Heuristic parser for plain OCR text to extract likely fields."""
    import re
    data: Dict[str, Any] = {}
    
    # Amount / total
    m_total = re.search(r"\btotal\s*[:\-]?\s*([$€£R$]?\s*[0-9.,]+)\b", text, flags=re.IGNORECASE)
    if m_total:
        data["total"] = m_total.group(1)
    m_amt = re.search(r"\bamount\s*[:\-]?\s*([$€£R$]?\s*[0-9.,]+)\b", text, flags=re.IGNORECASE)
    if m_amt and "total" not in data:
        data["amount"] = m_amt.group(1)
    
    # Currency
    m_cur = re.search(r"\b(USD|EUR|GBP|CAD|AUD|JPY|CHF|CNY|INR|BRL)\b", text, flags=re.IGNORECASE)
    if m_cur:
        data["currency"] = m_cur.group(1).upper()
    
    # Enhanced timestamp parsing - try multiple patterns
    timestamp_found = False
    
    # Pattern 1: Combined datetime formats (MM/DD/YY HH:MM:SS, YYYY-MM-DD HH:MM:SS, etc.)
    combined_patterns = [
        r"(\d{2}/\d{2}/\d{2,4}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)",  # MM/DD/YY HH:MM:SS
        r"(\d{4}[-/.]\d{2}[-/.]\d{2}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)",  # YYYY-MM-DD HH:MM:SS
        r"(\d{2}[-/.]\d{2}[-/.]\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)",  # DD/MM/YYYY HH:MM:SS
    ]
    
    for pattern in combined_patterns:
        m_combined = re.search(pattern, text)
        if m_combined:
            data["receipt_timestamp"] = m_combined.group(1)
            timestamp_found = True
            break
    
    # If no combined timestamp found, try separate date and time
    if not timestamp_found:
        # Date patterns
        m_date = re.search(r"(\d{4}[-/.]\d{2}[-/.]\d{2}|\d{2}[/.-]\d{2}[/.-]\d{2,4})", text)
        if m_date:
            data["date"] = m_date.group(1)
        
        # Time patterns
        m_time = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)", text)
        
        if m_time and m_date:
            # Combine date and time if both found
            try:
                date_str = m_date.group(1)
                time_str = m_time.group(1)
                data["receipt_timestamp"] = f"{date_str} {time_str}"
                timestamp_found = True
            except Exception:
                pass
        elif m_time:
            # Just time found, use today's date
            try:
                from datetime import datetime
                today = datetime.now().strftime("%Y-%m-%d")
                time_str = m_time.group(1)
                data["receipt_timestamp"] = f"{today} {time_str}"
                timestamp_found = True
            except Exception:
                pass
    
    # Vendor (first non-timestamp line that looks like a business name)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines:
        # Skip lines that look like timestamps or amounts
        if not re.search(r"\d{1,2}:\d{2}|\$\d+|\d+\.\d{2}", line) and len(line) > 3:
            data["vendor"] = line[:80]
            break
    
    return data if data else None


def test_problematic_input():
    """Test the problematic input that was failing"""
    test_input = "09/13/25 18:36:08"
    
    print(f"Testing input: '{test_input}'")
    print("=" * 50)
    
    result = _heuristic_parse_text(test_input)
    
    print("Result:")
    if result:
        for key, value in result.items():
            print(f"  {key}: {value}")
    else:
        print("  No data extracted")
    
    # Test the regex patterns individually
    print("\nRegex Pattern Analysis:")
    print("-" * 30)
    
    # Combined patterns
    combined_patterns = [
        (r"(\d{2}/\d{2}/\d{2,4}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)", "MM/DD/YY HH:MM:SS"),
        (r"(\d{4}[-/.]\d{2}[-/.]\d{2}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)", "YYYY-MM-DD HH:MM:SS"),
        (r"(\d{2}[-/.]\d{2}[-/.]\d{4}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)", "DD/MM/YYYY HH:MM:SS"),
    ]
    
    for pattern, description in combined_patterns:
        match = re.search(pattern, test_input)
        if match:
            print(f"✅ {description}: '{match.group(1)}'")
        else:
            print(f"❌ {description}: No match")
    
    # Separate patterns
    print("\nSeparate Pattern Analysis:")
    print("-" * 30)
    
    date_match = re.search(r"(\d{4}[-/.]\d{2}[-/.]\d{2}|\d{2}[/.-]\d{2}[/.-]\d{2,4})", test_input)
    if date_match:
        print(f"Date found: '{date_match.group(1)}'")
    else:
        print("No date found")
    
    time_match = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)", test_input)
    if time_match:
        print(f"Time found: '{time_match.group(1)}'")
    else:
        print("No time found")


def test_multiple_inputs():
    """Test multiple timestamp formats"""
    test_cases = [
        "09/13/25 18:36:08",
        "2024-11-06 14:32",
        "11/06/2024 2:45 PM",
        "06/11/2024 16:22",
        "2024-11-06 08:15:30",
        "Date: 2024-11-06\nTime: 14:32",
        "Just a time: 14:32",
        "No timestamp here"
    ]
    
    print("\n" + "=" * 60)
    print("TESTING MULTIPLE INPUTS")
    print("=" * 60)
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test_input}'")
        print("-" * 40)
        
        result = _heuristic_parse_text(test_input)
        
        if result:
            timestamp = result.get("receipt_timestamp")
            if timestamp:
                print(f"✅ Timestamp extracted: '{timestamp}'")
            else:
                print("⚠️  Data extracted but no timestamp")
                print(f"   Extracted: {result}")
        else:
            print("❌ No data extracted")


if __name__ == "__main__":
    test_problematic_input()
    test_multiple_inputs()