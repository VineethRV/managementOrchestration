"""
Backend Debugger Agent - Runs backend, analyzes errors, and fixes them using reasoning + file agents.

Architecture:
1. Run backend and capture errors
2. Create high-level todo list of fixes
3. For each todo:
   - Reasoning agent breaks down into simple steps
   - File agent executes each step
   - Validate and continue
"""

import os
import subprocess
import threading
import queue
import time
import re
import asyncio
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from file_manager import FileAgent

load_dotenv()


class BackendDebugger:
    """Debugs backend by analyzing errors and coordinating reasoning + file agents."""
    
    def __init__(self, backend_path: str):
        """
        Initialize the backend debugger.
        
        Args:
            backend_path: Path to the backend directory
        """
        self.backend_path = backend_path
        self.llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, max_tokens=4000)
    
    def setup_environment(self) -> bool:
        """
        Create virtual environment and install requirements if not already set up.
        
        Returns:
            bool: True if environment is ready, False if setup failed
        """
        print(f"\n{'='*80}")
        print("SETTING UP BACKEND ENVIRONMENT")
        print(f"{'='*80}")
        
        # Determine venv paths based on OS
        if os.name == 'nt':
            venv_dir = os.path.join(self.backend_path, "venv")
            python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
            pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            venv_dir = os.path.join(self.backend_path, "venv")
            python_exe = os.path.join(venv_dir, "bin", "python")
            pip_exe = os.path.join(venv_dir, "bin", "pip")
        
        requirements_file = os.path.join(self.backend_path, "requirements.txt")
        
        # Step 1: Create venv if it doesn't exist
        if not os.path.exists(python_exe):
            print(f"Creating virtual environment at: {venv_dir}")
            try:
                command = ["python", "-m", "venv", "venv"]
                print(f"RUNNING TERMINAL COMMAND: {' '.join(command)}")
                result = subprocess.run(
                    command,
                    cwd=self.backend_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"✗ Failed to create venv: {result.stderr}")
                    return False
                print(f"✓ Virtual environment created")
            except Exception as e:
                print(f"✗ Failed to create venv: {e}")
                return False
        else:
            print(f"✓ Virtual environment already exists at: {venv_dir}")
        
        # Step 2: Install requirements if requirements.txt exists
        if os.path.exists(requirements_file):
            print(f"Installing requirements from: {requirements_file}")
            try:
                command = f'"{pip_exe}" install -r requirements.txt'
                print(f"RUNNING TERMINAL COMMAND: {command}")
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.backend_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"✗ Failed to install requirements: {result.stderr}")
                    return False
                print(f"✓ Requirements installed successfully")
                if result.stdout:
                    # Show only last few lines of pip output
                    lines = result.stdout.strip().split('\n')
                    for line in lines[-5:]:
                        print(f"  {line}")
            except Exception as e:
                print(f"✗ Failed to install requirements: {e}")
                return False
        else:
            print(f"⚠ No requirements.txt found at: {requirements_file}")
        
        print(f"✓ Environment setup complete")
        return True
        
    def run_backend(self, duration: int = 15) -> dict:
        """
        Run backend and capture output for specified duration.
        
        Args:
            duration: How long to collect output (seconds)
            
        Returns:
            dict: Contains process, output lines, is_running, has_error
        """
        print(f"\n{'='*80}")
        print("RUNNING BACKEND")
        print(f"{'='*80}")
        print(f"Backend path: {self.backend_path}")
        print(f"Collection duration: {duration}s")
        
        # Check for venv
        if os.name == 'nt':
            python_exe = os.path.join(self.backend_path, "venv", "Scripts", "python.exe")
        else:
            python_exe = os.path.join(self.backend_path, "venv", "bin", "python")
        
        if not os.path.exists(python_exe):
            python_exe = "python"
        
        app_py = os.path.join(self.backend_path, "app.py")
        
        if not os.path.exists(app_py):
            return {
                'process': None,
                'output': [f"ERROR: app.py not found at {app_py}"],
                'is_running': False,
                'has_error': True
            }
        
        # Start the Flask server
        output_queue = queue.Queue()
        output_lines = []
        
        command = [python_exe, "app.py"]
        print(f"RUNNING TERMINAL COMMAND: {' '.join(command)}")
        
        process = subprocess.Popen(
            command,
            cwd=self.backend_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        def read_output():
            """Read output from process and put into queue."""
            try:
                for line in iter(process.stdout.readline, ''):
                    if line:
                        output_queue.put(line.strip())
            except:
                pass
        
        # Start thread to read output
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()
        
        print(f"Collecting output...")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                line = output_queue.get(timeout=1)
                output_lines.append(line)
                print(f"  {line}")
            except queue.Empty:
                pass
            
            # Check if process stopped
            if process.poll() is not None:
                print("Backend process stopped")
                break
        
        is_running = process.poll() is None
        has_error = self._detect_error(output_lines)
        
        return {
            'process': process,
            'output': output_lines,
            'is_running': is_running,
            'has_error': has_error
        }
    
    def _detect_error(self, output_lines: list) -> bool:
        """Detect if there's an error in the output."""
        error_patterns = [
            r'Error', r'Exception', r'Traceback', r'failed',
            r'ModuleNotFoundError', r'ImportError', r'SyntaxError', 
            r'NameError'
        ]
        
        for line in output_lines:
            for pattern in error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    return True
        return False
    
    def stop_backend(self, process):
        """Stop the backend process."""
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
            print("\nBackend stopped")
    
    def analyze_errors(self, output_lines: list) -> dict:
        """
        Analyze errors and create high-level todo list.
        
        Args:
            output_lines: List of output lines from backend
            
        Returns:
            dict: Contains diagnosis and todo list
        """
        print(f"\n{'='*80}")
        print("ANALYZING ERRORS")
        print(f"{'='*80}")
        
        output_text = '\n'.join(output_lines[-100:])  # Last 100 lines
        
        analysis_prompt = f"""You are a Flask backend debugging expert. Analyze these errors and create a high-level fix plan.

Backend directory: {self.backend_path}

Error output:
```
{output_text}
```

Provide:
1. Brief diagnosis (2-3 sentences) of the root cause
2. High-level todo list (3-7 items) to fix the issue

Format your response as:

DIAGNOSIS:
<your diagnosis here>

TODO:
1. <high-level step 1>
2. <high-level step 2>
3. <high-level step 3>
...

Keep todos high-level and actionable. Each todo should be a logical fix step."""

        response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
        response_text = response.content.strip()
        
        # Parse diagnosis
        diagnosis = ""
        if 'DIAGNOSIS:' in response_text:
            diag_start = response_text.find('DIAGNOSIS:') + len('DIAGNOSIS:')
            diag_end = response_text.find('TODO:') if 'TODO:' in response_text else len(response_text)
            diagnosis = response_text[diag_start:diag_end].strip()
        
        # Parse todos
        todos = []
        if 'TODO:' in response_text:
            todo_start = response_text.find('TODO:') + len('TODO:')
            todo_text = response_text[todo_start:].strip()
            
            for line in todo_text.split('\n'):
                line = line.strip()
                if line and line[0].isdigit():
                    # Remove number prefix
                    todo = re.sub(r'^\d+\.\s*', '', line)
                    todos.append({
                        'id': len(todos) + 1,
                        'task': todo,
                        'status': 'pending'
                    })
        
        print(f"\nDiagnosis: {diagnosis}")
        print(f"\nTodo List ({len(todos)} items):")
        for todo in todos:
            print(f"  {todo['id']}. {todo['task']}")
        
        return {
            'diagnosis': diagnosis,
            'todos': todos
        }
    
    async def execute_todo(self, todo: dict, diagnosis: str) -> dict:
        """
        Execute a single todo using reasoning agent + file agent feedback loop.
        
        Args:
            todo: Todo item dict with id, task, status
            diagnosis: Overall diagnosis context
            
        Returns:
            dict: Contains success, reasoning_steps, file_operations
        """
        print(f"\n{'='*80}")
        print(f"EXECUTING TODO {todo['id']}: {todo['task']}")
        print(f"{'='*80}")
        
        reasoning_steps = []
        file_operations = []
        conversation_history = []  # Maintain conversation context
        max_iterations = 10
        
        # Initial context for reasoning agent
        initial_context = f"""You are a reasoning agent helping fix a backend issue.

Overall Diagnosis: {diagnosis}

Current Todo: {todo['task']}

Your task:
1. Analyze what needs to be done for this todo
2. Break it down into ONE simple file operation per iteration
3. Provide clear instruction for the file agent
4. Review results and decide next step

RULES:
- ONE file operation per iteration
- Never read more than 300 lines at once (use smaller ranges like 1-50, 51-100, etc.)
- For large files, work in chunks
- Keep instructions simple and specific
- Build on previous steps progressively

Respond in this format:

REASONING: <explain what you're thinking and why this step>
NEXT_STEP: <describe the specific file operation needed>
FILE_AGENT_INSTRUCTION: <clear, simple instruction for file agent>
STATUS: <CONTINUE or COMPLETE>

STATUS should be COMPLETE only when this todo is fully resolved.

Let's start - what's your first step?"""
        
        conversation_history.append({"role": "user", "content": initial_context})
        
        for iteration in range(1, max_iterations + 1):
            print(f"\n--- Iteration {iteration}/{max_iterations} ---")
            
            # Build messages from conversation history
            from langchain_core.messages import HumanMessage, AIMessage
            messages = []
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))
            
            # Get reasoning agent response
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Add to conversation history
            conversation_history.append({"role": "assistant", "content": response_text})
            print(f"\nReasoning Agent Response:\n{response_text}\n")
            
            # Parse response
            reasoning = ""
            next_step = ""
            instruction = ""
            status = "CONTINUE"
            
            if 'REASONING:' in response_text:
                r_start = response_text.find('REASONING:') + len('REASONING:')
                r_end = response_text.find('NEXT_STEP:') if 'NEXT_STEP:' in response_text else len(response_text)
                reasoning = response_text[r_start:r_end].strip()
            
            if 'NEXT_STEP:' in response_text:
                n_start = response_text.find('NEXT_STEP:') + len('NEXT_STEP:')
                n_end = response_text.find('FILE_AGENT_INSTRUCTION:') if 'FILE_AGENT_INSTRUCTION:' in response_text else len(response_text)
                next_step = response_text[n_start:n_end].strip()
            
            if 'FILE_AGENT_INSTRUCTION:' in response_text:
                i_start = response_text.find('FILE_AGENT_INSTRUCTION:') + len('FILE_AGENT_INSTRUCTION:')
                i_end = response_text.find('STATUS:') if 'STATUS:' in response_text else len(response_text)
                instruction = response_text[i_start:i_end].strip()
            
            if 'STATUS:' in response_text:
                s_start = response_text.find('STATUS:') + len('STATUS:')
                status = response_text[s_start:].strip().upper()
                if 'COMPLETE' in status:
                    status = 'COMPLETE'
            
            # Record reasoning step
            reasoning_steps.append({
                'iteration': iteration,
                'reasoning': reasoning[:200] + '...' if len(reasoning) > 200 else reasoning,
                'next_step': next_step
            })
            
            # Check if complete
            if status == 'COMPLETE':
                print(f"\n✓ Todo marked as COMPLETE by reasoning agent")
                return {
                    'success': True,
                    'reasoning_steps': reasoning_steps,
                    'file_operations': file_operations
                }
            
            # Execute file operation with file agent
            if instruction:
                print(f"\nCalling File Agent with: {instruction[:100]}...")
                
                file_agent = FileAgent(self.backend_path)
                file_result = await file_agent.execute_task(instruction, max_iterations=5)
                
                file_operations.append({
                    'iteration': iteration,
                    'step': next_step,
                    'instruction': instruction,
                    'success': file_result['success'],
                    'answer': file_result.get('answer', ''),
                    'output': file_result.get('output', '')[:200]
                })
                
                success_status = '✓ Success' if file_result['success'] else '✗ Failed'
                print(f"\nFile Agent Result: {success_status}")
                
                # Add file agent result to conversation history
                feedback = f"""File Agent Result:

Instruction Given: {instruction}

Status: {success_status}

Output: {file_result.get('output', '')[:300]}

"""
                if file_result.get('answer'):
                    feedback += f"Answer Retrieved: {file_result['answer'][:300]}\n\n"
                
                feedback += "What's your next step? (Remember: ONE operation at a time, max 300 lines per read)"
                
                conversation_history.append({"role": "user", "content": feedback})
        
        # Max iterations reached
        print(f"\n⚠ Max iterations reached for this todo")
        return {
            'success': False,
            'reasoning_steps': reasoning_steps,
            'file_operations': file_operations
        }
    
    async def debug_backend(self, duration: int = 15, max_rounds: int = 5) -> dict:
        """
        Main debugging loop.
        
        Args:
            duration: How long to collect output per round
            max_rounds: Maximum debugging rounds
            
        Returns:
            dict: Contains results and statistics
        """
        print(f"\n{'='*80}")
        print("BACKEND DEBUGGER STARTED")
        print(f"{'='*80}")
        print(f"Max rounds: {max_rounds}")
        print(f"Output collection: {duration}s per round")
        
        # Setup environment first (create venv and install requirements)
        if not self.setup_environment():
            return {
                'success': False,
                'rounds': 0,
                'message': 'Failed to setup environment (venv/requirements)'
            }
        
        for round_num in range(1, max_rounds + 1):
            print(f"\n{'#'*80}")
            print(f"ROUND {round_num}/{max_rounds}")
            print(f"{'#'*80}")
            
            # Run backend
            result = self.run_backend(duration)
            
            # Stop backend
            if result['process']:
                self.stop_backend(result['process'])
            
            # Check for errors
            if not result['has_error']:
                print(f"\n{'='*80}")
                print("✓ SUCCESS - NO ERRORS DETECTED!")
                print(f"{'='*80}")
                print(f"Backend is running without errors after {round_num} round(s)")
                return {
                    'success': True,
                    'rounds': round_num,
                    'message': 'Backend running successfully'
                }
            
            # Analyze errors
            analysis = self.analyze_errors(result['output'])
            
            if not analysis['todos']:
                print(f"\n⚠ Could not generate todos from errors")
                return {
                    'success': False,
                    'rounds': round_num,
                    'message': 'Failed to analyze errors'
                }
            
            # Execute each todo
            for todo in analysis['todos']:
                todo_result = await self.execute_todo(todo, analysis['diagnosis'])
                todo['status'] = 'completed' if todo_result['success'] else 'failed'
                todo['details'] = todo_result
                
                print(f"\n{'='*80}")
                print(f"TODO {todo['id']} {'✓ COMPLETED' if todo_result['success'] else '✗ FAILED'}")
                print(f"{'='*80}")
            
            # Check if all todos completed
            completed = sum(1 for t in analysis['todos'] if t['status'] == 'completed')
            print(f"\nRound {round_num} Summary:")
            print(f"  Todos completed: {completed}/{len(analysis['todos'])}")
            
            if completed == 0:
                print(f"\n⚠ No todos completed successfully")
                return {
                    'success': False,
                    'rounds': round_num,
                    'message': 'Failed to complete any fixes'
                }
        
        print(f"\n{'='*80}")
        print(f"MAX ROUNDS REACHED ({max_rounds})")
        print(f"{'='*80}")
        return {
            'success': False,
            'rounds': max_rounds,
            'message': 'Max rounds reached, may still have errors'
        }


async def main():
    """Main entry point."""
    import sys
    
    backend_path = os.path.join(os.path.dirname(__file__), "backend")
    
    if len(sys.argv) > 1:
        backend_path = sys.argv[1]
    
    debugger = BackendDebugger(backend_path)
    result = await debugger.debug_backend(duration=15, max_rounds=5)
    
    print(f"\n{'='*80}")
    print("FINAL RESULT")
    print(f"{'='*80}")
    print(f"Success: {result['success']}")
    print(f"Rounds: {result['rounds']}")
    print(f"Message: {result['message']}")


if __name__ == "__main__":
    asyncio.run(main())
