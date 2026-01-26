"""Comprehensive unit data discovery - shows ALL data from ALL tables for a unit."""
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
import json

DB_CONFIG = {
    "host": settings.db_host,
    "port": settings.db_port,
    "user": settings.db_user,
    "password": settings.db_password,
    "database": settings.db_name
}

def discover_unit_in_all_tables(unit_id):
    """Find and display ALL data for a unit across ALL database tables."""
    print("=" * 100)
    print(f"COMPREHENSIVE UNIT DATA DISCOVERY FOR UNIT {unit_id}")
    print("=" * 100)
    print()
    
    try:
        with mysql.connector.connect(**DB_CONFIG) as connection:
            cursor = connection.cursor(dictionary=True)
            
            # Get all tables
            cursor.execute("SHOW TABLES")
            all_tables = [list(row.values())[0] for row in cursor.fetchall()]
            
            print(f"📊 Total tables in database: {len(all_tables)}\n")
            print("🔍 Searching for unit data...\n")
            print("=" * 100)
            
            tables_with_unit = []
            discount_keywords = ['promo', 'discount', 'offer', 'sale', 'deal', 'special']
            
            for table_idx, table in enumerate(all_tables, 1):
                try:
                    # Get columns
                    cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                    columns = cursor.fetchall()
                    column_names = [col['Field'] for col in columns]
                    
                    # Check if has unit_id or unt_id
                    has_unit_id = 'unit_id' in column_names
                    has_unt_id = 'unt_id' in column_names
                    
                    if has_unit_id or has_unt_id:
                        # Query for the unit
                        id_field = 'unit_id' if has_unit_id else 'unt_id'
                        query = f"SELECT * FROM `{table}` WHERE {id_field} = {unit_id} LIMIT 1"
                        cursor.execute(query)
                        result = cursor.fetchone()
                        
                        if result:
                            tables_with_unit.append(table)
                            is_discount_table = any(keyword in table.lower() for keyword in discount_keywords)
                            
                            print(f"\n{'🎁' if is_discount_table else '✅'} TABLE #{len(tables_with_unit)}: {table}")
                            if is_discount_table:
                                print(f"   ⚠️  DISCOUNT-RELATED TABLE!")
                            print(f"   ID Field: {id_field}")
                            print(f"   Total Columns: {len(column_names)}")
                            print(f"   " + "-" * 90)
                            
                            # Show ALL data
                            for key, value in result.items():
                                if value is not None and value != '':
                                    # Highlight potential discount fields
                                    is_discount_field = any(keyword in key.lower() for keyword in discount_keywords + ['price', 'payment'])
                                    prefix = "   💰 " if is_discount_field else "      "
                                    
                                    # Format value
                                    if isinstance(value, (int, float)):
                                        display_value = f"{value:,}" if value > 1000 else str(value)
                                    else:
                                        display_value = str(value)
                                        if len(display_value) > 100:
                                            display_value = display_value[:100] + "..."
                                    
                                    print(f"{prefix}{key}: {display_value}")
                            
                            print(f"   " + "-" * 90)
                
                except Exception as e:
                    # Skip tables we can't query
                    continue
            
            print(f"\n\n{'=' * 100}")
            print(f"SUMMARY")
            print(f"{'=' * 100}")
            print(f"Total tables searched: {len(all_tables)}")
            print(f"Tables containing unit {unit_id}: {len(tables_with_unit)}")
            print(f"\nTables found:")
            for idx, table in enumerate(tables_with_unit, 1):
                is_discount = any(keyword in table.lower() for keyword in discount_keywords)
                print(f"  {idx}. {table}{'  🎁 DISCOUNT-RELATED' if is_discount else ''}")
            print(f"{'=' * 100}\n")
            
            # Special focus on promo tables
            print(f"\n{'=' * 100}")
            print(f"SPECIAL CHECK: PROMO TABLES")
            print(f"{'=' * 100}\n")
            
            # Check promo table with unt_id
            print("1. Checking 'promo' table with unt_id:")
            print("-" * 90)
            try:
                cursor.execute(f"SELECT * FROM promo WHERE unt_id = {unit_id}")
                promo_records = cursor.fetchall()
                
                if promo_records:
                    print(f"   ✅ FOUND {len(promo_records)} PROMO RECORD(S)!\n")
                    for idx, promo in enumerate(promo_records, 1):
                        print(f"   Promo #{idx}:")
                        for key, value in promo.items():
                            if value is not None:
                                print(f"      {key}: {value}")
                        
                        # Get promo text
                        prom_id = promo.get('prom_id')
                        if prom_id:
                            cursor.execute(f"SELECT * FROM promo_text WHERE prom_id = {prom_id}")
                            promo_texts = cursor.fetchall()
                            if promo_texts:
                                print(f"\n      📝 PROMO TEXTS:")
                                for text in promo_texts:
                                    print(f"         Lang {text.get('lang_id')}: {text.get('title')} - {text.get('text')}")
                        print()
                else:
                    print("   ❌ No records found with unt_id\n")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}\n")
            
            # Check promo table with unit_id
            print("2. Checking 'promo' table with unit_id:")
            print("-" * 90)
            try:
                cursor.execute(f"SELECT * FROM promo WHERE unit_id = {unit_id}")
                promo_records = cursor.fetchall()
                
                if promo_records:
                    print(f"   ✅ FOUND {len(promo_records)} PROMO RECORD(S)!\n")
                    for idx, promo in enumerate(promo_records, 1):
                        print(f"   Promo #{idx}:")
                        for key, value in promo.items():
                            if value is not None:
                                print(f"      {key}: {value}")
                        print()
                else:
                    print("   ❌ No records found with unit_id\n")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}\n")
            
            print(f"{'=' * 100}\n")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    unit_id = 53198262
    
    # Allow command line argument
    if len(sys.argv) > 1:
        try:
            unit_id = int(sys.argv[1])
        except:
            pass
    
    discover_unit_in_all_tables(unit_id)
    
    print("\n" + "=" * 100)
    print("DISCOVERY COMPLETE")
    print("=" * 100)
