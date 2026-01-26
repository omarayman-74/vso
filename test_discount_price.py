"""Test script for discount price search functionality."""
import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.discount_service import get_unit_price_with_discount, format_price_response


def test_unit_price(unit_id: int):
    """Test price retrieval for a specific unit."""
    print("=" * 80)
    print(f"TESTING DISCOUNT PRICE SEARCH FOR UNIT {unit_id}")
    print("=" * 80)
    print()
    
    # Get price with discount information
    result = get_unit_price_with_discount(unit_id)
    
    # Print raw result
    print("📊 RAW RESULT:")
    print("-" * 80)
    for key, value in result.items():
        if key != 'debug_log':  # Skip debug log in summary
            print(f"  {key}: {value}")
    print()
    
    # Print formatted response
    print("📝 FORMATTED RESPONSE:")
    print("-" * 80)
    formatted = format_price_response(result)
    print(formatted)
    print()
    
    # Print debug log if available
    if result.get('debug_log'):
        print("🔍 DEBUG LOG:")
        print("-" * 80)
        print(result['debug_log'])
        print()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    # Test with multiple unit IDs
    test_units = [
        53198262,  # Unit from previous testing
        65846980,  # Another unit
    ]
    
    # Allow user to specify unit ID via command line
    if len(sys.argv) > 1:
        try:
            test_units = [int(sys.argv[1])]
        except ValueError:
            print("Invalid unit ID provided. Using default test units.")
    
    for unit_id in test_units:
        test_unit_price(unit_id)
        print("\n\n")
