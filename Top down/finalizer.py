import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

# Load environment variables from .env file
load_dotenv()

# Global variables to store finalized requirements
finalized_requirements = {
    "detailed_description": None,
    "features": None,
    "is_finalized": False
}

# Define the finalize tool for requirements
@tool
def finalize(detailed_description: str, features: list) -> str:
    """Use this function to pass requirements and features to dev team.
    
    Args:
        detailed_description: Detailed description of the application
        features: List of features required in the application
    """
    global finalized_requirements
    
    # Store the requirements in the global variable
    finalized_requirements["detailed_description"] = detailed_description
    finalized_requirements["features"] = features
    finalized_requirements["is_finalized"] = True
    
    print("finalize called:", detailed_description, features)
    result = {
        "status": "Requirements finalized and sent to dev team",
        "detailed_description": detailed_description,
        "features": features
    }
    return json.dumps(result, indent=2)
# List of tools for the requirements agent
tools = [finalize]
# System prompt for the requirements analyst agent
REQUIREMENTS_ANALYST_PROMPT = """You are a requirements analyst who tries to understand the user's application and the features it requires. 

Your job is to:
1. Ask clarifying questions about the application
2. Understand the key features and requirements
3. Summarize what you've understood
4. Confirm with the user that you have the complete picture
5. Once you both agree on the detailed description and all features, ONLY call the 'finalize' tool - do not add any text before or after the function call. Do this only after user has agreed to your summary.

IMPORTANT: When calling the finalize tool, do NOT include any conversational text in your response. Just call the function directly.

Be thorough, ask specific questions, and make sure you capture all important details before finalizing."""
# Initialize the Groq LLM for requirements agent
agent_requirements = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.6,
    max_tokens=8192
)
# Bind tools to the agent
agent_requirements_with_tools = agent_requirements.bind_tools(tools)
# Initialize conversation history for requirements agent
requirements_conversation_history = []
# Add system prompt as the first message
requirements_conversation_history.append(SystemMessage(content=REQUIREMENTS_ANALYST_PROMPT))
# Function for requirements agent interaction
def agent_requirements_chat(user_input):
    """Chat with the requirements analyst agent."""
    # Add user message to history
    requirements_conversation_history.append(HumanMessage(content=user_input))
    # Get response from agent with tools
    try:
        response = agent_requirements_with_tools.invoke(requirements_conversation_history)
    except Exception as e:
        # If tool calling failed, retry with emphasis on proper tool usage
        if "tool_use_failed" in str(e) or "Failed to call a function" in str(e):
            print("\n[System: Tool call failed, retrying with emphasis...]")
            
            # Add emphasis message to history
            emphasis_message = SystemMessage(content="""IMPORTANT REMINDER: 
- ONLY call the 'finalize' tool if the user has explicitly agreed to finalize the requirements
- Do NOT call the tool while still discussing or asking questions
- The tool should ONLY be called after user confirmation
- If you're still gathering information, just respond conversationally without calling any tools""")
            
            requirements_conversation_history.append(emphasis_message)
            
            # Retry the call
            response = agent_requirements_with_tools.invoke(requirements_conversation_history)
            
            # Remove the emphasis message from history to avoid cluttering
            requirements_conversation_history.pop()
        else:
            # Re-raise if it's a different error
            raise e

    # Add AI response to history
    requirements_conversation_history.append(response)
    # Check if the response contains tool calls (finalize)
    if hasattr(response, 'tool_calls') and response.tool_calls:
        # Execute tool calls
        for tool_call in response.tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            
            # Execute the finalize tool
            if tool_name == 'finalize':
                # Ignore if arguments are empty or invalid
                detailed_desc = tool_args.get('detailed_description', '')
                features = tool_args.get('features', [])
                
                if ( detailed_desc=="" or detailed_desc=="N/A") or not features:
                    print("\n[System: Tool call ignored - missing required information]")
                    continue  # Ignore the tool call if arguments are empty
                
                result = finalize.invoke(tool_args)
                print("\n" + "="*50)
                print("REQUIREMENTS FINALIZED!")
                print("="*50)
                print(result)
                print("="*50)
                return result, True  # Return result and finalized flag
            else:
                result = f"Unknown tool: {tool_name}"
    
    return response.content, False

# Interactive conversation loop with the requirements agent
def run_requirements_agent():
    """Run an interactive session with the requirements analyst agent."""
    print("="*50)
    print("REQUIREMENTS ANALYST AGENT")
    print("="*50)
    print("Hello! I'm your requirements analyst. I'll help you define your application requirements.")
    print("Type 'quit' or 'exit' to end the conversation.\n")
    # Initial greeting from agent
    initial_response, _ = agent_requirements_chat("Hello, I'd like to discuss my application idea.")
    print(f"Agent: {initial_response}\n")
    finalized = False
    while 1:
        # Get user input
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\nAgent: Goodbye! Feel free to come back when you're ready to finalize the requirements.")
            break
        if not user_input:
            continue
        # Get agent response
        response, finalized = agent_requirements_chat(user_input)
        if not finalized:
            print(f"\nAgent: {response}\n")
        else:
            # Requirements have been finalized
            print("\nThe requirements gathering session has ended. Your requirements have been sent to the dev team!")
            break

# Run the agent
if __name__ == "__main__":
    run_requirements_agent()
