"""Detailed investigation of unit 53198262 discount data."""
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
print(f"DETAILED DISCOUNT INVESTIGATION FOR UNIT {unit_id}")
print("=" * 80)
print()

try:
    with mysql.connector.connect(**DB_CONFIG) as connection:
        cursor = connection.cursor(dictionary=True)
        
        # Check PROMO table using unt_id
        print("1. CHECKING PROMO TABLE:")
        print("-" * 80)
        
        query = f"SELECT * FROM promo WHERE unt_id = {unit_id}"
        cursor.execute(query)
        promo_records = cursor.fetchall()
        
        if promo_records:
            print(f"✓ Found {len(promo_records)} promo record(s)!\n")
            for idx, promo in enumerate(promo_records, 1):
                print(f"Promo Record #{idx}:")
                prom_id = promo.get('prom_id')
                
                for key, value in promo.items():
                    if value is not None:
                        print(f"  {key}: {value}")
                
                # Get promo text
                if prom_id:
                    print(f"\n  Getting promo text for prom_id {prom_id}...")
                    text_query = f"SELECT * FROM promo_text WHERE prom_id = {prom_id} AND lang_id = 1"
                    cursor.execute(text_query)
                    promo_text = cursor.fetchone()
                    
                    if promo_text:
                        print(f"  📝 Promo Text (English):")
                        for key, value in promo_text.items():
                            if value is not None:
                                print(f"     {key}: {value}")
                    
                    # Try Arabic too
                    text_query_ar = f"SELECT * FROM promo_text WHERE prom_id = {prom_id} AND lang_id = 2"
                    cursor.execute(text_query_ar)
                    promo_text_ar = cursor.fetchone()
                    
                    if promo_text_ar:
                        print(f"\n  📝 Promo Text (Arabic):")
                        for key, value in promo_text_ar.items():
                            if value is not None:
                                print(f"     {key}: {value}")
                
                print()
        else:
            print("✗ No promo records found using unt_id")
        
        # Check unit tables for has_promo and promo_text
        print("\n2. CHECKING UNIT TABLES FOR PROMO FIELDS:")
        print("-" * 80)
        
        tables = ["unit_search_engine", "unit_search_engine2", "bi_unit", "unit_details"]
        
        for table in tables:
            try:
                query = f"SELECT has_promo, promo_text, price FROM `{table}` WHERE unit_id = {unit_id}"
                cursor.execute(query)
                result = cursor.fetchone()
                
                if result:
                    print(f"\n✓ Table: {table}")
                    print(f"  has_promo: {result.get('has_promo')}")
                    print(f"  promo_text: {result.get('promo_text')}")
                    print(f"  price: {result.get('price')}")
            except Exception as e:
                print(f"\n✗ Table {table}: {str(e)}")
        
        # Check for discount-related tables
        print("\n\n3. SEARCHING ALL DISCOUNT TABLES:")
        print("-" * 80)
        
        cursor.execute("SHOW TABLES")
        all_tables = [list(row.values())[0] for row in cursor.fetchall()]
        
        discount_keywords = ['discount', 'promo', 'offer', 'sale', 'deal']
        
        for table in all_tables:
            table_lower = table.lower()
            if any(keyword in table_lower for keyword in discount_keywords):
                try:
                    # Check columns
                    cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                    columns = [col['Field'] for col in cursor.fetchall()]
                    
                    # Try unit_id
                    if 'unit_id' in columns:
                        query = f"SELECT * FROM `{table}` WHERE unit_id = {unit_id}"
                        cursor.execute(query)
                        result = cursor.fetchone()
                        
                        if result:
                            print(f"\n✓ Found in table: {table}")
                            for key, value in result.items():
                                if value is not None:
                                    print(f"  {key}: {value}")
                    
                    # Try unt_id
                    elif 'unt_id' in columns:
                        query = f"SELECT * FROM `{table}` WHERE unt_id = {unit_id}"
                        cursor.execute(query)
                        result = cursor.fetchone()
                        
                        if result:
                            print(f"\n✓ Found in table: {table}")
                            for key, value in result.items():
                                if value is not None:
                                    print(f"  {key}: {value}")
                                    
                except Exception as e:
                    continue

except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
