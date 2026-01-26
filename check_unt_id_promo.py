"""Search for unit 53198262 using unt_id instead of unit_id"""
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
print(f"SEARCHING FOR PROMOS USING unt_id FIELD")
print("=" * 80)
print()

try:
    with mysql.connector.connect(**DB_CONFIG) as connection:
        cursor = connection.cursor(dictionary=True)
        
        # Check if promo table has this unt_id
        print("1. CHECKING PROMO TABLE FOR unt_id:")
        print("-" * 80)
        
        query = f"SELECT * FROM promo WHERE unt_id = {unit_id} LIMIT 10"
        cursor.execute(query)
        promos = cursor.fetchall()
        
        if promos:
            print(f"\n🎯 FOUND {len(promos)} PROMO(S) for unt_id {unit_id}!\n")
            
            for idx, promo in enumerate(promos, 1):
                print(f"Promo #{idx}:")
                prom_id = promo.get('prom_id')
                
                for key, value in promo.items():
                    print(f"   {key}: {value}")
                
                # Get promo text for this promo_id
                if prom_id:
                    text_query = f"SELECT * FROM promo_text WHERE prom_id = {prom_id} AND lang_id = 1"
                    cursor.execute(text_query)
                    promo_text = cursor.fetchone()
                    
                    if promo_text:
                        print(f"\n   📝 Promo Text:")
                        print(f"      Title: {promo_text.get('title')}")
                        print(f"      Text: {promo_text.get('text')}")
                
                print()
        else:
            print(f"\n✗ No promos found for unt_id {unit_id}")
        
        # Also check for compound-level promos
        print("\n2. CHECK COMPOUND-LEVEL PROMOS:")
        print("-" * 80)
        
        # Get comp_id first
        cursor.execute(f"SELECT comp_id, compound_name FROM unit_search_engine WHERE unit_id = {unit_id}")
        unit = cursor.fetchone()
        
        if unit:
            comp_id = unit['comp_id']
            print(f"\nCompound: {unit['compound_name']} (ID: {comp_id})")
            
            query = f"SELECT * FROM promo WHERE comp_id = {comp_id} AND unt_id IS NULL LIMIT 10"
            cursor.execute(query)
            comp_promos = cursor.fetchall()
            
            if comp_promos:
                print(f"\n✓ Found {len(comp_promos)} compound-level promo(s):")
                
                for idx, promo in enumerate(comp_promos, 1):
                    print(f"\nPromo #{idx}:")
                    prom_id = promo.get('prom_id')
                    
                    for key, value in promo.items():
                        print(f"   {key}: {value}")
                    
                    # Get promo text
                    if prom_id:
                        text_query = f"SELECT * FROM promo_text WHERE prom_id = {prom_id} AND lang_id = 1"
                        cursor.execute(text_query)
                        promo_text = cursor.fetchone()
                        
                        if promo_text:
                            print(f"\n   📝 Promo Text:")
                            print(f"      Title: {promo_text.get('title')}")
                            print(f"      Text: {promo_text.get('text')}")
            else:
                print(f"\n✗ No compound-level promos found")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("SEARCH COMPLETE")
print("=" * 80)
