
import sys
import os
import json
from datetime import datetime

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chat_service import chat_service
from services.agent_service import SessionMemory

def test_serialization():
    print("Testing chat service serialization fix...")
    
    # Mock session memory with a fake result containing a datetime object
    session_id = "test_session_123"
    session = chat_service.get_or_create_session(session_id)
    
    # Inject a fake result with datetime objects to trigger the carousel logic
    session.last_results = [{
        "unit_id": 12345,
        "compound_name": "Test Compound",
        "developer_name": "Test Dev",
        "price": 1000000,
        "area": 100,
        "room": 3,
        "bathroom": 2,
        "delivery_date": datetime.now(), # This would cause the error before
        "status_text": "Available",
        "unit_image": "image.jpg",
        "compound_image": "c_image.jpg",
        "has_promo": 0,
        "promo_text": None
    }]
    session.new_results_fetched = True
    session.detected_language = "en"
    
    # Trigger the process_message logic that builds the carousel
    # We pass a message that is NOT a detail request so it triggers the carousel
    try:
        response = chat_service.process_message(session_id, "show me units")
        print("SUCCESS: process_message completed without error.")
        
        # Check if carousel data is in the response and is valid JSON
        resp_text = response.get("response", "")
        if "<<PROPERTY_CAROUSEL_DATA>>" in resp_text:
            json_part = resp_text.split("<<PROPERTY_CAROUSEL_DATA>>")[1].split("\n\n")[0]
            try:
                data = json.loads(json_part)
                print("SUCCESS: JSON data in response is valid.")
                print(f"Carousel count: {data.get('count')}")
            except json.JSONDecodeError as e:
                print(f"FAILURE: JSON decode error: {e}")
        else:
            print("WARNING: Carousel marker not found in response (logic might have skipped it).")
            
    except Exception as e:
        print(f"FAILURE: process_message raised exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_serialization()
