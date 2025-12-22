"""
Standalone File Agent - Uses MCP server to read, write, and edit files based on prompts.
This is a testing tool for file operations.
"""

import os
import asyncio
import subprocess
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json

load_dotenv()


class FileAgent:
    """Agent that can read, write, and edit files using MCP tools."""
    
    def __init__(self, workspace_path: str):
        """
        Initialize the file agent.
        
        Args:
            workspace_path: Root path for file operations
        """
        self.workspace_path = workspace_path
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, max_tokens=4000)
        self.conversation_history = []
    
    def _quote_path_if_needed(self, path: str) -> str:
        """
        Quote EACH folder in path that contains whitespace with single quotes.
        Only adds quotes if not already quoted.
        Examples:
          C:\\My Folder -> C:\\'My Folder'
          C:\\'My Folder' -> C:\\'My Folder' (unchanged)
          C:\\My Folder\\Sub Folder -> C:\\'My Folder'\\'Sub Folder'
        
        Args:
            path: The path to potentially quote
            
        Returns:
            str: Path with EACH component containing whitespace wrapped in single quotes
        """
        # Handle empty path
        if not path:
            return path
            
        # Check if path separators exist (Windows or Unix)
        if '\\' in path or '/' in path:
            separator = '\\' if '\\' in path else '/'
            parts = path.split(separator)
            
            # Quote EACH part that contains whitespace individually (if not already quoted)
            quoted_parts = []
            for part in parts:
                if not part:  # Empty part (e.g., from leading separator)
                    quoted_parts.append(part)
                elif ' ' in part:  # Has whitespace - check if needs quoting
                    # Check if ALREADY enclosed in single quotes
                    if part.startswith("'") and part.endswith("'") and len(part) > 2:
                        # Already quoted, keep as is
                        quoted_parts.append(part)
                    else:
                        # Not quoted, add quotes
                        quoted_parts.append(f"'{part}'")
                else:
                    # No whitespace, no quotes needed
                    quoted_parts.append(part)
            
            return separator.join(quoted_parts)
        else:
            # No path separator, just a single name with potential whitespace
            if ' ' in path:
                # Check if already quoted
                if path.startswith("'") and path.endswith("'") and len(path) > 2:
                    return path  # Already quoted
                else:
                    return f"'{path}'"  # Add quotes
        
        return path
    
    def _process_command_paths(self, command: str) -> str:
        """
        Process a command and quote any paths with whitespace (each folder individually).
        This is ONLY for terminal commands - MCP tools should NOT use quotes.
        
        Args:
            command: The terminal command to process
            
        Returns:
            str: Command with paths properly quoted (each folder with whitespace quoted)
        """
        # Handle cd commands specially
        if command.strip().startswith('cd '):
            parts = command.split('cd ', 1)
            if len(parts) == 2:
                path = parts[1].strip()
                # Remove any existing quotes first
                path = path.strip('"').strip("'")
                return f'cd {self._quote_path_if_needed(path)}'
        
        # Handle common file operations - look for paths in the command
        # Try to find and quote any path that looks like it might have whitespace
        import re
        
        # Pattern to match potential file paths (with or without quotes)
        # This will match things like: C:\My Folder\file.txt or /path/to/folder
        path_pattern = r'[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*|(?:/[^/:*?"<>|\r\n]+)+'
        
        def quote_match(match):
            path = match.group(0)
            # Check if this path contains whitespace
            if ' ' in path:
                return self._quote_path_if_needed(path)
            return path
        
        # Replace all paths that contain whitespace
        processed = re.sub(path_pattern, quote_match, command)
        
        # Also handle workspace_path specifically if it appears
        if self.workspace_path in command and ' ' in self.workspace_path:
            # Remove any quotes around workspace_path first
            clean_workspace = self.workspace_path.strip('"').strip("'")
            quoted_workspace = self._quote_path_if_needed(clean_workspace)
            processed = processed.replace(self.workspace_path, quoted_workspace)
        
        return processed
        
    async def execute_task(self, prompt: str, max_iterations: int = 15) -> dict:
        """
        Execute a file operation task based on a prompt.
        
        Args:
            prompt: Natural language description of what to do
            max_iterations: Maximum number of tool calls before stopping
            
        Returns:
            dict: Contains success status, actions taken, and final output
        """
        print("="*80)
        print("FILE AGENT TASK")
        print("="*80)
        print(f"Workspace: {self.workspace_path}")
        print(f"Task: {prompt}")
        print("="*80)
        
        # Initialize MCP session
        server_params = StdioServerParameters(
            command="node",
            args=[
                r"C:\Users\ASUS\Desktop\Codes\POME\Top down\MCPServer\mcp-edit-file-lines\build\index.js",
                self.workspace_path
            ]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✓ MCP Server connected\n")
                
                # Initialize conversation and error tracking
                self.conversation_history = []
                error_history = []  # Track all errors with commands and reasoning
                user_response = None  # Store information to return to user
                
                initial_prompt = f"""You are a file operations agent with access to MCP tools, you have to perform a set of tasks to get your users requirements satisfied.

Workspace: {self.workspace_path}

Task: {prompt}
For TERMINAL COMMANDS: Each folder with whitespace will be automatically quoted individually
  Example: C:\\My Folder\\Sub Folder\\file.txt becomes C:\\'My Folder'\\'Sub Folder'\\file.txt
- For MCP TOOLS: Always use paths WITHOUT any quotes (normal paths)
  Example: C:\\My Folder\\file.txt (no quotes needed)
- The system handles quoting automatically for terminal commands only
3. get_file_lines - Get specific line numbers with context
4. read_file - Read entire file or specific line range
5. write_file - Overwrite existing file content (ONLY works on existing files)
6. run_terminal - Execute terminal/shell commands (PowerShell on Windows)

IMPORTANT FILE CREATION RULE:
- The MCP tools CANNOT create new files
- To create a new file, use run_terminal with: echo "" > filename
- After the file is created, you can then use edit_file_lines or write_file on it
- If you encounter "ENOENT: no such file or directory" error, create the file first with run_terminal

IMPORTANT PATH HANDLING:
- Paths with whitespace will be automatically quoted when used in terminal commands
- However, you can also quote paths explicitly if needed
- Example: cd "C:\\My Folder" or cd C:\\My Folder (both work)
- For other tools (MCP), use paths without quotes

Your workflow:
1. Understand the task requirements
2. Use appropriate tools to accomplish the task
3. For NEW files: Use run_terminal with echo "" > filename to create it first
4. For edits: First search/read to understand context, then edit
5. For writes: Only write to existing files (or create them first with run_terminal)
6. For information queries: Use read_file or search_file to get the information
7. Verify changes if needed
8. Decide when the task is complete

For each response, use this format:

REASONING: <explain your thinking>
ACTION: <SEARCH_FILE | EDIT_FILE | GET_LINES | READ_FILE | WRITE_FILE | RUN_TERMINAL | DONE>
TOOL_CALL: <if ACTION is not DONE, provide the tool call in JSON format>
ANSWER: <if user asked for information, provide the answer here. Only include this when completing a query task>

IMPORTANT:
- When user asks "what is/are", "show me", "get contents", etc., they want INFORMATION
- After reading/searching to get the information, provide it in the ANSWER field
- Then set ACTION: DONE

Example TOOL_CALL formats:
{{"tool": "search_file", "path": "path/to/file.py", "pattern": "import", "type": "text", "caseSensitive": false, "contextLines": 3, "maxMatches": 10}}
{{"tool": "edit_file_lines", "path": "path/to/file.py", "edits": [{{"startLine": 10, "endLine": 12, "content": "new code here"}}]}}
{{"tool": "get_file_lines", "path": "path/to/file.py", "lineNumbers": [1, 2, 3], "context": 2}}
{{"tool": "read_file", "path": "path/to/file.py", "startLine": 1, "endLine": 50}}
{{"tool": "write_file", "path": "path/to/newfile.py", "content": "file content here"}}
{{"tool": "run_terminal", "command": "echo \\"\\" > newfile.txt"}}
{{"tool": "run_terminal", "command": "dir"}}
{{"tool": "run_terminal", "command": "python --version"}}

Terminal command examples:
- Create file: echo "" > filename.txt
- List files: dir (Windows) or ls (Linux/Mac)
- Check file exists: Test-Path filename.txt
- Run Python: python script.py
- Install package: pip install package_name

Start by analyzing the task and taking your first action."""

                self.conversation_history.append({"role": "user", "content": initial_prompt})
                
                iteration = 0
                all_actions = []
                
                while iteration < max_iterations:
                    iteration += 1
                    print(f"\n{'='*80}")
                    print(f"Iteration {iteration}/{max_iterations}")
                    print(f"{'='*80}")
                    
                    # Get LLM response
                    messages = []
                    for msg in self.conversation_history:
                        if msg["role"] == "user":
                            messages.append(HumanMessage(content=msg["content"]))
                        else:
                            messages.append(AIMessage(content=msg["content"]))
                    
                    response = self.llm.invoke(messages)
                    response_text = response.content.strip()
                    self.conversation_history.append({"role": "assistant", "content": response_text})
                    print(response_text)
                    # Parse the response
                    action = None
                    reasoning = ""
                    tool_call_json = None
                    
                    # Extract ACTION
                    if 'ACTION:' in response_text:
                        action_line = response_text.split('ACTION:')[1].split('\n')[0].strip()
                        action = action_line.upper()
                        # print(f"Action: {action}")
                    
                    # Extract REASONING
                    if 'REASONING:' in response_text:
                        reasoning_start = response_text.find('REASONING:') + len('REASONING:')
                        reasoning_end = response_text.find('ACTION:') if 'ACTION:' in response_text else len(response_text)
                        reasoning = response_text[reasoning_start:reasoning_end].strip()
                        # print(f"Reasoning: {reasoning[:200]}{'...' if len(reasoning) > 200 else ''}")
                    
                    # Extract ANSWER if provided
                    if 'ANSWER:' in response_text:
                        answer_start = response_text.find('ANSWER:') + len('ANSWER:')
                        # Get everything after ANSWER: (could be at the end)
                        answer_text = response_text[answer_start:].strip()
                        # Stop at next known field if any
                        for field in ['REASONING:', 'ACTION:', 'TOOL_CALL:']:
                            if field in answer_text:
                                answer_text = answer_text[:answer_text.find(field)].strip()
                                break
                        if answer_text:
                            user_response = answer_text
                    
                    # Check if done
                    if action == 'DONE' or 'DONE' in str(action):
                        print(f"\n{'='*80}")
                        print("✓ TASK COMPLETED")
                        print(f"{'='*80}")
                        print(f"Total iterations: {iteration}")
                        print(f"Actions taken: {len(all_actions)}")
                        
                        # Display answer if it's an information request
                        if user_response:
                            print(f"\n{'='*80}")
                            print("ANSWER")
                            print(f"{'='*80}")
                            print(user_response)
                            print(f"{'='*80}")
                        
                        return {
                            'success': True,
                            'output': reasoning,
                            'answer': user_response,  # Include answer in return
                            'iterations': iteration,
                            'actions': all_actions
                        }
                    
                    # Extract TOOL_CALL
                    if 'TOOL_CALL:' in response_text:
                        tool_call_start = response_text.find('TOOL_CALL:') + len('TOOL_CALL:')
                        tool_call_str = response_text[tool_call_start:].strip()
                        
                        # Try to extract JSON
                        try:
                            if '{' in tool_call_str and '}' in tool_call_str:
                                json_start = tool_call_str.find('{')
                                json_end = tool_call_str.rfind('}') + 1
                                tool_call_json = json.loads(tool_call_str[json_start:json_end])
                        except Exception as e:
                            print(f"✗ Could not parse tool call: {str(e)}")
                            self.conversation_history.append({
                                "role": "user",
                                "content": f"Error parsing your tool call. Please provide valid JSON. Error: {str(e)}"
                            })
                            continue
                    
                    if not tool_call_json:
                        print(f"✗ No valid tool call found")
                        self.conversation_history.append({
                            "role": "user",
                            "content": "No valid tool call found. Please provide a TOOL_CALL in JSON format."
                        })
                        continue
                    
                    # Execute the tool call
                    tool_name = tool_call_json.get('tool')
                    print(f"Executing tool: {tool_name}")
                    
                    tool_result = None
                    try:
                        if tool_name == 'search_file':
                            mcp_result = await session.call_tool('search_file', {
                                'path': tool_call_json['path'],
                                'pattern': tool_call_json['pattern'],
                                'type': tool_call_json.get('type', 'text'),
                                'caseSensitive': tool_call_json.get('caseSensitive', False),
                                'contextLines': tool_call_json.get('contextLines', 3),
                                'maxMatches': tool_call_json.get('maxMatches', 10)
                            })
                            tool_result = mcp_result.content[0].text if mcp_result.content else str(mcp_result)
                            
                        elif tool_name == 'edit_file_lines':
                            mcp_result = await session.call_tool('edit_file_lines', {
                                'p': tool_call_json['path'],
                                'e': tool_call_json['edits'],
                                'dryRun': False
                            })
                            tool_result = mcp_result.content[0].text if mcp_result.content else str(mcp_result)
                            if 'Error:' not in tool_result:
                                num_edits = len(tool_call_json['edits'])
                                tool_result = f"✓ EDIT SUCCESSFUL: Applied {num_edits} edit(s) to {tool_call_json['path']}\n\n{tool_result}"
                            
                        elif tool_name == 'get_file_lines':
                            mcp_result = await session.call_tool('get_file_lines', {
                                'path': tool_call_json['path'],
                                'lineNumbers': tool_call_json['lineNumbers'],
                                'context': tool_call_json.get('context', 2)
                            })
                            tool_result = mcp_result.content[0].text if mcp_result.content else str(mcp_result)
                            
                        elif tool_name == 'read_file':
                            # Read file by checking actual line count first
                            path = tool_call_json['path']
                            full_path = os.path.join(self.workspace_path, path) if not os.path.isabs(path) else path
                            
                            try:
                                # Count actual lines in the file
                                with open(full_path, 'r', encoding='utf-8') as f:
                                    actual_lines = len(f.readlines())
                                
                                if actual_lines == 0:
                                    tool_result = f"File '{path}' is empty (0 lines)"
                                else:
                                    # Read only the lines that exist
                                    start = tool_call_json.get('startLine', 1)
                                    end = min(tool_call_json.get('endLine', actual_lines), actual_lines)
                                    
                                    # Ensure we don't request more lines than exist
                                    line_numbers = list(range(start, end + 1))
                                    
                                    mcp_result = await session.call_tool('get_file_lines', {
                                        'path': path,
                                        'lineNumbers': line_numbers,
                                        'context': 0
                                    })
                                    tool_result = mcp_result.content[0].text if mcp_result.content else str(mcp_result)
                                    tool_result = f"File '{path}' ({actual_lines} lines):\n{tool_result}"
                            except FileNotFoundError:
                                tool_result = f"Error: File not found: {path}"
                            except Exception as e:
                                tool_result = f"Error reading file: {str(e)}"
                            
                        elif tool_name == 'write_file':
                            # Write by editing from line 1 to end
                            content = tool_call_json['content']
                            path = tool_call_json['path']
                            
                            # Check if file exists
                            full_path = os.path.join(self.workspace_path, path) if not os.path.isabs(path) else path
                            
                            if os.path.exists(full_path):
                                # Count existing lines
                                with open(full_path, 'r', encoding='utf-8') as f:
                                    existing_lines = len(f.readlines())
                                # Replace all content
                                mcp_result = await session.call_tool('edit_file_lines', {
                                    'p': path,
                                    'e': [{'startLine': 1, 'endLine': existing_lines, 'content': content}],
                                    'dryRun': False
                                })
                            else:
                                # Create new file by writing to line 1
                                mcp_result = await session.call_tool('edit_file_lines', {
                                    'p': path,
                                    'e': [{'startLine': 1, 'endLine': 1, 'content': content}],
                                    'dryRun': False
                                })
                            
                            tool_result = mcp_result.content[0].text if mcp_result.content else str(mcp_result)
                            if 'Error:' not in tool_result:
                                tool_result = f"✓ FILE WRITTEN: {path}\n\n{tool_result}"
                        
                        elif tool_name == 'run_terminal':
                            # Execute terminal command
                            command = tool_call_json['command']
                            #EACH folder with whitespace individually
                            # This ensures proper handling of paths like: C:\My Folder\Another Folder\file.txt
                            # Process command to quote paths with whitespace
                            processed_command = self._process_command_paths(command)
                            
                            if processed_command != command:
                                print(f"  Original: {command}")
                                print(f"  Processed: {processed_command}")
                            
                            print(f"RUNNING TERMINAL COMMAND: {processed_command}")
                            
                            try:
                                result = subprocess.run(
                                    processed_command,
                                    shell=True,
                                    cwd=self.workspace_path,
                                    capture_output=True,
                                    text=True,
                                    timeout=30
                                )
                                
                                output = result.stdout if result.stdout else result.stderr
                                if not output:
                                    output = f"Command executed with exit code {result.returncode}"
                                
                                if result.returncode == 0:
                                    tool_result = f"✓ COMMAND SUCCESS:\nCommand: {processed_command}\nOutput:\n{output}"
                                else:
                                    tool_result = f"✗ COMMAND FAILED (exit code {result.returncode}):\nCommand: {processed_command}\nOutput:\n{output}"
                            
                            except subprocess.TimeoutExpired:
                                tool_result = f"Error: Command timed out after 30 seconds: {processed_command}"
                            except Exception as e:
                                tool_result = f"Error: Failed to execute command: {str(e)}"
                        
                        else:
                            tool_result = f"Unknown tool: {tool_name}"
                        
                        print(f"Tool result (first 300 chars):\n{tool_result}\n")
                        
                        # Check if error occurred
                        has_error = 'Error:' in tool_result or 'error' in tool_result.lower()
                        
                        # Generate short reasoning summary for history
                        reasoning_summary = reasoning.split('.')[0] if '.' in reasoning else reasoning[:100]
                        reasoning_summary = reasoning_summary.strip() + '...' if len(reasoning) > len(reasoning_summary) else reasoning_summary
                        
                        # Track action with full details
                        action_record = {
                            'iteration': iteration,
                            'action': action,
                            'tool': tool_name,
                            'command': json.dumps(tool_call_json),
                            'reasoning': reasoning_summary,  # Short summary instead of full reasoning
                            'result': tool_result[:500],
                            'success': not has_error
                        }
                        all_actions.append(action_record)
                        
                        # Track errors separately with full context
                        if has_error:
                            error_record = {
                                'iteration': iteration,
                                'command': json.dumps(tool_call_json),
                                'error': tool_result,
                                'reasoning': reasoning_summary  # Short summary instead of full reasoning
                            }
                            error_history.append(error_record)
                            print(f"⚠ Error recorded (total errors: {len(error_history)})")
                        
                        # Build error context for next prompt
                        error_context = ""
                        if error_history:
                            error_context = "\n\nPREVIOUS ERRORS ENCOUNTERED:\n"
                            for i, err in enumerate(error_history[-3:], 1):  # Show last 3 errors
                                error_context += f"\nError {err['iteration']}:\n"
                                error_context += f"  Command: {err['command']}\n"
                                error_context += f"  Reasoning: {err['reasoning']}\n"  # Already summarized
                                error_context += f"  Error: {err['error'][:200]}...\n"
                            error_context += "\n⚠ AVOID repeating these exact same commands that failed!\n"
                        
                        # Add result to conversation with error context
                        next_instruction = "What's your next action? Use the format with ACTION, REASONING, and TOOL_CALL (or ACTION: DONE if finished)."
                        
                        self.conversation_history.append({
                            "role": "user",
                            "content": f"Tool result:\n{tool_result}{error_context}\n\n{next_instruction}"
                        })
                        
                    except Exception as e:
                        error_msg = f"Error executing tool: {str(e)}"
                        print(f"✗ {error_msg}")
                        
                        # Generate short reasoning summary
                        reasoning_summary = reasoning.split('.')[0] if '.' in reasoning and reasoning else reasoning[:100] if reasoning else 'N/A'
                        reasoning_summary = reasoning_summary.strip() + '...' if reasoning and len(reasoning) > len(reasoning_summary) else reasoning_summary
                        
                        # Track exception as error
                        error_record = {
                            'iteration': iteration,
                            'command': json.dumps(tool_call_json) if tool_call_json else 'N/A',
                            'error': error_msg,
                            'reasoning': reasoning_summary
                        }
                        error_history.append(error_record)
                        all_actions.append({
                            'iteration': iteration,
                            'action': action,
                            'tool': tool_name,
                            'command': json.dumps(tool_call_json) if tool_call_json else 'N/A',
                            'reasoning': reasoning_summary,
                            'result': error_msg,
                            'success': False
                        })
                        
                        # Build error context
                        error_context = "\n\nPREVIOUS ERRORS:\n"
                        for err in error_history[-3:]:
                            error_context += f"  Iteration {err['iteration']}: {err['error'][:150]}...\n"
                        
                        self.conversation_history.append({
                            "role": "user",
                            "content": f"{error_msg}{error_context}\n\nPlease try again or choose a different approach."
                        })
                
                # Max iterations reached
                print(f"\n{'='*80}")
                print(f"⚠ REACHED MAX ITERATIONS ({max_iterations})")
                print(f"{'='*80}")
                return {
                    'success': False,
                    'output': 'Max iterations reached without completion',
                    'iterations': iteration,
                    'actions': all_actions
                }


async def main():
    """Main function to run the file agent."""
    print("\n" + "="*80)
    print("FILE AGENT - Interactive Mode")
    print("="*80)
    print("This agent can read, write, and edit files using natural language prompts.")
    print("Type 'exit' or 'quit' to stop.")
    print("="*80 + "\n")
    
    workspace_path = os.path.dirname(__file__)
    agent = FileAgent(workspace_path)
    
    while True:
        try:
            prompt = input("\nEnter your task (or 'exit' to quit): ").strip()
            
            if prompt.lower() in ['exit', 'quit', 'q']:
                print("\nExiting file agent...")
                break
            
            if not prompt:
                print("Please enter a valid task.")
                continue
            
            # Execute the task
            result = await agent.execute_task(prompt)
            
            # Display summary
            print("\n" + "="*80)
            print("TASK SUMMARY")
            print("="*80)
            print(f"Status: {'✓ Success' if result['success'] else '✗ Failed'}")
            print(f"Iterations: {result['iterations']}")
            print(f"Actions taken: {len(result['actions'])}")
            
            if result['actions']:
                print("\nActions:")
                for i, action in enumerate(result['actions'], 1):
                    status = "✓" if action['success'] else "✗"
                    print(f"  {status} {i}. {action['tool']}: {action['reasoning'][:80]}...")
                    if not action['success']:
                        print(f"      Error: {action['result'][:100]}...")
            
            print("="*80)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"\n✗ Error: {str(e)}")
            continue


if __name__ == "__main__":
    # Example usage - can be run with a direct prompt or interactively
    import sys
    
    if len(sys.argv) > 1:
        # Run with command line argument
        workspace = os.path.dirname(__file__)
        agent = FileAgent(workspace)
        task = ' '.join(sys.argv[1:])
        result = asyncio.run(agent.execute_task(task))
        
        print(f"\n{'='*80}")
        print("FINAL RESULT")
        print(f"{'='*80}")
        print(f"Success: {result['success']}")
        print(f"Iterations: {result['iterations']}")
        if result.get('answer'):
            print(f"\nAnswer:\n{result['answer']}")
        else:
            print(f"Output: {result['output']}")
    else:
        # Run interactively
        asyncio.run(main())
