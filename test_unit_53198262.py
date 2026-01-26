"""Quick test for unit 53198262 discount discovery"""
import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.agent_service import _get_payment_plan_impl
import json

print("=" * 80)
print("TESTING PAYMENT PLAN FOR UNIT 53198262")
print("=" * 80)
print()

result = _get_payment_plan_impl(53198262)

# Try to extract structured data
if "<<PAYMENT_PLAN_DATA>>" in result:
    parts = result.split("<<PAYMENT_PLAN_DATA>>")
    markdown = parts[0]
    data = json.loads(parts[1])
    
    print("📄 MARKDOWN OUTPUT:")
    print(markdown)
    print()
    print("=" * 80)
    print("📊 STRUCTURED DATA:")
    print(json.dumps(data, indent=2))
else:
    print(result)

print()
print("Check payment_plan_debug.log for detailed debug information")
