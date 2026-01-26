import sys
import os

# Ensure root is in path
sys.path.append(os.getcwd())

from services.agent_service import create_agent, SessionMemory

def main():
    print("Testing agent initialization and simple invocation...")
    try:
        session_memory = SessionMemory()
        # This will fail if create_agent hits import errors or definition errors
        agent_executor = create_agent(session_memory)
        print("Agent created successfully.")
        
        # Test a query that should trigger the pre-processor bypass
        query = "What are the payment plans for unit 12345?"
        print(f"Testing invoke with: {query}")
        
        # We need to ensure session_memory has the required structure if we mock it, 
        # but create_agent accepts an instance.
        
        response = agent_executor.invoke({
            "input": query,
            "chat_history": []
        })
        print("Invoked successfully.")
        output = response.get("output", "No output")
        print(f"Response start: {output[:100]}...") 
 
        
        # We can't easily see internal tool calls here without verbose logs, 
        # but success implies the graph didn't crash.

        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
