
import json
from datetime import datetime
from services.database_service import safe_serialize

def test_safe_serialize():
    data = {
        "id": 1,
        "date": datetime.now(),
        "name": "Test"
    }
    
    try:
        json_str = json.dumps(data, default=safe_serialize)
        print("SUCCESS: Serialization worked!")
        print(f"Result: {json_str}")
    except TypeError as e:
        print(f"FAILURE: Serialization failed: {e}")

if __name__ == "__main__":
    test_safe_serialize()
