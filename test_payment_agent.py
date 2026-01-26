import os
import sys

# Ensure root is in path
sys.path.append(os.getcwd())

from services.agent_service import create_agent, SessionMemory

def main():
    print("Initializing Agent...")
    try:
        session_memory = SessionMemory()
        agent_executor = create_agent(session_memory)
        print("Agent initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        return

    # Sample queries to test
    test_queries = [
        "What is the payment plan for unit 12345?",
        "Tell me about financing options for unit #999"
    ]

    print("\nRunning specific test queries...")
    for query in test_queries:
        print(f"\nContext: Identifying unit from query '{query}'")
        try:
            print(f"User Query: {query}")
            response = agent_executor.invoke({
                "input": query, 
                "chat_history": session_memory.chat_history
            })
            print("\nAgent Response:")
            print(response["output"])
            
            # Update history
            session_memory.chat_history.append(("human", query))
            session_memory.chat_history.append(("ai", response["output"]))
            
        except Exception as e:
            print(f"Error running query: {e}")

    print("\nTest Complete. You can now try running the main application.")

if __name__ == "__main__":
    main()
