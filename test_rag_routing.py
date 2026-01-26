
import sys
import os

# Fix Windows terminal encoding for emoji support
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.chat_service import chat_service

def test_rag_routing():
    """Test that RAG routing works correctly for general knowledge queries."""
    
    print("="*70)
    print("Testing RAG Routing Fix")
    print("="*70)
    
    # Test 1: General knowledge query about TMG
    print("\n📝 Test 1: General Knowledge Query")
    print("Query: 'who is the owner of TMG'")
    print("-" * 70)
    
    session_id = "test_rag_routing"
    query = "who is the owner of TMG"
    
    result = chat_service.process_message(session_id, query)
    response = result['response']
    
    print(f"\nResponse:\n{response}\n")
    
    # Check if RAG was used (response should contain information, not "no properties")
    if "no available properties" in response.lower() or "no properties listed" in response.lower():
        print("❌ FAILED: Query was routed to SQL instead of RAG")
        print("   The response indicates it searched for properties instead of answering from knowledge base")
    elif len(response) > 50:  # RAG responses should have substantial content
        print("✅ PASSED: Query appears to have been routed to RAG")
        print("   Response contains substantial information from knowledge base")
    else:
        print("⚠️  UNCERTAIN: Response is too short to determine routing")
    
    # Test 2: Property search query (should use SQL)
    print("\n" + "="*70)
    print("📝 Test 2: Property Search Query")
    print("Query: 'show me 3-bedroom apartments'")
    print("-" * 70)
    
    session_id2 = "test_sql_routing"
    query2 = "show me 3-bedroom apartments"
    
    result2 = chat_service.process_message(session_id2, query2)
    response2 = result2['response']
    
    print(f"\nResponse preview: {response2[:200]}...")
    
    if "<<PROPERTY_CAROUSEL_DATA>>" in response2 or "properties" in response2.lower():
        print("\n✅ PASSED: Property search routed to SQL correctly")
    else:
        print("\n❌ FAILED: Property search not routed correctly")
    
    print("\n" + "="*70)
    print("Test Complete - Check chat_log.txt for detailed tool usage")
    print("="*70)

if __name__ == "__main__":
    test_rag_routing()
