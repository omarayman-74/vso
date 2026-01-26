"""
Diagnostic script to identify data discrepancies between website and chatbot.
Run this script to check:
1. Price differences (original vs promotional)
2. Payment plan differences  
3. Language-specific data
4. Database table comparisons
"""

import mysql.connector
from config import DB_CONFIG

def check_unit_discrepancies(unit_id):
    """Check all potential data discrepancies for a specific unit."""
    
    print(f"\n{'='*80}")
    print(f"DIAGNOSTIC REPORT FOR UNIT ID: {unit_id}")
    print(f"{'='*80}\n")
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # 1. Check data across different language IDs
        print("1. LANGUAGE VERSIONS:")
        print("-" * 60)
        cursor.execute(f"""
            SELECT lang_id, price, has_promo, promo_text, payment_plan,
                   down_payment, deposit, monthly_installment, delivery_date
            FROM unit_search_sorting 
            WHERE unit_id = {unit_id}
        """)
        lang_results = cursor.fetchall()
        
        for row in lang_results:
            print(f"\n  Lang ID {row['lang_id']}:")
            print(f"    Price: {row['price']:,.0f} EGP" if row['price'] else "    Price: N/A")
            print(f"    Has Promo: {row['has_promo']}")
            if row['promo_text']:
                print(f"    Promo Text: {row['promo_text']}")
            print(f"    Payment Plan: {row['payment_plan']}")
            print(f"    Down Payment: {row['down_payment']:,.0f} EGP" if row['down_payment'] else "    Down Payment: N/A")
            print(f"    Deposit: {row['deposit']:,.0f} EGP" if row['deposit'] else "    Deposit: N/A")
            print(f"    Monthly Installment: {row['monthly_installment']:,.0f} EGP" if row['monthly_installment'] else "    Monthly Installment: N/A")
            print(f"    Delivery Date: {row['delivery_date']}")
        
        # 2. Check promotional pricing
        print(f"\n\n2. PROMOTIONAL PRICING ANALYSIS:")
        print("-" * 60)
        cursor.execute(f"""
            SELECT price, has_promo, promo_text 
            FROM unit_search_sorting 
            WHERE unit_id = {unit_id} AND lang_id = 1
        """)
        promo_data = cursor.fetchone()
        
        if promo_data:
            print(f"  Original Price: {promo_data['price']:,.0f} EGP" if promo_data['price'] else "  Original Price: N/A")
            print(f"  Has Promotion: {'Yes' if promo_data['has_promo'] else 'No'}")
            
            if promo_data['has_promo'] and promo_data['promo_text']:
                print(f"  Promo Details: {promo_data['promo_text']}")
                
                # Try to extract discount percentage
                import re
                discount_match = re.search(r'(\d+)%', promo_data['promo_text'])
                if discount_match:
                    discount_pct = int(discount_match.group(1))
                    original_price = float(promo_data['price'] or 0)
                    discounted_price = original_price * (1 - discount_pct/100)
                    print(f"  Calculated Discounted Price: {discounted_price:,.0f} EGP")
                    print(f"  Discount: {discount_pct}%")
        
        # 3. Check across different tables
        print(f"\n\n3. DATA ACROSS DIFFERENT TABLES:")
        print("-" * 60)
        
        tables_to_check = [
            "unit_search_sorting",
            "unit_search_engine",
            "bi_unit"
        ]
        
        for table in tables_to_check:
            try:
                # Check if table exists and has unit_id column
                cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                columns = [col['Field'] for col in cursor.fetchall()]
                
                if 'unit_id' in columns:
                    # Get data from this table
                    payment_cols = [col for col in columns if any(
                        keyword in col.lower() for keyword in 
                        ['price', 'payment', 'down', 'deposit', 'installment', 'plan']
                    )]
                    
                    if payment_cols:
                        col_str = ', '.join(payment_cols[:10])  # Limit to first 10
                        cursor.execute(f"SELECT {col_str} FROM `{table}` WHERE unit_id = {unit_id} LIMIT 1")
                        result = cursor.fetchone()
                        
                        if result:
                            print(f"\n  Table: {table}")
                            for col in payment_cols[:10]:
                                value = result.get(col)
                                if value is not None:
                                    print(f"    {col}: {value}")
            except Exception as e:
                print(f"\n  Error checking table '{table}': {str(e)}")
                continue
        
        # 4. Show what the chatbot sees (lang_id = 1 only)
        print(f"\n\n4. WHAT THE CHATBOT SEES (lang_id = 1):")
        print("-" * 60)
        cursor.execute(f"""
            SELECT unit_id, compound_name, region_text, price, area, room, bathroom,
                   has_promo, promo_text, payment_plan, down_payment, deposit, 
                   monthly_installment, delivery_date
            FROM unit_search_sorting 
            WHERE unit_id = {unit_id} AND lang_id = 1
        """)
        chatbot_view = cursor.fetchone()
        
        if chatbot_view:
            for key, value in chatbot_view.items():
                if value is not None:
                    print(f"  {key}: {value}")
        else:
            print("  ⚠️ NO DATA FOUND for lang_id = 1")
            print("  This means the chatbot cannot see this unit!")
        
        cursor.close()
        connection.close()
        
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"\nError: {e}")


def find_units_with_discounts():
    """Find units that have promotional pricing to test."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        print("\nFINDING UNITS WITH PROMOTIONAL PRICING...")
        print("="*80)
        
        cursor.execute("""
            SELECT unit_id, compound_name, price, has_promo, promo_text
            FROM unit_search_sorting 
            WHERE has_promo = 1 AND lang_id = 1
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        
        if results:
            print(f"\nFound {len(results)} units with promotions:\n")
            for idx, unit in enumerate(results, 1):
                print(f"{idx}. Unit ID: {unit['unit_id']}")
                print(f"   Compound: {unit['compound_name']}")
                print(f"   Price: {unit['price']:,.0f} EGP" if unit['price'] else "   Price: N/A")
                print(f"   Promo: {unit['promo_text']}")
                print()
        else:
            print("\n⚠️ No units found with promotional pricing (has_promo = 1)")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("DATA DISCREPANCY DIAGNOSTIC TOOL")
    print("="*80)
    
    # First, find units with discounts
    find_units_with_discounts()
    
    # Then check a specific unit if provided
    print("\n\nTo check a specific unit, enter the unit ID below:")
    print("(Press Enter to skip)")
    
    unit_input = input("Unit ID: ").strip()
    
    if unit_input and unit_input.isdigit():
        check_unit_discrepancies(int(unit_input))
    else:
        print("\nNo unit ID provided. Diagnostic complete.")
