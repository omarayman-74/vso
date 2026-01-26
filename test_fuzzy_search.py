import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.chat_service import chat_service
# We might need to access session memory directly for debug, but chat_service manages it.

def test_fuzzy_search_logic():
    print("\n" + "="*60)
    print("TEST: Fuzzy Search Logic Verification")
    print("="*60)
    
    # Session ID for isolation
    session_id = "test_fuzzy_session_1"
    
    # Query for something likely to fail exact match (e.g. 10 bedrooms)
    query = "I want 10 bedrooms"
    print(f"Query: {query}")
    
    result = chat_service.process_message(session_id, query)
    response_text = result['response']
    
    print("\n[RESULT]")
    print(response_text)
    
    # Verification checks
    if "I couldn't find units with exactly 10" in response_text or "alternatives" in response_text.lower():
        print("\n[PASS] Correct message received about missing exact match/alternatives.")
    else:
        print("\n[FAIL] Did not receive expected 'no exact match' message.")
        
    if "JSON_DATA" in response_text or "PROPERTY_CAROUSEL_DATA" in response_text or "Found" in response_text:
        # The agent might wrap the tool output
        print("[PASS] Results appear to be returned.")

if __name__ == "__main__":
    test_fuzzy_search_logic()
