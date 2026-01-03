"""
Integration test for token tracking.
"""
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from token_tracker import get_tracker

load_dotenv()

# Reset tracker for clean test
tracker = get_tracker()
tracker.reset()

print("Testing Token Tracker Integration...\n")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3, max_tokens=100)

# Test 1: Conversation tokens
print("1. Testing conversation token tracking...")
try:
    response = llm.invoke([HumanMessage(content="What is 2+2?")])
    tracker.track_conversation(response, "requirements_gathering")
    print(f"   Response: {response.content}")
    print(f"   ✓ Conversation tokens tracked")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Coding tokens
print("\n2. Testing coding token tracking...")
try:
    response = llm.invoke([HumanMessage(content="Write a hello world function in Python")])
    tracker.track_coding(response, "frontend_implementation")
    print(f"   Response: {response.content[:100]}...")
    print(f"   ✓ Coding tokens tracked")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Print summary
print("\n" + "="*50)
tracker.print_summary()
