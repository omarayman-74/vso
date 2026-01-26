"""Direct database query to check discount data for unit 53198262"""
import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import mysql.connector
from config import settings

DB_CONFIG = {
    "host": settings.db_host,
    "port": settings.db_port,
    "user": settings.db_user,
    "password": settings.db_password,
    "database": settings.db_name
}

unit_id = 53198262

print("=" * 80)
print(f"DIRECT DATABASE QUERY FOR UNIT {unit_id}")
print("=" * 80)
print()

try:
    with mysql.connector.connect(**DB_CONFIG) as connection:
        cursor = connection.cursor(dictionary=True)
        
        # Check main tables first
        print("1. CHECKING MAIN UNIT TABLES:")
        print("-" * 80)
        
        tables = ["bi_unit", "unit_search_engine", "unit_search_engine2"]
        
        for table in tables:
            try:
                query = f"""
                SELECT unit_id, compound_name, price, has_promo, promo_text 
                FROM `{table}` 
                WHERE unit_id = {unit_id} 
                LIMIT 1
                """
                cursor.execute(query)
                result = cursor.fetchone()
                
                if result:
                    print(f"\n✓ Found in '{table}':")
                    print(f"   unit_id: {result.get('unit_id')}")
                    print(f"   compound_name: {result.get('compound_name')}")
                    print(f"   price: {result.get('price')}")
                    print(f"   has_promo: {result.get('has_promo')}")
                    print(f"   promo_text: {result.get('promo_text')}")
                else:
                    print(f"\n✗ Not found in '{table}'")
            except Exception as e:
                print(f"\n✗ Error querying '{table}': {str(e)}")
        
        # Now discover ALL discount tables
        print("\n\n2. DISCOVERING DISCOUNT TABLES:")
        print("-" * 80)
        
        cursor.execute("SHOW TABLES")
        all_tables = [list(row.values())[0] for row in cursor.fetchall()]
        
        discount_keywords = ['discount', 'promo', 'promotion', 'offer', 'sale', 'deal', 'special']
        discount_tables = []
        
        for table in all_tables:
            table_lower = table.lower()
            if any(keyword in table_lower for keyword in discount_keywords):
                discount_tables.append(table)
        
        print(f"\nTotal tables in database: {len(all_tables)}")
        print(f"Discount-related tables: {len(discount_tables)}")
        
        if discount_tables:
            print(f"\nDiscount tables found:")
            for dt in discount_tables:
                print(f"   - {dt}")
            
            # Check each for unit_id column
            print("\n\n3. SEARCHING DISCOUNT TABLES FOR UNIT ID:")
            print("-" * 80)
            
            for table in discount_tables:
                try:
                    # Check if table has unit_id column
                    cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                    columns = [col['Field'] for col in cursor.fetchall()]
                    
                    if 'unit_id' in columns:
                        print(f"\n✓ '{table}' has unit_id column")
                        
                        # Search for our unit
                        query = f"SELECT * FROM `{table}` WHERE unit_id = {unit_id} LIMIT 1"
                        cursor.execute(query)
                        result = cursor.fetchone()
                        
                        if result:
                            print(f"   🎯 FOUND UNIT {unit_id} in '{table}'!")
                            print(f"   Columns in this table: {', '.join(columns)}")
                            print(f"   Data:")
                            for key, value in result.items():
                                if value is not None and str(value).strip():
                                    print(f"      {key}: {value}")
                        else:
                            print(f"   - Unit {unit_id} not found in this table")
                    else:
                        print(f"\n✗ '{table}' does NOT have unit_id column")
                        
                except Exception as e:
                    print(f"\n✗ Error checking '{table}': {str(e)}")
        else:
            print("\n⚠️  No discount-related tables found in database")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("QUERY COMPLETE")
print("=" * 80)
