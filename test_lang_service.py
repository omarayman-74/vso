import sys
import os
import json
from services.language_service import detect_language

def test_language_detection():
    print("Testing Enhanced Language Detection...")
    
    test_cases = [
        ("3ayez sha2a fe el tagamo3", "franco"),
        ("عايز شقة في التجمع", "ar"),
        ("I want an apartment in New Cairo", "en"),
        ("meen el developer?", "franco"),
        ("kam el se3r?", "franco"),
        ("شقة 3 غرف", "ar"), # Should be AR despite number
        ("3owd", "franco") # Should be Franco because of pattern
    ]
    
    for text, expected in test_cases:
        result_json = detect_language(text)
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        detected = result.get('language')
        
        # Mapping for validation if needed (though service should return ar/franco/en now)
        print(f"Input: '{text}' -> Detected: {detected} | Expected: {expected}")
        
        if detected == expected or (expected == 'ar' and detected == 'arabic') or (expected == 'franco' and detected == 'franco_arabic'):
             print("✅ PASS")
        else:
             print(f"❌ FAIL (Expected {expected}, got {detected})")

if __name__ == "__main__":
    test_language_detection()
