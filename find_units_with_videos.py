"""Script to find units with video URLs in the database."""
import mysql.connector
from config import DB_CONFIG

try:
    # Connect to database
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor(dictionary=True)
    
    # Query for units with video URLs (not null and not empty)
    query = """
    SELECT 
        unit_id, 
        compound_name, 
        region_text, 
        video_url,
        price,
        room,
        area
    FROM unit_search_sorting 
    WHERE video_url IS NOT NULL 
        AND video_url != '' 
        AND lang_id = 1
    LIMIT 20
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"\n{'='*80}")
    print(f"Found {len(results)} units with video URLs:")
    print(f"{'='*80}\n")
    
    if results:
        for idx, unit in enumerate(results, 1):
            print(f"{idx}. Unit ID: {unit['unit_id']}")
            print(f"   Compound: {unit['compound_name']}")
            print(f"   Location: {unit['region_text']}")
            print(f"   Price: {unit['price']:,.0f} EGP" if unit['price'] else "   Price: N/A")
            print(f"   Bedrooms: {unit['room']}")
            print(f"   Area: {unit['area']} m²")
            print(f"   Video URL: {unit['video_url']}")
            print(f"   Property Link: https://eshtriaqar.com/en/details/{unit['unit_id']}")
            print()
    else:
        print("No units found with video URLs.")
        print("\nChecking total units with any data in video_url column...")
        
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM unit_search_sorting 
            WHERE video_url IS NOT NULL AND lang_id = 1
        """)
        count_result = cursor.fetchone()
        print(f"Total units with non-null video_url: {count_result['count']}")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"Error: {e}")
