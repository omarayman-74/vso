"""Test script to verify discount-aware payment plan functionality."""
import sys
import os

# Fix Windows encoding for emoji output
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.agent_service import _get_payment_plan_impl
from diagnose_discrepancies import find_units_with_discounts
import mysql.connector
from config import settings

# Database configuration
DB_CONFIG = {
    "host": settings.db_host,
    "port": settings.db_port,
    "user": settings.db_user,
    "password": settings.db_password,
    "database": settings.db_name
}


def test_payment_plan_with_discount():
    """Test payment plan for units with promotional pricing."""
    print("\n" + "="*80)
    print("TESTING DISCOUNT-AWARE PAYMENT PLAN")
    print("="*80 + "\n")
    
    try:
        # Find units with discounts
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        print("Finding units with promotional pricing...")
        cursor.execute("""
            SELECT unit_id, compound_name, price, has_promo, promo_text
            FROM unit_search_sorting 
            WHERE has_promo = 1 AND lang_id = 1 AND price > 0
            LIMIT 3
        """)
        
        units_with_discounts = cursor.fetchall()
        
        if not units_with_discounts:
            print("No units found with promotional pricing (has_promo = 1)")
            print("\nTesting with a regular unit instead...")
            
            # Get a regular unit for comparison
            cursor.execute("""
                SELECT unit_id, compound_name, price, has_promo, promo_text
                FROM unit_search_sorting 
                WHERE lang_id = 1 AND price > 0
                LIMIT 1
            """)
            test_unit = cursor.fetchone()
        else:
            print(f"\nFound {len(units_with_discounts)} units with promotions:\n")
            for idx, unit in enumerate(units_with_discounts, 1):
                print(f"{idx}. Unit ID: {unit['unit_id']}")
                print(f"   Compound: {unit['compound_name']}")
                print(f"   Price: {unit['price']:,.0f} EGP" if unit['price'] else "   Price: N/A")
                print(f"   Promo: {unit['promo_text']}")
                print()
            
            test_unit = units_with_discounts[0]
        
        cursor.close()
        connection.close()
        
        # Test payment plan function
        if test_unit:
            print("\n" + "-"*80)
            print(f"Testing Payment Plan for Unit ID: {test_unit['unit_id']}")
            print("-"*80 + "\n")
            
            result = _get_payment_plan_impl(test_unit['unit_id'])
            
            print("\n" + "="*80)
            print("PAYMENT PLAN RESULT:")
            print("="*80 + "\n")
            print(result)
            print("\n" + "="*80)
            
            # Check if discount information is included
            if test_unit.get('has_promo'):
                if 'Special Offer' in result:
                    print("\nSUCCESS: Discount information is displayed!")
                else:
                    print("\nFAILED: Discount information not found in payment plan")
            else:
                print("\nRegular payment plan (no discount expected)")
                
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


def test_payment_plan_without_discount():
    """Test payment plan for units without promotional pricing."""
    print("\n" + "="*80)
    print("TESTING PAYMENT PLAN WITHOUT DISCOUNT")
    print("="*80 + "\n")
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        print("Finding unit without promotional pricing...")
        cursor.execute("""
            SELECT unit_id, compound_name, price, has_promo, promo_text
            FROM unit_search_sorting 
            WHERE (has_promo = 0 OR has_promo IS NULL) AND lang_id = 1 AND price > 0
            LIMIT 1
        """)
        
        unit = cursor.fetchone()
        
        if unit:
            print(f"\nFound unit: {unit['unit_id']} - {unit['compound_name']}")
            print(f"   Price: {unit['price']:,.0f} EGP")
            print(f"   Has Promo: {unit['has_promo']}")
            
            cursor.close()
            connection.close()
            
            # Test payment plan function
            print("\n" + "-"*80)
            print(f"Testing Payment Plan for Unit ID: {unit['unit_id']}")
            print("-"*80 + "\n")
            
            result = _get_payment_plan_impl(unit['unit_id'])
            
            print("\n" + "="*80)
            print("PAYMENT PLAN RESULT:")
            print("="*80 + "\n")
            print(result)
            print("\n" + "="*80)
            
            # Verify no discount section is shown
            if 'Special Offer' not in result:
                print("\nSUCCESS: No discount section shown (as expected)")
            else:
                print("\nFAILED: Discount section shown for non-promotional unit")
        else:
            print("No units found without promotional pricing")
            cursor.close()
            connection.close()
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Test with discount
    test_payment_plan_with_discount()
    
    print("\n\n")
    
    # Test without discount
    test_payment_plan_without_discount()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")
