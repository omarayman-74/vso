"""Find units that actually have discounts in the database"""
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

print("=" * 80)
print("FINDING UNITS WITH ACTUAL DISCOUNTS IN DATABASE")
print("=" * 80)
print()

try:
    with mysql.connector.connect(**DB_CONFIG) as connection:
        cursor = connection.cursor(dictionary=True)
        
        # Find units with has_promo=1 and promo_text
        print("1. UNITS WITH has_promo=1 AND promo_text:")
        print("-" * 80)
        
        query = """
        SELECT unit_id, compound_name, price, has_promo, promo_text
        FROM unit_search_engine
        WHERE has_promo = 1 AND promo_text IS NOT NULL AND promo_text != ''
        LIMIT 10
        """
        cursor.execute(query)
        units_with_promo = cursor.fetchall()
        
        if units_with_promo:
            print(f"\n✓ Found {len(units_with_promo)} units with promo_text:\n")
            for idx, unit in enumerate(units_with_promo, 1):
                print(f"{idx}. Unit ID: {unit['unit_id']}")
                print(f"   Compound: {unit['compound_name']}")
                print(f"   Price: {unit['price']:,} EGP")
                print(f"   Promo Text: {unit['promo_text']}")
                print()
        else:
            print("\n✗ No units found with has_promo=1 and promo_text")
        
        # Find units in promo table
        print("\n2. UNITS IN PROMO TABLE:")
        print("-" * 80)
        
        query = """
        SELECT DISTINCT p.unt_id, p.prom_id, pt.title, pt.text
        FROM promo p
        LEFT JOIN promo_text pt ON p.prom_id = pt.prom_id AND pt.lang_id = 1
        WHERE p.unt_id IS NOT NULL
        LIMIT 10
        """
        cursor.execute(query)
        units_in_promo = cursor.fetchall()
        
        if units_in_promo:
            print(f"\n✓ Found {len(units_in_promo)} units in promo table:\n")
            for idx, promo in enumerate(units_in_promo, 1):
                # Get unit details
                unt_id = promo['unt_id']
                query2 = f"SELECT compound_name, price FROM unit_search_engine WHERE unit_id = {unt_id} LIMIT 1"
                cursor.execute(query2)
                unit = cursor.fetchone()
                
                print(f"{idx}. Unit ID: {unt_id}")
                if unit:
                    print(f"   Compound: {unit.get('compound_name', 'Unknown')}")
                    print(f"   Price: {unit.get('price', 0):,} EGP")
                print(f"   Promo ID: {promo['prom_id']}")
                print(f"   Promo Title: {promo['title']}")
                print(f"   Promo Text: {promo['text']}")
                print()
        else:
            print("\n✗ No units found in promo table")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("=" * 80)
print("If units are found above, test with: python test_unit_53198262.py")
print("(Just update the unit_id variable to one of the IDs above)")
print("=" * 80)
