"""
Test script to verify cross-table discount discovery in payment plans.

This script allows you to test the discount discovery functionality by:
1. Entering a unit ID
2. Seeing which discount tables exist in the database
3. Checking if the unit has a discount
4. Viewing the complete payment plan with discount information
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.agent_service import _get_payment_plan_impl
import json


def test_payment_plan(unit_id):
    """Test payment plan for a specific unit."""
    print("=" * 80)
    print(f"TESTING PAYMENT PLAN FOR UNIT ID: {unit_id}")
    print("=" * 80)
    print()
    
    try:
        # Call the payment plan function
        result = _get_payment_plan_impl(unit_id)
        
        # Check if result is JSON (error) or markdown (success)
        try:
            error_data = json.loads(result)
            if error_data.get('error'):
                print(f"❌ ERROR: {error_data.get('message')}")
                return False
        except json.JSONDecodeError:
            # Result is markdown, which is expected
            pass
        
        # Extract structured data from result
        if "<<PAYMENT_PLAN_DATA>>" in result:
            parts = result.split("<<PAYMENT_PLAN_DATA>>")
            markdown_output = parts[0]
            json_data = json.loads(parts[1])
            
            print("📄 PAYMENT PLAN OUTPUT:")
            print("-" * 80)
            print(markdown_output)
            print()
            
            print("=" * 80)
            print("📊 STRUCTURED DATA:")
            print("=" * 80)
            print()
            print(f"Unit ID: {json_data.get('unit_id')}")
            print(f"Compound: {json_data.get('compound')}")
            print(f"Price: {json_data.get('formatted_price')}")
            print(f"Has Discount: {json_data.get('has_discount')}")
            print()
            
            if json_data.get('discount_info'):
                discount = json_data['discount_info']
                print("🎁 DISCOUNT INFORMATION:")
                print(f"   Source: {discount.get('discount_source', 'Unknown')}")
                print(f"   Promo Text: {discount.get('promo_text')}")
                print(f"   Discount %: {discount.get('discount_percentage')}%")
                print(f"   Original Price: {discount.get('formatted_original')}")
                print(f"   Discounted Price: {discount.get('formatted_discounted')}")
                print(f"   You Save: {discount.get('formatted_savings')}")
            else:
                print("ℹ️  No discount available for this unit")
            
            print()
            print("=" * 80)
            print("✅ TEST COMPLETED SUCCESSFULLY")
            print("=" * 80)
            return True
        else:
            print("⚠️  Could not extract structured data from result")
            print(result)
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run tests."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "DISCOUNT DISCOVERY TEST TOOL" + " " * 35 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    # Test with a specific unit ID
    print("Enter a unit ID to test (or press Enter to use default test units):")
    user_input = input("> ").strip()
    
    if user_input:
        # Test user-provided unit ID
        try:
            unit_id = int(user_input)
            test_payment_plan(unit_id)
        except ValueError:
            print("❌ Invalid unit ID. Please enter a number.")
    else:
        # Test with common unit IDs
        print("Testing with sample unit IDs...")
        print()
        
        test_unit_ids = [
            65846980,  # Example from chat history
            # Add more test IDs here based on your database
        ]
        
        for uid in test_unit_ids:
            test_payment_plan(uid)
            print("\n" * 2)
    
    print()
    print("💡 TIP: Check the payment_plan_debug.log file for detailed debug information")
    print()


if __name__ == "__main__":
    main()
