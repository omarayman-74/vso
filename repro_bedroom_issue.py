
import os
import sys
import json
from services.agent_service import generate_sql_tool, execute_sql_tool

def test_bedroom_search():
    # Test cases
    test_cases = [
        {"lang": "en", "query": "3 bedroom apartments", "lang_id": 1, "expected_rooms": 3},
        {"lang": "ar", "query": "شقق 3 غرف", "lang_id": 2, "expected_rooms": 3}
    ]

    for case in test_cases:
        print(f"\n--- Testing {case['lang'].upper()} Search for {case['expected_rooms']} Rooms ---")
        print(f"Query: {case['query']}")
        
        # 1. Generate SQL
        try:
            sql = generate_sql_tool(case['query'], lang_id=case['lang_id'])
            print(f"Generated SQL: {sql}")
        except Exception as e:
            print(f"Error generating SQL: {e}")
            continue
        
        # 2. Execute SQL
        try:
            results_json = execute_sql_tool(sql)
            results = json.loads(results_json)
            print(f"Results found: {len(results)}")
            
            if len(results) > 0:
                # Verify room count in first few results
                match_count = 0
                for res in results[:5]:
                    room_count = res.get('room')
                    print(f"Result: {res.get('compound_name')} - {room_count} rooms")
                    # Note: 'room' field might be string or int in DB
                    if str(room_count) == str(case['expected_rooms']):
                        match_count += 1
                
                print(f"Matched {match_count} out of checked results")
            else:
                print("No results found.")
                
        except Exception as e:
            print(f"Error executing SQL: {e}")

if __name__ == "__main__":
    test_bedroom_search()
