"""Investigate promo table structure and compound-level discounts"""
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
print(f"INVESTIGATING PROMO TABLE STRUCTURE")
print("=" * 80)
print()

try:
    with mysql.connector.connect(**DB_CONFIG) as connection:
        cursor = connection.cursor(dictionary=True)
        
        # First get compound_id and developer_id for our unit
        print("1. GET UNIT DETAILS:")
        print("-" * 80)
        
        query = f"""
        SELECT unit_id, compound_name, comp_id, dev_id, developer_name, price
        FROM unit_search_engine
        WHERE unit_id = {unit_id}
        LIMIT 1
        """
        cursor.execute(query)
        unit = cursor.fetchone()
        
        if unit:
            print(f"Unit ID: {unit['unit_id']}")
            print(f"Compound: {unit['compound_name']}")
            print(f"Compound ID: {unit['comp_id']}")
            print(f"Developer: {unit['developer_name']}")
            print(f"Developer ID: {unit['dev_id']}")
            print(f"Price: {unit['price']}")
            
            comp_id = unit['comp_id']
            dev_id = unit['dev_id']
            
            # Check promo table structure
            print("\n\n2. PROMO TABLE STRUCTURE:")
            print("-" * 80)
            
            cursor.execute("SHOW COLUMNS FROM promo")
            promo_cols = cursor.fetchall()
            
            print(f"\nColumns in 'promo' table:")
            for col in promo_cols:
                print(f"   - {col['Field']} ({col['Type']})")
            
            # Check if there are promos for this compound
            print("\n\n3. SEARCH FOR COMPOUND-LEVEL PROMOS:")
            print("-" * 80)
            
            cursor.execute(f"SELECT * FROM promo WHERE comp_id = {comp_id} LIMIT 5")
            comp_promos = cursor.fetchall()
            
            if comp_promos:
                print(f"\n✓ Found {len(comp_promos)} promo(s) for compound ID {comp_id}:")
                for idx, promo in enumerate(comp_promos, 1):
                    print(f"\n   Promo #{idx}:")
                    for key, value in promo.items():
                        if value is not None and str(value).strip():
                            print(f"      {key}: {value}")
            else:
                print(f"\n✗ No promos found for compound ID {comp_id}")
            
            # Check promo_text table
            print("\n\n4. PROMO_TEXT TABLE STRUCTURE:")
            print("-" * 80)
            
            cursor.execute("SHOW COLUMNS FROM promo_text")
            promo_text_cols = cursor.fetchall()
            
            print(f"\nColumns in 'promo_text' table:")
            for col in promo_text_cols:
                print(f"   - {col['Field']} ({col['Type']})")
            
            # Get sample data from promo_text
            cursor.execute("SELECT * FROM promo_text LIMIT 3")
            promo_texts = cursor.fetchall()
            
            if promo_texts:
                print(f"\nSample data from promo_text:")
                for idx, pt in enumerate(promo_texts, 1):
                    print(f"\n   Row #{idx}:")
                    for key, value in pt.items():
                        print(f"      {key}: {value}")
        
        else:
            print(f"❌ Unit {unit_id} not found")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
