"""
Kaizen Runtime Debugger: Integrates runtime error detection and fixing into PDCA cycles.
Adapted from Top down approach but designed specifically for Kaizen methodology.

Key differences from Top down:
- Integrates with defect ledger
- Uses Kaizen rate limiting
- Works within PDCA CHECK and ACT phases
- Focuses on continuous improvement rather than one-time fixes
- Tracks fixes as defect resolutions
"""

import os
import time
import subprocess
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Import Kaizen modules
from defect_ledger import DefectLedger, DefectSeverity, DefectStatus
from rate_limiter import RateLimiter
from kaizen_orchestrator import get_agent, invoke_with_rate_limit, log_and_print

load_dotenv()


class KaizenRuntimeDebugger:
    """
    Runtime debugger for Kaizen projects.
    Detects runtime errors and integrates fixes into the PDCA cycle.
    """
    
    def __init__(self, react_path: str, flask_path: str, defect_ledger: DefectLedger, 
                 rate_limiter: RateLimiter, log_file: str = None):
        self.react_path = react_path
        self.flask_path = flask_path
        self.defect_ledger = defect_ledger
        self.rate_limiter = rate_limiter
        self.log_file = log_file
        
        # Process tracking
        self.frontend_process = None
        self.backend_process = None
        
        # Fix tracking
        self.fixes_applied = []
        self.errors_detected = []
        
        # Ports
        self.frontend_port = 3000
        self.backend_port = 5000
    
    def start_projects(self) -> Dict[str, bool]:
        """Start both frontend and backend projects."""
        log_and_print("\n[Kaizen Debugger] Starting projects for runtime testing...", self.log_file)
        
        results = {"frontend": False, "backend": False}
        
        # Start backend first
        log_and_print("  [Backend] Starting Flask server...", self.log_file)
        self.backend_process = self._start_backend()
        results["backend"] = self.backend_process is not None
        
        # Wait a bit for backend to start
        if results["backend"]:
            time.sleep(5)
        
        # Start frontend
        log_and_print("  [Frontend] Starting Vite dev server...", self.log_file)
        self.frontend_process = self._start_frontend()
        results["frontend"] = self.frontend_process is not None
        
        # Wait for frontend to start
        if results["frontend"]:
            time.sleep(10)  # Vite needs more time
        
        return results
    
    def _start_backend(self) -> Optional[subprocess.Popen]:
        """Start Flask backend server."""
        try:
            # Determine Python executable
            if os.name == 'nt':  # Windows
                python_exe = os.path.join(self.flask_path, "venv", "Scripts", "python.exe")
            else:  # Unix
                python_exe = os.path.join(self.flask_path, "venv", "bin", "python")
            
            if not os.path.exists(python_exe):
                log_and_print(f"    ⚠ Virtual environment not found, using system Python", self.log_file)
                python_exe = "python"
            
            app_py = os.path.join(self.flask_path, "app.py")
            
            process = subprocess.Popen(
                f'"{python_exe}" "{app_py}"',
                shell=True,
                cwd=self.flask_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            log_and_print(f"    ✓ Backend process started (PID: {process.pid})", self.log_file)
            return process
            
        except Exception as e:
            log_and_print(f"    ✗ Failed to start backend: {e}", self.log_file)
            return None
    
    def _start_frontend(self) -> Optional[subprocess.Popen]:
        """Start Vite frontend server."""
        try:
            process = subprocess.Popen(
                "npm run dev",
                shell=True,
                cwd=self.react_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            log_and_print(f"    ✓ Frontend process started (PID: {process.pid})", self.log_file)
            return process
            
        except Exception as e:
            log_and_print(f"    ✗ Failed to start frontend: {e}", self.log_file)
            return None
    
    def check_runtime_errors(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Check for runtime errors in both projects.
        Returns errors categorized by component.
        """
        log_and_print("\n[Kaizen Debugger] Checking for runtime errors...", self.log_file)
        
        errors = {"frontend": [], "backend": []}
        
        # Check backend
        if self.backend_process:
            backend_errors = self._check_backend_errors()
            errors["backend"] = backend_errors
            if backend_errors:
                log_and_print(f"  [Backend] Found {len(backend_errors)} runtime errors", self.log_file)
            else:
                log_and_print(f"  [Backend] ✓ No runtime errors detected", self.log_file)
        
        # Check frontend
        if self.frontend_process:
            frontend_errors = self._check_frontend_errors()
            errors["frontend"] = frontend_errors
            if frontend_errors:
                log_and_print(f"  [Frontend] Found {len(frontend_errors)} runtime errors", self.log_file)
            else:
                log_and_print(f"  [Frontend] ✓ No runtime errors detected", self.log_file)
        
        self.errors_detected.extend(errors["frontend"] + errors["backend"])
        return errors
    
    def _check_backend_errors(self) -> List[Dict[str, Any]]:
        """Check for Python/Flask runtime errors."""
        errors = []
        
        if not self.backend_process:
            return errors
        
        try:
            # Check if process crashed
            if self.backend_process.poll() is not None:
                stdout, stderr = self.backend_process.communicate()
                error_output = stderr if stderr else stdout
                
                if error_output:
                    error_details = self._parse_python_error(error_output)
                    if error_details:
                        errors.append(error_details)
                    else:
                        # Fallback for unparseable errors
                        errors.append({
                            "type": "runtime_crash",
                            "component": "backend",
                            "message": "Backend server crashed",
                            "details": error_output[-2000:],
                            "severity": DefectSeverity.CRITICAL.value
                        })
        
        except Exception as e:
            log_and_print(f"    ✗ Error checking backend: {e}", self.log_file)
        
        return errors
    
    def _check_frontend_errors(self) -> List[Dict[str, Any]]:
        """Check for React/Vite runtime errors."""
        errors = []
        
        if not self.frontend_process:
            return errors
        
        try:
            # Check if process crashed
            if self.frontend_process.poll() is not None:
                stdout, stderr = self.frontend_process.communicate()
                error_output = stderr if stderr else stdout
                
                if error_output:
                    error_details = self._parse_react_error(error_output)
                    if error_details:
                        errors.append(error_details)
                    else:
                        # Fallback for unparseable errors
                        errors.append({
                            "type": "runtime_crash",
                            "component": "frontend",
                            "message": "Frontend server crashed",
                            "details": error_output[-2000:],
                            "severity": DefectSeverity.CRITICAL.value
                        })
        
        except Exception as e:
            log_and_print(f"    ✗ Error checking frontend: {e}", self.log_file)
        
        return errors
    
    def _parse_python_error(self, error_output: str) -> Optional[Dict[str, Any]]:
        """Parse Python traceback to extract error details."""
        # Look for: File "path", line N
        file_pattern = r'File "([^"]+)", line (\d+)'
        error_pattern = r'(\w+Error): (.+?)(?:\n|$)'
        
        file_match = re.search(file_pattern, error_output)
        error_match = re.search(error_pattern, error_output)
        
        if file_match and error_match:
            file_path = file_match.group(1)
            line_num = int(file_match.group(2))
            error_type = error_match.group(1)
            error_msg = error_match.group(2).strip()
            
            # Convert to absolute path if needed
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.flask_path, file_path)
            
            # Determine severity
            severity = DefectSeverity.HIGH.value
            if "ImportError" in error_type or "ModuleNotFoundError" in error_type:
                severity = DefectSeverity.CRITICAL.value
            elif "SyntaxError" in error_type:
                severity = DefectSeverity.CRITICAL.value
            
            return {
                "type": error_type.lower().replace('error', ''),
                "component": "backend",
                "file": file_path,
                "line": line_num,
                "message": f"{error_type}: {error_msg}",
                "details": error_output[-2000:],
                "severity": severity
            }
        
        return None
    
    def _parse_react_error(self, error_output: str) -> Optional[Dict[str, Any]]:
        """Parse React/Vite error output."""
        # React errors: ./src/App.jsx or src/App.jsx
        file_pattern = r'(?:\.\/)?src[\/\\][\w\/\\.-]+\.(?:js|jsx|ts|tsx)'
        line_pattern = r'Line (\d+):|line (\d+)|:(\d+):\d+'
        error_pattern = r'(SyntaxError|TypeError|ReferenceError|Error): (.+?)(?:\n|$)'
        
        file_match = re.search(file_pattern, error_output)
        line_match = re.search(line_pattern, error_output)
        error_match = re.search(error_pattern, error_output)
        
        if file_match:
            file_path = file_match.group(0)
            if file_path.startswith('./'):
                file_path = file_path[2:]
            file_path = os.path.join(self.react_path, file_path)
            
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
            
            # Determine severity
            severity = DefectSeverity.HIGH.value
            if "SyntaxError" in error_msg or "Failed to compile" in error_msg:
                severity = DefectSeverity.CRITICAL.value
            
            result = {
                "type": error_type,
                "component": "frontend",
                "file": file_path,
                "message": error_msg,
                "details": error_output[-2000:],
                "severity": severity
            }
            
            if line_num:
                result["line"] = line_num
            
            return result
        
        return None
    
    def record_errors_to_ledger(self, errors: Dict[str, List[Dict[str, Any]]]):
        """
        Record detected runtime errors to the defect ledger.
        This integrates runtime debugging into Kaizen's defect tracking.
        """
        if not self.defect_ledger:
            return
        
        total_recorded = 0
        
        for component, component_errors in errors.items():
            for error in component_errors:
                # Create defect description
                description = f"Runtime error: {error.get('message', 'Unknown error')}"
                if error.get('file'):
                    description += f" in {os.path.basename(error.get('file'))}"
                if error.get('line'):
                    description += f" at line {error.get('line')}"
                
                # Determine component path for ledger
                component_path = f"{component}/{os.path.basename(error.get('file', 'unknown'))}"
                
                # Get severity
                severity_str = error.get('severity', DefectSeverity.HIGH.value)
                try:
                    severity = DefectSeverity[severity_str.upper()]
                except:
                    severity = DefectSeverity.HIGH
                
                # Add to ledger
                defect_id = self.defect_ledger.add_defect(
                    description=description,
                    component=component_path,
                    severity=severity,
                    category="runtime_error",
                    metadata={
                        "error_type": error.get('type'),
                        "file": error.get('file'),
                        "line": error.get('line'),
                        "details": error.get('details', '')[:500]  # Truncate for storage
                    }
                )
                
                total_recorded += 1
        
        if total_recorded > 0:
            log_and_print(f"  [Defect Ledger] Recorded {total_recorded} runtime errors as defects", self.log_file)
    
    async def fix_runtime_error(self, error: Dict[str, Any]) -> bool:
        """
        Use Kaizen's approach to fix a runtime error.
        Integrates with rate limiting and defect ledger.
        """
        error_type = error.get('type', 'unknown')
        component = error.get('component', 'unknown')
        file_path = error.get('file')
        line_num = error.get('line')
        
        log_and_print(f"\n  [Kaizen Fix] Attempting to fix {error_type} error in {component}", self.log_file)
        
        # Check token budget
        remaining_tokens = self.rate_limiter.get_remaining_daily_tokens()
        if remaining_tokens < 3000:
            log_and_print(f"    ⚠ Insufficient tokens for fix ({remaining_tokens} remaining)", self.log_file)
            return False
        
        try:
            # Stage 1: Analyze error (using Kaizen's agent system)
            analysis_prompt = f"""You are a debugging expert in the Kaizen continuous improvement system.
Analyze this runtime error and provide a concise analysis.

Error Type: {error_type}
Component: {component}
File: {os.path.basename(file_path) if file_path else 'N/A'}
Line: {line_num if line_num else 'N/A'}
Message: {error.get('message', 'N/A')}
Details: {error.get('details', 'N/A')[:500]}

Provide a brief analysis:
1. What is the root cause?
2. What needs to be fixed?
3. Is this a critical issue that blocks functionality?

Keep your analysis concise (2-3 sentences)."""
            
            agent = get_agent(temperature=0.2, max_tokens=1000)
            analysis_response = invoke_with_rate_limit(
                agent, 
                [HumanMessage(content=analysis_prompt)], 
                self.log_file,
                estimated_tokens=800
            )
            
            if not analysis_response:
                log_and_print(f"    ✗ Failed to analyze error (token limit or API error)", self.log_file)
                return False
            
            analysis = analysis_response.content.strip()
            log_and_print(f"    Analysis: {analysis[:200]}...", self.log_file)
            
            # Stage 2: Generate fix steps
            steps_prompt = f"""Based on this error analysis, provide the fix steps.

Error: {error.get('message')}
Analysis: {analysis}
File: {file_path or 'N/A'}

Provide 1-3 specific steps to fix this error. Each step should be:
- A specific action (modify code, install package, fix import, etc.)
- Clear and actionable

Format:
1. STEP_TYPE: Description
2. STEP_TYPE: Description

STEP_TYPE can be: MODIFY_FILE or FILESYSTEM"""
            
            steps_response = invoke_with_rate_limit(
                agent,
                [HumanMessage(content=steps_prompt)],
                self.log_file,
                estimated_tokens=1000
            )
            
            if not steps_response:
                return False
            
            steps_text = steps_response.content.strip()
            
            # Parse and execute steps
            step_lines = [line.strip() for line in steps_text.split('\n') if re.match(r'^\d+\.', line.strip())]
            
            if not step_lines:
                log_and_print(f"    ✗ No actionable steps found", self.log_file)
                return False
            
            log_and_print(f"    Found {len(step_lines)} fix steps", self.log_file)
            
            # Execute steps
            steps_executed = 0
            for i, step_line in enumerate(step_lines[:3], 1):  # Limit to 3 steps per error
                log_and_print(f"    [Step {i}] {step_line[:100]}", self.log_file)
                
                # Determine step type
                if "MODIFY_FILE" in step_line.upper() or "MODIFY" in step_line.upper():
                    # File modification
                    if file_path and os.path.exists(file_path):
                        fix_instruction = f"""Fix this runtime error:

{error.get('message')}
Step: {step_line}
Analysis: {analysis}

Make the necessary code changes to resolve this issue."""
                        
                        result = await self._edit_file_chunked(file_path, fix_instruction, line_num)
                        if result.get('success'):
                            steps_executed += 1
                            log_and_print(f"      ✓ Modified {os.path.basename(file_path)}", self.log_file)
                        else:
                            log_and_print(f"      ✗ Edit failed: {result.get('error', 'Unknown')}", self.log_file)
                    else:
                        log_and_print(f"      ✗ File not found: {file_path}", self.log_file)
                
                elif "FILESYSTEM" in step_line.upper() or "INSTALL" in step_line.upper() or "RUN" in step_line.upper():
                    # Filesystem operation
                    command_prompt = f"""Provide the exact command for this step:

Step: {step_line}
Project: {self.react_path if component == 'frontend' else self.flask_path}

Return ONLY the command, nothing else."""
                    
                    command_response = invoke_with_rate_limit(
                        agent,
                        [HumanMessage(content=command_prompt)],
                        self.log_file,
                        estimated_tokens=500
                    )
                    
                    if command_response:
                        command = command_response.content.strip().strip('`').strip('"').strip("'")
                        project_path = self.react_path if component == 'frontend' else self.flask_path
                        
                        try:
                            result = subprocess.run(
                                command,
                                shell=True,
                                cwd=project_path,
                                capture_output=True,
                                text=True,
                                timeout=60
                            )
                            
                            if result.returncode == 0:
                                steps_executed += 1
                                log_and_print(f"      ✓ Command succeeded", self.log_file)
                            else:
                                log_and_print(f"      ✗ Command failed: {result.stderr[:100]}", self.log_file)
                        except Exception as e:
                            log_and_print(f"      ✗ Command error: {e}", self.log_file)
            
            # Record fix result
            if steps_executed > 0:
                self.fixes_applied.append({
                    "error": error,
                    "steps_executed": steps_executed,
                    "total_steps": len(step_lines)
                })
                
                # Mark related defects as resolved
                if self.defect_ledger and file_path:
                    component_path = f"{component}/{os.path.basename(file_path)}"
                    open_defects = self.defect_ledger.get_open_defects()
                    for defect in open_defects:
                        if defect.get('component') == component_path and defect.get('category') == 'runtime_error':
                            self.defect_ledger.update_defect_status(
                                defect['id'],
                                DefectStatus.RESOLVED,
                                "Kaizen Runtime Debugger",
                                f"Fixed via {steps_executed} steps"
                            )
                
                log_and_print(f"    ✓ Fixed error ({steps_executed}/{len(step_lines)} steps)", self.log_file)
                return True
            else:
                log_and_print(f"    ✗ No steps could be executed", self.log_file)
                return False
        
        except Exception as e:
            log_and_print(f"    ✗ Fix failed: {e}", self.log_file)
            return False
    
    async def _edit_file_chunked(self, file_path: str, instructions: str, error_line: int = None) -> Dict[str, Any]:
        """
        Edit file using chunked approach (similar to Top down but integrated with Kaizen).
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            chunk_size = 50
            overlap = 10
            
            # Focus on error line if provided
            if error_line:
                start_line = max(0, error_line - chunk_size // 2)
                end_line = min(total_lines, error_line + chunk_size // 2)
            else:
                start_line = 0
                end_line = min(chunk_size, total_lines)
            
            # Extract chunk with overlap
            chunk_start = max(0, start_line - overlap)
            chunk_end = min(total_lines, end_line + overlap)
            chunk_lines = lines[chunk_start:chunk_end]
            chunk_content = ''.join(chunk_lines)
            
            # Create edit prompt
            edit_prompt = f"""You are editing a file to fix a runtime error. Here is the relevant section:

File: {os.path.basename(file_path)}
Lines {chunk_start + 1} to {chunk_end}:
```
{chunk_content}
```

Task: {instructions}

Provide ONLY the fixed code for this section, with no explanations or markdown.
Start your response with the fixed code immediately."""
            
            # Use Kaizen's agent system
            agent = get_agent(temperature=0.2, max_tokens=2000)
            response = invoke_with_rate_limit(
                agent,
                [HumanMessage(content=edit_prompt)],
                self.log_file,
                estimated_tokens=1500
            )
            
            if not response:
                return {"success": False, "error": "No response from agent"}
            
            fixed_chunk = response.content.strip()
            
            # Remove markdown code fences
            if fixed_chunk.startswith('```'):
                fixed_chunk = '\n'.join(fixed_chunk.split('\n')[1:-1])
            
            # Replace chunk in original lines
            fixed_lines = fixed_chunk.split('\n')
            new_lines = (
                lines[:start_line] +
                [line + '\n' if not line.endswith('\n') else line for line in fixed_lines] +
                lines[end_line:]
            )
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            return {"success": True, "lines_modified": end_line - start_line}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stop_projects(self):
        """Stop both running projects."""
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
            except:
                self.frontend_process.kill()
            self.frontend_process = None
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
            except:
                self.backend_process.kill()
            self.backend_process = None
        
        log_and_print("  [Kaizen Debugger] Stopped all projects", self.log_file)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get debugging summary."""
        return {
            "errors_detected": len(self.errors_detected),
            "fixes_applied": len(self.fixes_applied),
            "frontend_running": self.frontend_process is not None and self.frontend_process.poll() is None,
            "backend_running": self.backend_process is not None and self.backend_process.poll() is None
        }


async def run_kaizen_runtime_debugging_async(react_path: str, flask_path: str, defect_ledger: DefectLedger,
                                  rate_limiter: RateLimiter, log_file: str = None, max_iterations: int = 5) -> Dict[str, Any]:
    """
    Run Kaizen runtime debugging cycle (async version).
    Integrates with PDCA - this is the CHECK phase for runtime errors.
    
    Args:
        react_path: Path to React frontend
        flask_path: Path to Flask backend
        defect_ledger: Kaizen defect ledger
        rate_limiter: Kaizen rate limiter
        log_file: Log file path
        max_iterations: Maximum debugging iterations
    
    Returns:
        Summary of debugging session
    """
    log_and_print("\n" + "="*70, log_file)
    log_and_print("KAIZEN RUNTIME DEBUGGING - CHECK PHASE", log_file)
    log_and_print("="*70, log_file)
    
    debugger = KaizenRuntimeDebugger(react_path, flask_path, defect_ledger, rate_limiter, log_file)
    
    # Start projects
    start_results = debugger.start_projects()
    if not start_results["frontend"] and not start_results["backend"]:
        log_and_print("  ✗ Failed to start projects. Cannot proceed with runtime debugging.", log_file)
        return {"success": False, "reason": "projects_failed_to_start"}
    
    iteration = 1
    total_fixes = 0
    
    while iteration <= max_iterations:
        log_and_print(f"\n[Iteration {iteration}/{max_iterations}]", log_file)
        
        # Check for errors
        errors = debugger.check_runtime_errors()
        total_errors = len(errors["frontend"]) + len(errors["backend"])
        
        if total_errors == 0:
            log_and_print(f"  ✓ No runtime errors detected. Debugging complete.", log_file)
            break
        
        # Record errors to defect ledger
        debugger.record_errors_to_ledger(errors)
        
        log_and_print(f"  Found {total_errors} runtime errors", log_file)
        
        # Fix errors (limit to top 2 per component to save tokens)
        fixes_this_iteration = 0
        
        # Fix backend errors
        for error in errors["backend"][:2]:
            if await debugger.fix_runtime_error(error):
                fixes_this_iteration += 1
        
        # Fix frontend errors
        for error in errors["frontend"][:2]:
            if await debugger.fix_runtime_error(error):
                fixes_this_iteration += 1
        
        if fixes_this_iteration > 0:
            total_fixes += fixes_this_iteration
            log_and_print(f"  ✓ Applied {fixes_this_iteration} fixes. Restarting projects...", log_file)
            
            # Restart projects to test fixes
            debugger.stop_projects()
            time.sleep(2)
            debugger.start_projects()
            time.sleep(5)  # Wait for restart
        else:
            log_and_print(f"  ⚠ No fixes could be applied. Stopping to prevent infinite loop.", log_file)
            break
        
        iteration += 1
    
    # Final summary
    summary = debugger.get_summary()
    summary["iterations"] = iteration - 1
    summary["total_fixes"] = total_fixes
    
    log_and_print(f"\n[Kaizen Debugger Summary]", log_file)
    log_and_print(f"  Errors detected: {summary['errors_detected']}", log_file)
    log_and_print(f"  Fixes applied: {summary['total_fixes']}", log_file)
    log_and_print(f"  Iterations: {summary['iterations']}", log_file)
    
    # Stop projects
    debugger.stop_projects()
    
    return summary


def run_kaizen_runtime_debugging(react_path: str, flask_path: str, defect_ledger: DefectLedger,
                                  rate_limiter: RateLimiter, log_file: str = None, max_iterations: int = 5) -> Dict[str, Any]:
    """
    Synchronous wrapper for async runtime debugging.
    """
    import asyncio
    
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, we need to use a different approach
            # For now, just run synchronously without async
            log_and_print("  [Runtime Debugging] Running in sync mode (event loop already running)", log_file)
            return {"success": False, "reason": "async_not_available"}
    except RuntimeError:
        # No event loop, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(
            run_kaizen_runtime_debugging_async(react_path, flask_path, defect_ledger, rate_limiter, log_file, max_iterations)
        )
    except Exception as e:
        log_and_print(f"  [Runtime Debugging] Error: {e}", log_file)
        return {"success": False, "reason": str(e)}

