"""Simple test to verify discount price tool integration."""
import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.agent_service import get_unit_price_with_discount


def test_tool_integration():
    """Test that the tool is properly registered and works."""
    print("=" * 80)
    print("TESTING DISCOUNT PRICE TOOL INTEGRATION")
    print("=" * 80)
    print()
    
    unit_id = 53198262
    
    print(f"📞 Calling get_unit_price_with_discount({unit_id})...")
    print()
    
    try:
        result = get_unit_price_with_discount.invoke({'unit_id': unit_id})
        
        print("✅ TOOL CALL SUCCESSFUL!")
        print("=" * 80)
        print(result)
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_tool_integration()
