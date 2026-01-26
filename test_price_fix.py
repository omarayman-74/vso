"""
Test script to verify the fix for unit details price display.
Tests that unit 63182552 shows correct price (86.2M) instead of wrong price (3M).
"""
import requests
import json

# Server URL
SERVER_URL = "http://localhost:8005"

# Test session ID
SESSION_ID = "test_fix_price_display"

def test_unit_details():
    """Test asking for unit details"""
    
    # Query for unit details
    query = "Retrieve full details for unit number 63182552 from the database."
    
    print(f"\n{'='*80}")
    print(f"Testing: {query}")
    print(f"{'='*80}\n")
    
    # Send request
    response = requests.post(
        f"{SERVER_URL}/chat",
        json={
            "session_id": SESSION_ID,
            "message": query
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        bot_response = result.get("response", "")
        
        print("BOT RESPONSE:")
        print(bot_response)
        print(f"\n{'='*80}\n")
        
        # Check for correct values
        has_correct_price = "86,200,000" in bot_response or "86200000" in bot_response
        has_wrong_price = "3,000,000" in bot_response and "86" not in bot_response
        has_correct_bedrooms = "9" in bot_response
        has_wrong_bedrooms = "3 bedrooms" in bot_response or "3 Bedrooms" in bot_response
        has_correct_area = "500" in bot_response
        has_wrong_area = "150" in bot_response
        
        print("VERIFICATION:")
        print(f"✓ Correct price (86.2M):     {has_correct_price}")
        print(f"✗ Wrong price (3M):          {has_wrong_price}")
        print(f"✓ Correct bedrooms (9):      {has_correct_bedrooms}")
        print(f"✗ Wrong bedrooms (3):        {has_wrong_bedrooms}")
        print(f"✓ Correct area (500m²):      {has_correct_area}")
        print(f"✗ Wrong area (150m²):        {has_wrong_area}")
        
        if has_correct_price and has_correct_bedrooms and has_correct_area:
            print("\n✅ FIX SUCCESSFUL! All values are correct.")
            return True
        else:
            print("\n❌ FIX FAILED! Some values are still wrong.")
            return False
    else:
        print(f"ERROR: Request failed with status {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    success = test_unit_details()
    exit(0 if success else 1)
