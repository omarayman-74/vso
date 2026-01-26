"""
Test script specifically for:
1. SQL logging fix - verify SQL only logged when SQL agent used
2. Chat agent scope restriction - verify refusal of out-of-scope queries
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.chat_service import chat_service

def test_sql_logging_chat_agent():
    """Test that SQL is NOT logged when chat agent is used"""
    print("\n" + "="*60)
    print("TEST: SQL Logging - Chat Agent (Should NOT log SQL)")
    print("="*60)
    
    # Clear log file
    with open("chat_log.txt", "w", encoding="utf-8") as f:
        f.write("")
    
    try:
        # Use chat agent
        result = chat_service.process_message(
            session_id="test_sql_log_1",
            message="Hello, how are you?"
        )
        
        # Read log
        with open("chat_log.txt", "r", encoding="utf-8") as f:
            log_content = f.read()
        
        if "SQL:" in log_content:
            print("FAILED! SQL was logged for chat agent")
            print(f"Log content:\n{log_content}")
            return False
        else:
            print("SUCCESS! SQL was NOT logged for chat agent")
            return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sql_logging_sql_agent():
    """Test that SQL IS logged when SQL agent is used"""
    print("\n" + "="*60)
    print("TEST: SQL Logging - SQL Agent (SHOULD log SQL)")
    print("="*60)
    
    # Clear log file
    with open("chat_log.txt", "w", encoding="utf-8") as f:
        f.write("")
    
    try:
        # Use SQL agent
        result = chat_service.process_message(
            session_id="test_sql_log_2",
            message="Show me apartments with 3 bedrooms"
        )
        
        # Read log
        with open("chat_log.txt", "r", encoding="utf-8") as f:
            log_content = f.read()
        
        if "SQL:" in log_content:
            print("SUCCESS! SQL was logged for SQL agent")
            print(f"SQL found in log")
            return True
        else:
            print("FAILED! SQL was NOT logged for SQL agent")
            print(f"Log content:\n{log_content}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_agent_in_scope():
    """Test that chat agent responds to real estate questions"""
    print("\n" + "="*60)
    print("TEST: Chat Agent In-Scope (Should respond)")
    print("="*60)
    
    try:
        queries = [
            "Hello",
            "Thank you for your help",
            "What services do you provide?",
            "Tell me about buying property"
        ]
        
        for query in queries:
            print(f"\nQuery: {query}")
            result = chat_service.process_message(
                session_id="test_chat_scope_in",
                message=query
            )
            
            response = result['response'].lower()
            # Should NOT contain the refusal message
            if "can only assist with real estate" in response:
                print(f"FAILED! Refused in-scope query: {query}")
                print(f"Response: {result['response']}")
                return False
            else:
                print(f"SUCCESS! Responded to: {query}")
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_agent_out_of_scope():
    """Test that chat agent refuses non-real-estate questions"""
    print("\n" + "="*60)
    print("TEST: Chat Agent Out-of-Scope (Should refuse)")
    print("="*60)
    
    try:
        queries = [
            "What is the weather today?",
            "How do I cook pasta?",
            "Who won the football match?",
            "Tell me about quantum physics"
        ]
        
        refused_count = 0
        for query in queries:
            print(f"\nQuery: {query}")
            result = chat_service.process_message(
                session_id="test_chat_scope_out",
                message=query
            )
            
            response = result['response'].lower()
            # Should contain the refusal message
            if "can only assist with real estate" in response or "only answer" in response:
                print(f"SUCCESS! Refused out-of-scope query")
                print(f"Response: {result['response'][:100]}...")
                refused_count += 1
            else:
                print(f"WARNING: May have answered out-of-scope query")
                print(f"Response: {result['response'][:150]}...")
        
        # At least 75% should be refused
        if refused_count >= len(queries) * 0.75:
            print(f"\nSUCCESS! Refused {refused_count}/{len(queries)} out-of-scope queries")
            return True
        else:
            print(f"\nFAILED! Only refused {refused_count}/{len(queries)} out-of-scope queries")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# SQL LOGGING & CHAT SCOPE TESTS")
    print("#"*60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Run tests
    tests = [
        ("SQL Logging - Chat Agent (No SQL)", test_sql_logging_chat_agent),
        ("SQL Logging - SQL Agent (Has SQL)", test_sql_logging_sql_agent),
        ("Chat Agent In-Scope", test_chat_agent_in_scope),
        ("Chat Agent Out-of-Scope", test_chat_agent_out_of_scope)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'*'*60}")
        print(f"Running: {test_name}")
        print('*'*60)
        
        if test_func():
            tests_passed += 1
        else:
            tests_failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests Passed: {tests_passed}/{len(tests)}")
    print(f"Tests Failed: {tests_failed}/{len(tests)}")
    print("="*60)
    
    if tests_failed == 0:
        print("\n*** ALL TESTS PASSED! ***")
    else:
        print(f"\nWARNING: {tests_failed} test(s) failed")
