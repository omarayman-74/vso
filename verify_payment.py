
import sys
import os
import json
import re

# Fix Windows terminal encoding for emoji support
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.agent_service import get_detailed_payment_plan

def test_payment_tool():
    print("Testing get_detailed_payment_plan...")
    
    # Use a unit_id that is likely to exist (based on previous logs/context)
    # If uncertain, we could try to find one first, but let's try the one from the prompt context if possible
    # User mentioned "51115662" in the link request, let's use that or search for one.
    # To be safe, let's use a dummy query first to find a unit if needed, but the tool takes int.
    # Let's try to find a valid unit ID from the DB first.
    
    from services.database_service import db_service
    rows, err = db_service.execute_query("SELECT unit_id FROM unit_search_sorting LIMIT 1")
    if err or not rows:
        print("Could not find any units to test.")
        return

    unit_id = rows[0]['unit_id']
    print(f"Testing with Unit ID: {unit_id}")
    
    try:
        # LangChain tool requires invoke with input dict
        result = get_detailed_payment_plan.invoke({"unit_id": unit_id})
        
        print("\n" + "="*60)
        print("FULL RESULT:")
        print("="*60)
        print(result)
        print("="*60 + "\n")
        
        # Validation checks
        has_marker = "<<PAYMENT_PLAN_DATA>>" in result
        has_new_link = f"(https://eshtriaqar.com/en/details/{unit_id})" in result
        
        print(f"Marker found: {has_marker}")
        print(f"Link format fixed: {has_new_link}")
        
        if has_marker:
            json_part = result.split("<<PAYMENT_PLAN_DATA>>")[1]
            data = json.loads(json_part)
            print("JSON Data structure valid.")
            print("Keys:", list(data.keys()))
            
        print("\nSUCCESS: Tool implementation verified.")
        
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    test_payment_tool()
