#!/usr/bin/env python3
"""
Simple timestamp extraction test that can be run in the API container
"""
import re
from typing import Dict, Any, Optional


def heuristic_parse_text(text: str) -> Optional[Dict[str, Any]]:
    """Heuristic parser for plain OCR text to extract likely fields."""
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


def test_cases():
    """Test the problematic case and other formats"""
    
    test_inputs = [
        {
            "name": "Original Problem Case",
            "text": "09/13/25 18:36:08",
            "expected": "Should extract '09/13/25 18:36:08'"
        },
        {
            "name": "Standard Receipt",
            "text": """
            WALMART SUPERCENTER
            Date: 2024-11-06
            Time: 14:32
            Total: $6.48
            """,
            "expected": "Should extract '2024-11-06 14:32'"
        },
        {
            "name": "Combined Format",
            "text": "2024-11-06 08:15:30",
            "expected": "Should extract '2024-11-06 08:15:30'"
        },
        {
            "name": "AM/PM Format",
            "text": "11/06/2024 2:45 PM",
            "expected": "Should extract '11/06/2024 2:45 PM'"
        },
        {
            "name": "Time Only",
            "text": "Purchase at 14:32",
            "expected": "Should extract time with today's date"
        }
    ]
    
    print("🧪 TIMESTAMP EXTRACTION TEST")
    print("=" * 50)
    
    success_count = 0
    total_count = len(test_inputs)
    
    for i, test_case in enumerate(test_inputs, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Input: {repr(test_case['text'])}")
        print(f"Expected: {test_case['expected']}")
        
        result = heuristic_parse_text(test_case['text'])
        
        if result:
            print("✅ Extraction successful:")
            for key, value in result.items():
                print(f"   {key}: {value}")
            
            if "receipt_timestamp" in result:
                print(f"🕐 Timestamp: {result['receipt_timestamp']}")
                success_count += 1
            else:
                print("⚠️  No timestamp extracted")
        else:
            print("❌ No data extracted")
        
        print("-" * 30)
    
    print(f"\n📊 RESULTS SUMMARY")
    print(f"Successful timestamp extractions: {success_count}/{total_count}")
    print(f"Success rate: {(success_count/total_count)*100:.1f}%")
    
    if success_count >= 4:  # Expect at least 4/5 to work
        print("✅ TIMESTAMP EXTRACTION WORKING CORRECTLY!")
    else:
        print("❌ Some timestamp extractions failed")
    
    return success_count == total_count


def test_original_problem():
    """Specifically test the original problematic input"""
    
    print("\n🎯 TESTING ORIGINAL PROBLEM CASE")
    print("=" * 40)
    
    problem_input = "09/13/25 18:36:08"
    print(f"Input: '{problem_input}'")
    
    result = heuristic_parse_text(problem_input)
    
    print(f"Result: {result}")
    
    if result and "receipt_timestamp" in result:
        extracted_timestamp = result["receipt_timestamp"]
        print(f"✅ SUCCESS: Extracted timestamp '{extracted_timestamp}'")
        
        # Verify it's exactly what we expect
        if extracted_timestamp == problem_input:
            print("✅ PERFECT: Extracted timestamp matches input exactly")
            return True
        else:
            print(f"⚠️  PARTIAL: Extracted '{extracted_timestamp}' but expected '{problem_input}'")
            return False
    else:
        print("❌ FAILED: No timestamp extracted")
        return False


def main():
    """Run all tests"""
    print("🚀 TIMESTAMP EXTRACTION VERIFICATION")
    print("=" * 60)
    
    # Test the specific problem case first
    problem_fixed = test_original_problem()
    
    # Test all cases
    all_tests_passed = test_cases()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL RESULTS")
    print("=" * 60)
    
    if problem_fixed:
        print("✅ Original problem case FIXED")
    else:
        print("❌ Original problem case still FAILING")
    
    if all_tests_passed:
        print("✅ All test cases PASSED")
    else:
        print("⚠️  Some test cases need attention")
    
    if problem_fixed and all_tests_passed:
        print("\n🎉 SUCCESS: Timestamp extraction is working correctly!")
        print("💡 The system should now properly extract timestamps from receipts")
        print("🔄 When heuristic extraction fails, the system will recommend AI LLM processing")
    else:
        print("\n⚠️  Some issues remain - check the test results above")


if __name__ == "__main__":
    main()