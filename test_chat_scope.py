"""Test Chat Agent scope enforcement."""
import sys
import os

# Add root directory to path
sys.path.append(os.path.abspath(os.curdir))

from services.chat_service import chat_service
import json

def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))

def test_query(session_id, query, expected_in_response=None):
    safe_print(f"\nQUERY: {query}")
    result = chat_service.process_message(session_id, query)
    response = result.get("response", "")
    safe_print(f"RESPONSE: {response}")
    
    if expected_in_response:
        if expected_in_response in response:
            print("[PASS] Response matches expected template portion.")
        else:
            print("[FAIL] Response DOES NOT match expected template portion.")
    return response

# Test session
session_id = "test_scope_session"

print("=" * 60)
print("TESTING CHAT AGENT SCOPE ENFORCEMENT")
print("=" * 60)

# 1. Off-topic English
test_query(session_id, "How do I make a chocolate cake?", "I apologize, but I'm a real estate assistant")

# 2. Off-topic Arabic
test_query(session_id, "من فاز بالدوري الإنجليزي العام الماضي؟", "أعتذر، أنا مساعد عقاري")

# 3. Off-topic Franco
test_query(session_id, "momken te2oly taree2et el pasta?", "Ana assef, ana mosa3ed 3a2ary")

# 3b. More off-topic (Tricky)
test_query(session_id, "Tell me a joke", "I apologize")
test_query(session_id, "What is the weather in Cairo?", "I apologize")

# 4. Legit Greeting (should pass)
print("\n--- GREETINGS (should work) ---")
test_query(session_id, "Hi there")

# 5. Legit Real Estate (should pass)
print("\n--- REAL ESTATE (should work) ---")
test_query(session_id, "What is a compound?")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
