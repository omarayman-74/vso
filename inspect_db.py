
import json
from services.database_service import db_service

def inspect_database():
    print("--- Inspecting 'unit_search_sorting' Table ---")
    
    # Check schema
    schema_sql = "SHOW COLUMNS FROM unit_search_sorting"
    columns, error = db_service.execute_query(schema_sql)
    if error:
        print(f"Error getting schema: {error}")
        return

    print(f"Columns found: {len(columns)}")
    room_col = next((c for c in columns if c['Field'] == 'room'), None)
    if room_col:
        print(f"Column 'room' details: {room_col}")
    else:
        print("CRITICAL: Column 'room' NOT FOUND in unit_search_sorting!")

    # Check data sample
    data_sql = "SELECT unit_id, room, lang_id FROM unit_search_sorting LIMIT 10"
    rows, error = db_service.execute_query(data_sql)
    if error:
        print(f"Error getting data: {error}")
        return
        
    print(f"Sample data rows: {len(rows)}")
    for row in rows:
        print(row)

    # Check specific room count
    count_sql = "SELECT COUNT(*) as count FROM unit_search_sorting WHERE room = 3"
    count, error = db_service.execute_query(count_sql)
    print(f"Count of units with room=3 (any lang): {count}")
    
    # Check status_text for room=3 units
    print("\nChecking status_text for room=3 units:")
    status_sql = "SELECT unit_id, status_text FROM unit_search_sorting WHERE room = 3 AND lang_id = 1 LIMIT 20"
    rows, error = db_service.execute_query(status_sql)
    if rows:
        for row in rows:
            print(f"ID: {row.get('unit_id')}, Status: '{row.get('status_text')}'")
    
    # Check distinct statuses
    print("\nDistinct statuses for room=3 units:")
    distinct_sql = "SELECT DISTINCT status_text, COUNT(*) as c FROM unit_search_sorting WHERE room = 3 AND lang_id = 1 GROUP BY status_text"
    rows, error = db_service.execute_query(distinct_sql)
    if rows:
        for row in rows:
            print(f"Status: '{row.get('status_text')}' - Count: {row.get('c')}")


if __name__ == "__main__":
    inspect_database()
