"""
Debugging agents that run and test the generated projects.
One agent for frontend, one for backend - they identify and fix issues.
"""

import os
import time
import subprocess
import json
import re
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client

load_dotenv()


class ProjectDebugger:
    """Base class for project debugging agents."""
    
    def __init__(self, project_path: str, project_type: str, agent_id: str):
        self.project_path = project_path
        self.project_type = project_type
        self.agent_id = agent_id
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, max_tokens=8000)
        
        # Setup logging
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(logs_dir, f"{project_type}_debugger_{timestamp}.log")
        
        self.process = None
        self.errors_found = []
        self.fixes_applied = []
        # self.wcgw_transport = None
        # self.wcgw_client = None
        # self.wcgw_session = None
    
    def log_print(self, msg: str):
        """Log to file and print to console."""
        print(msg)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    
    def start_project(self) -> Optional[subprocess.Popen]:
        """Start the project process. Override in subclasses."""
        raise NotImplementedError
    
    def check_errors(self) -> List[Dict[str, Any]]:
        """Check for errors in the running project. Override in subclasses."""
        raise NotImplementedError
    
    async def fix_error(self, error: Dict[str, Any]) -> bool:
        """Use LLM to fix an error. Override in subclasses."""
        raise NotImplementedError
    
    # async def start_wcgw_server(self):
    #     """Start WCGW MCP server."""
    #     pass
    
    # async def stop_wcgw_server(self):
    #     """Stop WCGW MCP server."""
    #     pass
    
    async def _edit_file_with_chunks(self, file_path: str, instructions: str, error_line: int = None) -> Dict[str, Any]:
        """Edit a file using chunking with context method."""
        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            chunk_size = 50  # Lines per chunk
            overlap = 10  # Overlapping lines for context
            
            # If error line is known, focus on that chunk
            if error_line:
                start_line = max(0, error_line - chunk_size // 2)
                end_line = min(total_lines, error_line + chunk_size // 2)
            else:
                # Process first chunk by default
                start_line = 0
                end_line = min(chunk_size, total_lines)
            
            # Extract relevant chunk with overlap
            chunk_start = max(0, start_line - overlap)
            chunk_end = min(total_lines, end_line + overlap)
            chunk_lines = lines[chunk_start:chunk_end]
            chunk_content = ''.join(chunk_lines)
            
            # Create editing prompt with chunk
            edit_prompt = f"""You are editing a file. Here is the relevant section:

File: {os.path.basename(file_path)}
Lines {chunk_start + 1} to {chunk_end}:
```
{chunk_content}
```

Task: {instructions}

Provide ONLY the fixed code for this section, with no explanations or markdown.
Start your response with the fixed code immediately."""

            # Get fixed code from LLM
            response = self.llm.invoke([HumanMessage(content=edit_prompt)])
            fixed_chunk = response.content.strip()
            
            # Remove markdown code fences if present
            if fixed_chunk.startswith('```'):
                fixed_chunk = '\n'.join(fixed_chunk.split('\n')[1:-1])
            
            # Replace the chunk in the original lines
            fixed_lines = fixed_chunk.split('\n')
            # Keep overlap context unchanged, only modify the target section
            new_lines = (
                lines[:start_line] + 
                [line + '\n' if not line.endswith('\n') else line for line in fixed_lines] +
                lines[end_line:]
            )
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            return {"success": True, "lines_modified": end_line - start_line}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stop_project(self):
        """Stop the running project."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None


class FrontendDebugger(ProjectDebugger):
    """Debugging agent for React frontend."""
    
    def __init__(self, project_path: str):
        super().__init__(project_path, "frontend", "FE-DEBUG-1")
        self.port = 3000
    
    def start_project(self) -> Optional[subprocess.Popen]:
        """Start React development server."""
        self.log_print(f"\n{'='*60}")
        self.log_print(f"FRONTEND DEBUGGER - Starting Project")
        self.log_print(f"{'='*60}")
        self.log_print(f"Project path: {self.project_path}")
        self.log_print(f"Port: {self.port}")
        
        try:
            self.log_print("\n[1/2] Starting npm development server...")
            
            # Start npm in background
            self.process = subprocess.Popen(
                "npm start",
                shell=True,
                cwd=self.project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.log_print(f"  Process started (PID: {self.process.pid})")
            self.log_print("  Waiting for server to start (30 seconds)...")
            
            # Wait for server to start
            time.sleep(30)
            
            # Check if process is still running
            if self.process.poll() is not None:
                # Process ended, check for errors
                stdout, stderr = self.process.communicate()
                self.log_print(f"✗ Server failed to start")
                self.log_print(f"  stdout: {stdout[:1000]}")
                self.log_print(f"  stderr: {stderr[:1000]}")
                return None
            
            self.log_print(f"✓ Server appears to be running")
            return self.process
            
        except Exception as e:
            self.log_print(f"✗ Failed to start server: {str(e)}")
            return None
    
    def check_errors(self) -> List[Dict[str, Any]]:
        """Check for compilation and runtime errors by analyzing React output."""
        self.log_print(f"\n[2/2] Checking for errors...")
        errors = []
        
        if not self.process:
            self.log_print("  No running process to check")
            return errors
        
        try:
            # Check if process crashed
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                error_output = stderr if stderr else stdout
                
                if error_output:
                    # Parse React/webpack error from output
                    error_details = self._parse_react_error(error_output)
                    if error_details:
                        errors.append(error_details)
                        self.log_print(f"  ✗ Found {error_details['type']} in {error_details.get('file', 'unknown')}")
                    else:
                        # Fallback if we can't parse it
                        errors.append({
                            "type": "crash",
                            "message": "React dev server crashed",
                            "details": error_output[-2000:]
                        })
                        self.log_print(f"  ✗ Found crash error (could not parse details)")
                else:
                    self.log_print(f"  ✓ Process ended cleanly")
                
                return errors
            
            # If server is running, no errors detected
            self.log_print(f"  ✓ Server running, no errors detected")
            return errors
            
        except Exception as e:
            self.log_print(f"  ✗ Error during check: {str(e)}")
            return errors
    
    def _parse_react_error(self, error_output: str) -> Optional[Dict[str, Any]]:
        """Parse React/webpack error output to extract error details."""
        import re
        
        # React errors look like:
        # "Failed to compile."
        # "./src/App.js"
        # "  Line 5:15:  'React' is not defined  no-undef"
        # Or: "SyntaxError: Unexpected token (10:5)"
        
        # Try to find file path
        file_pattern = r'(?:\.\/)?src[\/\\][\w\/\\.-]+\.(?:js|jsx)'
        file_match = re.search(file_pattern, error_output)
        
        # Try to find line number
        line_pattern = r'Line (\d+):|line (\d+)|:(\d+):\d+'
        line_match = re.search(line_pattern, error_output)
        
        # Try to find error message
        error_pattern = r'(SyntaxError|TypeError|ReferenceError|Error): (.+?)(?:\n|$)'
        error_match = re.search(error_pattern, error_output)
        
        if file_match:
            file_path = file_match.group(0)
            # Convert to absolute path
            if file_path.startswith('./'):
                file_path = file_path[2:]
            file_path = os.path.join(self.project_path, file_path)
            
            line_num = None
            if line_match:
                line_num = int(line_match.group(1) or line_match.group(2) or line_match.group(3))
            
            error_type = "compilation"
            error_msg = "Compilation error"
            
            if error_match:
                error_type = error_match.group(1).lower().replace('error', '')
                error_msg = f"{error_match.group(1)}: {error_match.group(2).strip()}"
            elif 'Failed to compile' in error_output:
                error_msg = "Failed to compile"
            
            result = {
                "type": error_type,
                "file": file_path,
                "message": error_msg,
                "details": error_output[-2000:]
            }
            
            if line_num:
                result["line"] = line_num
            
            return result
        
        return None
    
    async def fix_error(self, error: Dict[str, Any]) -> bool:
        """Use LLM to reason about error and choose action to fix it."""
        self.log_print(f"\n  Attempting to fix: {error.get('type')} error")
        
        # Stage 1: Reason about the error
        reasoning_prompt = f"""You are a React debugging expert. Analyze this error and reason about its cause.

Error Type: {error.get('type')}
Message: {error.get('message')}
File: {error.get('file', 'N/A')}
Line: {error.get('line', 'N/A')}
Details: {error.get('details', 'N/A')[:500]}

Think step by step:
1. What type of error is this?
2. What is the most likely cause?
3. What needs to be fixed?

Provide a clear, concise analysis of the problem."""
        
        try:
            reasoning_response = self.llm.invoke([HumanMessage(content=reasoning_prompt)])
            reasoning = reasoning_response.content.strip()
            
            self.log_print(f"\n  Reasoning: {reasoning[:300]}...")
            
            # Stage 2: List steps to solve the bug
            file_path = error.get('file')
            
            steps_prompt = f"""Based on this error analysis, list ALL the steps needed to completely solve this bug.

Error: {error.get('message')}
File: {file_path or 'N/A'}
Analysis: {reasoning}

Break down the solution into separate, distinct actions. Each step should be:
- A specific action (modify a file, rename a file, run a command, etc.)
- In a specific location (which file, which directory)
- Clearly different from other steps

Example for import error with hyphenated module name:
1. FILESYSTEM: Rename file 'my-module.js' to 'my_module.js' (hyphens not allowed in imports)
2. MODIFY_FILE: Update import statement in App.js from "import MyModule from './my-module'" to "import MyModule from './my_module'"
3. MODIFY_FILE: Update any other files that import this module

Example for missing dependency:
1. FILESYSTEM: Run 'npm install axios' to add missing package
2. MODIFY_FILE: Verify import statement is correct in api.js

Provide your step-by-step solution with SPECIFIC files and actions:"""

            steps_response = self.llm.invoke([HumanMessage(content=steps_prompt)])
            steps = steps_response.content.strip()
            
            self.log_print(f"\n  Steps to fix:")
            self.log_print(f"  {steps[:400]}...")
            
            # Parse the steps to extract individual actions
            import re
            step_lines = [line.strip() for line in steps.split('\n') if re.match(r'^\d+\.', line.strip())]
            
            self.log_print(f"\n  Found {len(step_lines)} steps to execute")
            
            # Stage 3: Classify all steps at once
            self.log_print(f"\n  Classifying all steps...")
            
            classify_prompt = f"""You are a React debugging expert. Review this list of steps and classify each one.

Steps to classify:
{steps}

For EACH step, determine if it requires:
- MODIFY_FILE: Changing code in a file
- FILESYSTEM: Filesystem operations (rename, move, delete, install package, create file, run command, etc.)

Respond in this EXACT format:
STEP 1: [MODIFY_FILE or FILESYSTEM]
STEP 2: [MODIFY_FILE or FILESYSTEM]
STEP 3: [MODIFY_FILE or FILESYSTEM]
...and so on for all steps."""

            classify_response = self.llm.invoke([HumanMessage(content=classify_prompt)])
            classifications = classify_response.content.strip()
            
            self.log_print(f"\n  Classifications:")
            self.log_print(f"  {classifications[:300]}...")
            
            # Parse classifications
            classification_dict = {}
            for line in classifications.split('\n'):
                match = re.match(r'STEP (\d+):\s*(MODIFY_FILE|FILESYSTEM)', line.strip(), re.IGNORECASE)
                if match:
                    step_num = int(match.group(1))
                    action_type = match.group(2).upper()
                    classification_dict[step_num] = action_type
            
            # Execute each step sequentially
            steps_executed = 0
            for i, step_line in enumerate(step_lines, 1):
                self.log_print(f"\n  Executing step {i}/{len(step_lines)}...")
                self.log_print(f"    {step_line[:150]}")
                
                # Get the classification for this step
                action_type = classification_dict.get(i)
                
                if not action_type:
                    self.log_print(f"    ✗ No classification found for this step")
                    continue
                
                self.log_print(f"    Action type: {action_type}")
                
                if action_type == "MODIFY_FILE":
                    # Use WCGW tool to modify the file
                    modify_instruction = f"""Fix this error in the code:

Step to fix: {step_line}
Original Error: {error.get('message')}

Make the necessary code changes to resolve this issue."""

                    try:
                        # Get target file path from step if mentioned, otherwise use error file
                        target_file = file_path
                        
                        # Try to extract file path from step description
                        file_mention = re.search(r'in ([\\w/\\\\.-]+\\.(?:js|jsx|tsx|ts))', step_line, re.IGNORECASE)
                        if file_mention:
                            mentioned_file = file_mention.group(1)
                            # Convert to absolute path
                            if not os.path.isabs(mentioned_file):
                                mentioned_file = os.path.join(self.project_path, mentioned_file)
                            if os.path.exists(mentioned_file):
                                target_file = mentioned_file
                        
                        if not target_file or not os.path.exists(target_file):
                            self.log_print(f"    ✗ Could not determine target file")
                            continue
                        
                        self.log_print(f"    Target file: {os.path.basename(target_file)}")
                        
                        # Use chunked editing to modify the file
                        error_line = error.get('line')
                        result = await self._edit_file_with_chunks(target_file, modify_instruction, error_line)
                        
                        if result.get('success'):
                            lines_modified = result.get('lines_modified', 0)
                            self.log_print(f"    ✓ Modified {os.path.basename(target_file)} ({lines_modified} lines)")
                            steps_executed += 1
                        else:
                            self.log_print(f"    ✗ Edit failed: {result.get('error', 'Unknown error')}")
                        
                    except Exception as e:
                        self.log_print(f"    ✗ Failed to modify file: {str(e)}")
                            
                elif action_type == "FILESYSTEM":
                    # Get the command for this filesystem operation
                    command_prompt = f"""Provide the exact command to execute for this step:

Step: {step_line}
Project directory: {self.project_path}

Respond with ONLY the command, nothing else.
Examples:
- npm install axios
- mv src/old-name.js src/newName.js
- rm src/unused.js"""

                    command_response = self.llm.invoke([HumanMessage(content=command_prompt)])
                    command = command_response.content.strip()
                    
                    self.log_print(f"    Command: {command}")
                    
                    # TODO: Use filesystem MCP here instead of subprocess
                    # For now, using subprocess as placeholder
                    try:
                        result = subprocess.run(
                            command,
                            shell=True,
                            cwd=self.project_path,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        
                        if result.returncode == 0:
                            self.log_print(f"    ✓ Command succeeded")
                            steps_executed += 1
                        else:
                            self.log_print(f"    ✗ Command failed: {result.stderr[:100]}")
                    except Exception as e:
                        self.log_print(f"    ✗ Failed to execute: {str(e)}")
            
            # Record overall result
            if steps_executed > 0:
                self.log_print(f"\n  ✓ Successfully executed {steps_executed}/{len(step_lines)} steps")
                self.fixes_applied.append({
                    "error": error,
                    "steps_total": len(step_lines),
                    "steps_executed": steps_executed,
                    "applied": True
                })
                return True
            else:
                self.log_print(f"\n  ✗ No steps could be executed")
                return False
            
        except Exception as e:
            self.log_print(f"  ✗ Failed to generate fix: {str(e)}")
            return False


class BackendDebugger(ProjectDebugger):
    """Debugging agent for Flask backend."""
    
    def __init__(self, project_path: str):
        super().__init__(project_path, "backend", "BE-DEBUG-1")
        self.port = 5000
    
    def start_project(self) -> Optional[subprocess.Popen]:
        """Start Flask development server."""
        self.log_print(f"\n{'='*60}")
        self.log_print(f"BACKEND DEBUGGER - Starting Project")
        self.log_print(f"{'='*60}")
        self.log_print(f"Project path: {self.project_path}")
        self.log_print(f"Port: {self.port}")
        
        try:
            self.log_print("\n[1/2] Starting Flask server...")
            
            # Determine Python executable in venv
            if os.name == 'nt':  # Windows
                python_exe = os.path.join(self.project_path, "venv", "Scripts", "python.exe")
            else:  # Unix
                python_exe = os.path.join(self.project_path, "venv", "bin", "python")
            
            # Check if venv python exists
            if not os.path.exists(python_exe):
                self.log_print(f"  ⚠ Virtual environment not found, using system Python")
                python_exe = "python"
            
            app_py = os.path.join(self.project_path, "app.py")
            
            self.log_print(f"  Python: {python_exe}")
            self.log_print(f"  App: {app_py}")
            
            # Start Flask in background
            self.process = subprocess.Popen(
                f'"{python_exe}" "{app_py}"',
                shell=True,
                cwd=self.project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.log_print(f"  Process started (PID: {self.process.pid})")
            self.log_print("  Waiting for server to start (10 seconds)...")
            
            # Wait for server to start
            time.sleep(10)
            
            # Check if process is still running
            if self.process.poll() is not None:
                # Process ended, check for errors
                stdout, stderr = self.process.communicate()
                self.log_print(f"✗ Server failed to start")
                self.log_print(f"  stdout: {stdout[:1000]}")
                self.log_print(f"  stderr: {stderr[:1000]}")
                return None
            
            self.log_print(f"✓ Server appears to be running")
            return self.process
            
        except Exception as e:
            self.log_print(f"✗ Failed to start server: {str(e)}")
            return None
    
    def check_errors(self) -> List[Dict[str, Any]]:
        """Check for Python errors by analyzing server output."""
        self.log_print(f"\n[2/2] Checking for errors...")
        errors = []
        
        if not self.process:
            self.log_print("  No running process to check")
            return errors
        
        try:
            # Check if process crashed
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                error_output = stderr if stderr else stdout
                
                if error_output:
                    # Parse the actual error from stderr/stdout
                    error_details = self._parse_python_error(error_output)
                    if error_details:
                        errors.append(error_details)
                        self.log_print(f"  ✗ Found {error_details['type']} in {error_details.get('file', 'unknown')}")
                    else:
                        # Fallback if we can't parse it
                        errors.append({
                            "type": "crash",
                            "message": "Server process crashed",
                            "details": error_output[-2000:]
                        })
                        self.log_print(f"  ✗ Found crash error (could not parse details)")
                else:
                    self.log_print(f"  ✓ Process ended cleanly")
                
                return errors
            
            # If server is running, no errors detected
            self.log_print(f"  ✓ Server running, no errors detected")
            return errors
            
        except Exception as e:
            self.log_print(f"  ✗ Error during check: {str(e)}")
            return errors
    
    def _parse_python_error(self, error_output: str) -> Optional[Dict[str, Any]]:
        """Parse Python traceback to extract error details."""
        import re
        
        # Look for common Python error patterns
        # Example: "  File "app.py", line 15, in <module>"
        # Followed by: "ImportError: No module named 'flask_sqlalchemy'"
        
        file_pattern = r'File "([^"]+)", line (\d+)'
        error_pattern = r'(\w+Error): (.+?)(?:\n|$)'
        
        file_match = re.search(file_pattern, error_output)
        error_match = re.search(error_pattern, error_output)
        
        if file_match and error_match:
            file_path = file_match.group(1)
            line_num = int(file_match.group(2))
            error_type = error_match.group(1)
            error_msg = error_match.group(2).strip()
            
            # Convert relative path to absolute if needed
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.project_path, file_path)
            
            return {
                "type": error_type.lower().replace('error', ''),
                "file": file_path,
                "line": line_num,
                "message": f"{error_type}: {error_msg}",
                "details": error_output[-2000:]
            }
        
        return None
    
    async def fix_error(self, error: Dict[str, Any]) -> bool:
        """Use LLM to reason about error and choose action to fix it."""
        self.log_print(f"\n  Attempting to fix: {error.get('type')} error in {error.get('file', 'N/A')}")
        
        # Stage 1: Reason about the error
        reasoning_prompt = f"""You are a Flask/Python debugging expert. Analyze this error and reason about its cause.

Error Type: {error.get('type')}
Message: {error.get('message')}
File: {error.get('file', 'N/A')}
Line: {error.get('line', 'N/A')}
Details: {error.get('details', 'N/A')[:500]}

Think step by step:
1. What type of error is this?
2. What is the most likely cause?
3. What needs to be fixed?

Provide a clear, concise analysis of the problem."""
        
        try:
            reasoning_response = self.llm.invoke([HumanMessage(content=reasoning_prompt)])
            reasoning = reasoning_response.content.strip()
            
            self.log_print(f"\n  Reasoning: {reasoning[:300]}...")
            
            # Stage 2: List steps to solve the bug
            file_path = error.get('file')
            
            steps_prompt = f"""Based on this error analysis, list ALL the steps needed to completely solve this bug.

Error: {error.get('message')}
File: {file_path or 'N/A'}
Analysis: {reasoning}

Break down the solution into separate, distinct actions. Each step should be:
- A specific action (modify a file, rename a file, run a command, etc.)
- In a specific location (which file, which directory)
- Clearly different from other steps

Example for import error with hyphenated module name:
1. FILESYSTEM: Rename file 'my_helper.py' to 'helper.py' (fix naming convention)
2. MODIFY_FILE: Update import statement in app.py from "from my_helper import func" to "from helper import func"
3. MODIFY_FILE: Update any other files that import from my_helper

Example for missing dependency:
1. FILESYSTEM: Run 'pip install flask-sqlalchemy' to add missing package
2. MODIFY_FILE: Verify import statement is correct in models.py

Provide your step-by-step solution with SPECIFIC files and actions:"""

            steps_response = self.llm.invoke([HumanMessage(content=steps_prompt)])
            steps = steps_response.content.strip()
            
            self.log_print(f"\n  Steps to fix:")
            self.log_print(f"  {steps[:400]}...")
            
            # Parse the steps to extract individual actions
            import re
            step_lines = [line.strip() for line in steps.split('\n') if re.match(r'^\d+\.', line.strip())]
            
            self.log_print(f"\n  Found {len(step_lines)} steps to execute")
            
            # Stage 3: Classify all steps at once
            self.log_print(f"\n  Classifying all steps...")
            
            classify_prompt = f"""You are a Flask/Python debugging expert. Review this list of steps and classify each one.

Steps to classify:
{steps}

For EACH step, determine if it requires:
- MODIFY_FILE: Changing code in a file
- FILESYSTEM: Filesystem operations (rename, move, delete, install package, create file, run command, etc.)

Respond in this EXACT format:
STEP 1: [MODIFY_FILE or FILESYSTEM]
STEP 2: [MODIFY_FILE or FILESYSTEM]
STEP 3: [MODIFY_FILE or FILESYSTEM]
...and so on for all steps."""

            classify_response = self.llm.invoke([HumanMessage(content=classify_prompt)])
            classifications = classify_response.content.strip()
            
            self.log_print(f"\n  Classifications:")
            self.log_print(f"  {classifications[:300]}...")
            
            # Parse classifications
            classification_dict = {}
            for line in classifications.split('\n'):
                match = re.match(r'STEP (\d+):\s*(MODIFY_FILE|FILESYSTEM)', line.strip(), re.IGNORECASE)
                if match:
                    step_num = int(match.group(1))
                    action_type = match.group(2).upper()
                    classification_dict[step_num] = action_type
            
            # Execute each step sequentially
            steps_executed = 0
            for i, step_line in enumerate(step_lines, 1):
                self.log_print(f"\n  Executing step {i}/{len(step_lines)}...")
                self.log_print(f"    {step_line[:150]}")
                
                # Get the classification for this step
                action_type = classification_dict.get(i)
                
                if not action_type:
                    self.log_print(f"    ✗ No classification found for this step")
                    continue
                
                self.log_print(f"    Action type: {action_type}")
                
                if action_type == "MODIFY_FILE":
                    # Use WCGW tool to modify the file
                    modify_instruction = f"""Fix this error in the code:

Step to fix: {step_line}
Original Error: {error.get('message')}

Make the necessary code changes to resolve this issue."""

                    try:
                        # Get target file path from step if mentioned, otherwise use error file
                        target_file = file_path
                        
                        # Try to extract file path from step description
                        file_mention = re.search(r'in ([\\w/\\\\.-]+\\.py)', step_line, re.IGNORECASE)
                        if file_mention:
                            mentioned_file = file_mention.group(1)
                            # Convert to absolute path
                            if not os.path.isabs(mentioned_file):
                                mentioned_file = os.path.join(self.project_path, mentioned_file)
                            if os.path.exists(mentioned_file):
                                target_file = mentioned_file
                        
                        if not target_file or not os.path.exists(target_file):
                            self.log_print(f"    ✗ Could not determine target file")
                            continue
                        
                        self.log_print(f"    Target file: {os.path.basename(target_file)}")
                        
                        # Use chunked editing to modify the file
                        error_line = error.get('line')
                        result = await self._edit_file_with_chunks(target_file, modify_instruction, error_line)
                        
                        if result.get('success'):
                            lines_modified = result.get('lines_modified', 0)
                            self.log_print(f"    ✓ Modified {os.path.basename(target_file)} ({lines_modified} lines)")
                            steps_executed += 1
                        else:
                            self.log_print(f"    ✗ Edit failed: {result.get('error', 'Unknown error')}")
                        
                    except Exception as e:
                        self.log_print(f"    ✗ Failed to modify file: {str(e)}")
                            
                elif action_type == "FILESYSTEM":
                    # Get the command for this filesystem operation
                    command_prompt = f"""Provide the exact command to execute for this step:

Step: {step_line}
Project directory: {self.project_path}

Respond with ONLY the command, nothing else.
Examples:
- pip install flask-sqlalchemy
- mv backend/old_name.py backend/new_name.py
- rm backend/unused.py"""

                    command_response = self.llm.invoke([HumanMessage(content=command_prompt)])
                    command = command_response.content.strip()
                    
                    self.log_print(f"    Command: {command}")
                    
                    # TODO: Use filesystem MCP here instead of subprocess
                    # For now, using subprocess as placeholder
                    try:
                        # For Python packages, use the venv's pip
                        if 'pip install' in command.lower():
                            if os.name == 'nt':
                                pip_exe = os.path.join(self.project_path, "venv", "Scripts", "pip.exe")
                            else:
                                pip_exe = os.path.join(self.project_path, "venv", "bin", "pip")
                            
                            if os.path.exists(pip_exe):
                                command = command.replace('pip install', f'"{pip_exe}" install')
                        
                        result = subprocess.run(
                            command,
                            shell=True,
                            cwd=self.project_path,
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        
                        if result.returncode == 0:
                            self.log_print(f"    ✓ Command succeeded")
                            steps_executed += 1
                        else:
                            # Command failed - ask LLM to fix it
                            error_output = result.stderr[:500] if result.stderr else result.stdout[:500]
                            self.log_print(f"    ✗ Command failed: {error_output[:100]}")
                            
                            # Try to get a corrected command
                            retry_prompt = f"""The following command failed:

Command: {command}
Error output: {error_output}
Working directory: {self.project_path}

Provide a corrected command that will work. Respond with ONLY the command, nothing else."""
                            
                            retry_response = self.llm.invoke([HumanMessage(content=retry_prompt)])
                            corrected_command = retry_response.content.strip()
                            
                            if corrected_command and corrected_command != command:
                                self.log_print(f"    Retrying with: {corrected_command}")
                                
                                # Retry with corrected command
                                retry_result = subprocess.run(
                                    corrected_command,
                                    shell=True,
                                    cwd=self.project_path,
                                    capture_output=True,
                                    text=True,
                                    timeout=120
                                )
                                
                                if retry_result.returncode == 0:
                                    self.log_print(f"    ✓ Corrected command succeeded")
                                    steps_executed += 1
                                else:
                                    self.log_print(f"    ✗ Corrected command also failed: {retry_result.stderr[:100]}")
                            else:
                                self.log_print(f"    ✗ Could not generate corrected command")
                    except Exception as e:
                        self.log_print(f"    ✗ Failed to execute: {str(e)}")
            
            # Record overall result
            if steps_executed > 0:
                self.log_print(f"\n  ✓ Successfully executed {steps_executed}/{len(step_lines)} steps")
                self.fixes_applied.append({
                    "error": error,
                    "steps_total": len(step_lines),
                    "steps_executed": steps_executed,
                    "applied": True
                })
                return True
            else:
                self.log_print(f"\n  ✗ No steps could be executed")
                return False
            
        except Exception as e:
            self.log_print(f"  ✗ Failed to generate fix: {str(e)}")
            return False


async def run_debugging_agents(react_path: str, flask_path: str):
    """
    Run both frontend and backend debugging agents in parallel.
    Loops until no errors are found.
    """
    print("\n" + "="*70)
    print("DEPLOYING DEBUGGING AGENTS")
    print("="*70)
    
    # Create agents
    frontend_debugger = FrontendDebugger(react_path)
    backend_debugger = BackendDebugger(flask_path)
    
    # Start projects
    print("\n[Phase 1] Starting projects...")
    
    print("\n  Starting backend...")
    backend_process = backend_debugger.start_project()
    
    print("\n  Starting frontend...")
    frontend_process = frontend_debugger.start_project()
    
    # Debugging loop - continue until no errors found
    iteration = 1
    max_iterations = 10  # Safety limit to prevent infinite loops
    
    while iteration <= max_iterations:
        print(f"\n{'='*70}")
        print(f"DEBUGGING ITERATION {iteration}")
        print(f"{'='*70}")
        
        # Check for errors
        print("\n[Check] Running diagnostics...")
        
        backend_errors = backend_debugger.check_errors()
        frontend_errors = frontend_debugger.check_errors()
        
        total_errors = len(backend_errors) + len(frontend_errors)
        
        if total_errors == 0:
            print("\n✓ No errors found! Debugging complete.")
            break
        
        print(f"\n  Found {total_errors} total errors")
        print(f"  Backend: {len(backend_errors)} errors")
        print(f"  Frontend: {len(frontend_errors)} errors")
        
        # Analyze and fix errors
        print("\n[Fix] Analyzing and fixing issues...")
        
        backend_fixes_applied = 0
        if backend_errors:
            print(f"\n  Backend errors:")
            for i, error in enumerate(backend_errors[:3], 1):  # Fix top 3 per iteration
                print(f"    [{i}] {error.get('type')}: {error.get('message')}")
                if await backend_debugger.fix_error(error):
                    if backend_debugger.fixes_applied and backend_debugger.fixes_applied[-1].get('applied'):
                        backend_fixes_applied += 1
        
        frontend_fixes_applied = 0
        if frontend_errors:
            print(f"\n  Frontend errors:")
            for i, error in enumerate(frontend_errors[:3], 1):  # Fix top 3 per iteration
                print(f"    [{i}] {error.get('type')}: {error.get('message')}")
                if await frontend_debugger.fix_error(error):
                    if frontend_debugger.fixes_applied and frontend_debugger.fixes_applied[-1].get('applied'):
                        frontend_fixes_applied += 1
        
        # Restart servers if fixes were applied
        if backend_fixes_applied > 0 or frontend_fixes_applied > 0:
            print(f"\n[Restart] Applying {backend_fixes_applied + frontend_fixes_applied} fixes and restarting...")
            
            if backend_fixes_applied > 0:
                print("\n  Restarting backend...")
                backend_debugger.stop_project()
                time.sleep(2)
                backend_process = backend_debugger.start_project()
            
            if frontend_fixes_applied > 0:
                print("\n  Restarting frontend...")
                frontend_debugger.stop_project()
                time.sleep(2)
                frontend_process = frontend_debugger.start_project()
            
            print("\n  ✓ Servers restarted")
        else:
            print("\n  ⚠ No fixes could be applied, stopping to prevent infinite loop")
            break
        
        iteration += 1
    
    if iteration > max_iterations:
        print(f"\n⚠ Reached maximum iterations ({max_iterations}), stopping debugging loop")
    
    # Save debugging report
    logs_dir = "logs"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(logs_dir, f"debugging_report_{timestamp}.json")
    
    report = {
        "timestamp": timestamp,
        "frontend": {
            "project_path": react_path,
            "running": frontend_process is not None,
            "errors_found": len(frontend_errors),
            "fixes_applied": len(frontend_debugger.fixes_applied),
            "log_file": frontend_debugger.log_file
        },
        "backend": {
            "project_path": flask_path,
            "running": backend_process is not None,
            "errors_found": len(backend_errors),
            "fixes_applied": len(backend_debugger.fixes_applied),
            "log_file": backend_debugger.log_file
        }
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    # Summary
    print("\n" + "="*70)
    print("DEBUGGING SUMMARY")
    print("="*70)
    print(f"\nBackend:")
    print(f"  Status: {'✓ Running' if backend_process else '✗ Failed to start'}")
    print(f"  Errors found: {len(backend_errors)}")
    print(f"  Fixes suggested: {len(backend_debugger.fixes_applied)}")
    print(f"  Fixes applied: {backend_fixes_applied}")
    print(f"  Log: {backend_debugger.log_file}")
    
    print(f"\nFrontend:")
    print(f"  Status: {'✓ Running' if frontend_process else '✗ Failed to start'}")
    print(f"  Errors found: {len(frontend_errors)}")
    print(f"  Fixes suggested: {len(frontend_debugger.fixes_applied)}")
    print(f"  Fixes applied: {frontend_fixes_applied}")
    print(f"  Log: {frontend_debugger.log_file}")
    
    print(f"\nReport: {report_path}")
    
    if backend_fixes_applied > 0 or frontend_fixes_applied > 0:
        print(f"\n✓ {backend_fixes_applied + frontend_fixes_applied} fixes were automatically applied to your code!")
    
    print("\n" + "="*70)
    print("PROJECTS ARE RUNNING")
    print("="*70)
    print(f"\nFrontend: http://localhost:{frontend_debugger.port}")
    print(f"Backend: http://localhost:{backend_debugger.port}")
    print("\nPress Ctrl+C to stop servers...")
    
    # Keep running until user stops
    try:
        while True:
            time.sleep(1)
            # Check if processes are still alive
            if frontend_process and frontend_process.poll() is not None:
                print("\n⚠ Frontend server stopped")
                break
            if backend_process and backend_process.poll() is not None:
                print("\n⚠ Backend server stopped")
                break
    except KeyboardInterrupt:
        print("\n\nStopping servers...")
    finally:
        frontend_debugger.stop_project()
        backend_debugger.stop_project()
        print("✓ Servers stopped")
