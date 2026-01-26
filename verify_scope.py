
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chat_service import chat_service

# Fix Windows encoding for output
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def test_scope():
    print("Testing Scope Restriction...")
    
    # Test case 1: Out of scope
    query1 = "What is the capital of Spain?"
    print(f"\nQuery: {query1}")
    response1 = chat_service.process_message("test_session", query1)
    print(f"Response: {response1['response']}")
    
    if "I apologize" in response1['response'] and "related to real estate" in response1['response']:
        print("PASS: Correctly refused out-of-scope query.")
    else:
        print("FAIL: Did not refuse out-of-scope query correctly.")

    # Test case 2: In scope
    query2 = "Show me apartments in Cairo"
    print(f"\nQuery: {query2}")
    response2 = chat_service.process_message("test_session", query2)
    # We just check if it doesn't apologize in the restriction way
    if "I apologize, but I can only answer questions related to real estate" not in response2['response']:
        print("PASS: Accepted in-scope query.")
    else:
        print("FAIL: Incorrectly refused in-scope query.")

    # Test case 3: Greeting (should be accepted)
    query3 = "Hello"
    print(f"\nQuery: {query3}")
    response3 = chat_service.process_message("test_session", query3)
    if "Welcome to Eshtri Aqar" in response3['response']:
        print("PASS: Correctly handled greeting.")
    else:
        print(f"FAIL: Greeting not handled correctly. Got: {response3['response']}")


if __name__ == "__main__":
    test_scope()
