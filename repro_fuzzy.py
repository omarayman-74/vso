
import sys
import os
import json
from datetime import datetime

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chat_service import chat_service
from services.agent_service import SessionMemory

def test_fuzzy_messaging():
    print("Testing Fuzzy Search Messaging and Duplication...")
    
    session_id = "test_fuzzy_session"
    session = chat_service.get_or_create_session(session_id)
    
    # 1. Simulate Fuzzy Search State
    session.last_results = [{
        "unit_id": 999,
        "compound_name": "Alternative Compound",
        "room": 9,  # Found 9 instead of 10
        "price": 5000000,
        "status_text": "Available"
    }]
    session.new_results_fetched = True
    session.alternative_search = True
    session.original_value = 10
    session.detected_language = "en"
    
    # Mock the Agent's raw output (Simulating what the LLM might say)
    # The LLM often repeats valid results if not instructed otherwise.
    # If the LLM doesn't use "1.", the current logic might fail to truncate.
    mock_llm_response = "I found this unit with 9 bedrooms which is close to your request. It is located in Alternative Compound and costs 5,000,000."
    
    # We can't easily mock the internal agent executor without heavy patching.
    # However, we can test the `_clean_image_sections` and the "REMOVE DUPLICATION" logic 
    # by calling a simplified version of that logic or just inspecting `chat_service.py` logic physically.
    
    # Instead, let's try to simulate `process_message` but we need to bypass the actual LLM call 
    # if we want a fast repro, OR we can just rely on the fact that we know the logic is in `process_message`.
    
    # Let's verify the "REMOVE DUPLICATION" logic specifically.
    
    print(f"\n[Scenario 1] LLM returns text WITHOUT numbered list")
    response_text = "I found a unit with 9 bedrooms. It is in Cairo."
    
    # Start manual logic check from chat_service.py
    detected_lang = "en"
    labels = {"found": "Found", "properties": "properties"}
    
    print(f"Original Text: {response_text}")
    
    if detected_lang in ['franco', 'franco_arabic', 'franco-arabic']:
        response_text = ""
    elif response_text and (rank := response_text.find("1.")) != -1:
        response_text = response_text[:rank].strip()
    elif not response_text:
        response_text = "Found " + str(len(session.last_results)) + " properties"
        
    print(f"Processed Text: {response_text}")
    
    if response_text == "I found a unit with 9 bedrooms. It is in Cairo.":
        print("FAIL: Text was NOT truncated because no '1.' was found.")
    else:
        print("PASS: Text was truncated.")

    # [Scenario 2] Logic for Fuzzy Search Alternative Message
    print(f"\n[Scenario 2] Check for Alternative Message Injection")
    # Current code does NOT inject an alternative message in `chat_service.py`.
    # It relies entirely on the LLM. If the LLM fails, we fail.
    # We should detect `session.alternative_search` in `chat_service.py` and PREPEND a clear message.
    
    if getattr(session, 'alternative_search', False):
         print(f"Detected Alternative Search! Original: {session.original_value}")
         print("Hypothesis: We should prepend 'I couldn't find exactly X, but found Y...' here.")

if __name__ == "__main__":
    test_fuzzy_messaging()
