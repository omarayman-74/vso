import requests
import json
import sys

url = "http://localhost:8000/api/chat"
payload = {"message": "ما هي المشاريع المتاحة؟", "session_id": "test_session"}
headers = {"Content-Type": "application/json"}

try:
    print(f"Sending request to {url} with payload: {payload}")
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    print("Response Status:", response.status_code)
    # Use ensure_ascii=True to avoid console encoding errors on Windows
    print("Response Body:", json.dumps(response.json(), ensure_ascii=True, indent=2))
except Exception as e:
    print(f"Request failed: {e}")
    if 'response' in locals():
        print("Error Response:", response.text)
