"""
Test script to check Groq API response metadata for token tracking.
"""
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()

print("Testing Groq API token metadata extraction...\n")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3, max_tokens=100)

try:
    response = llm.invoke([HumanMessage(content="Say hello in one word.")])
    
    print("Response content:", response.content)
    print("\n" + "="*50)
    print("RESPONSE ATTRIBUTES:")
    print("="*50)
    
    # Check all attributes
    for attr in dir(response):
        if not attr.startswith('_'):
            try:
                value = getattr(response, attr)
                if not callable(value):
                    print(f"\n{attr}:")
                    print(f"  {value}")
            except:
                pass
    
    print("\n" + "="*50)
    print("TOKEN INFO EXTRACTION:")
    print("="*50)
    
    # Check response_metadata
    if hasattr(response, 'response_metadata'):
        print("\nresponse_metadata found:")
        print(f"  {response.response_metadata}")
        
        metadata = response.response_metadata
        if 'token_usage' in metadata:
            print("\n  token_usage:")
            print(f"    {metadata['token_usage']}")
        if 'usage' in metadata:
            print("\n  usage:")
            print(f"    {metadata['usage']}")
    
    # Check usage_metadata
    if hasattr(response, 'usage_metadata'):
        print("\nusage_metadata found:")
        print(f"  {response.usage_metadata}")
        
        usage = response.usage_metadata
        if usage:
            if hasattr(usage, 'input_tokens'):
                print(f"  input_tokens: {usage.input_tokens}")
            if hasattr(usage, 'output_tokens'):
                print(f"  output_tokens: {usage.output_tokens}")
            if hasattr(usage, 'total_tokens'):
                print(f"  total_tokens: {usage.total_tokens}")
    
except Exception as e:
    print(f"Error: {e}")
