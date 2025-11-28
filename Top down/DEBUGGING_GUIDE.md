# Debugging Agents Guide

## Overview

The debugging agents automatically start your React and Flask projects and monitor them for errors in real-time. They use AI (LLM) to analyze any issues found and suggest fixes.

## How to Use

### Option 1: Through Main Workflow

Run the complete workflow:
```powershell
python main.py
```

After worker agents complete implementation, you'll be asked:
```
Would you like to start the projects and run debugging agents? (yes/no):
```

Type `yes` to automatically:
1. Start React dev server (port 3000)
2. Start Flask backend (port 5000)
3. Deploy frontend debugging agent
4. Deploy backend debugging agent
5. Monitor both for errors
6. Generate debugging report

### Option 2: Standalone Script

If you've already generated projects:
```powershell
python start_and_debug.py
```

This assumes:
- `frontend/` directory exists with React project
- `backend/` directory exists with Flask project
- Both projects are ready to run

## What the Debuggers Do

### Frontend Debugger

**Startup:**
- Runs `npm start` in the React project directory
- Waits 30 seconds for server to initialize
- Checks if process is still running

**Error Detection:**
- Monitors for compilation errors
- Checks for common React issues (import syntax, etc.)
- Reads recent stderr output for error messages

**Analysis:**
- Uses LLM to analyze errors
- Provides explanation of the problem
- Suggests specific fixes
- Logs all activity

### Backend Debugger

**Startup:**
- Activates virtual environment
- Runs `python app.py` in the Flask project directory
- Waits 10 seconds for server to initialize
- Checks if process is still running

**Error Detection:**
- Compiles all Python files to check for syntax errors
- Monitors for server crashes
- Checks stderr for error messages
- Skips venv and __pycache__ directories

**Analysis:**
- Uses LLM to analyze errors
- Provides explanation of the problem
- Suggests specific fixes with code
- Logs all activity

## Output Files

All debugging output is saved to the `logs/` directory:

### Individual Agent Logs
- `frontend_debugger_YYYYMMDD_HHMMSS.log` - Frontend debugger activity
- `backend_debugger_YYYYMMDD_HHMMSS.log` - Backend debugger activity

### Debugging Report
- `debugging_report_YYYYMMDD_HHMMSS.json` - Summary JSON report

Example report:
```json
{
  "timestamp": "20250108_143022",
  "frontend": {
    "project_path": "C:\\...\\frontend",
    "running": true,
    "errors_found": 2,
    "fixes_applied": 2,
    "log_file": "logs/frontend_debugger_20250108_143022.log"
  },
  "backend": {
    "project_path": "C:\\...\\backend",
    "running": true,
    "errors_found": 0,
    "fixes_applied": 0,
    "log_file": "logs/backend_debugger_20250108_143022.log"
  }
}
```

## Console Output

The debuggers provide clear console output:

```
======================================================================
DEPLOYING DEBUGGING AGENTS
======================================================================

[Phase 1] Starting projects...

  Starting backend...
======================================================================
BACKEND DEBUGGER - Starting Project
======================================================================
Project path: C:\...\backend
Port: 5000

[1/2] Starting Flask server...
  Python: C:\...\backend\venv\Scripts\python.exe
  App: C:\...\backend\app.py
  Process started (PID: 12345)
  Waiting for server to start (10 seconds)...
✓ Server appears to be running

  Starting frontend...
======================================================================
FRONTEND DEBUGGER - Starting Project
======================================================================
Project path: C:\...\frontend
Port: 3000

[1/2] Starting npm development server...
  Process started (PID: 12346)
  Waiting for server to start (30 seconds)...
✓ Server appears to be running

[Phase 2] Running diagnostics...

[2/2] Checking for errors...
  ✓ No errors detected

[Phase 3] Analyzing issues...

  Backend: ✓ No issues found
  Frontend: ✓ No issues found

======================================================================
DEBUGGING SUMMARY
======================================================================

Backend:
  Status: ✓ Running
  Errors found: 0
  Fixes suggested: 0
  Log: logs/backend_debugger_20250108_143022.log

Frontend:
  Status: ✓ Running
  Errors found: 0
  Fixes suggested: 0
  Log: logs/frontend_debugger_20250108_143022.log

Report: logs/debugging_report_20250108_143022.json

======================================================================
PROJECTS ARE RUNNING
======================================================================

Frontend: http://localhost:3000
Backend: http://localhost:5000

Press Ctrl+C to stop servers...
```

## Error Handling

### When Servers Fail to Start

If a server fails to start, the debugger will:
1. Capture stdout and stderr
2. Log the error details (first 1000 characters)
3. Continue with the other server
4. Report the failure in the summary

### When Errors Are Found

If errors are detected, the debugger will:
1. Identify the error type (syntax, crash, compilation, etc.)
2. Send error details to LLM for analysis
3. Get explanation and fix suggestion
4. Log the suggested fix
5. Add to the debugging report

**Note:** The debuggers suggest fixes but do NOT automatically apply them. You need to review and apply fixes manually.

## Stopping the Debuggers

Press `Ctrl+C` in the terminal to stop both servers.

The debuggers will:
1. Catch the keyboard interrupt
2. Terminate both processes gracefully
3. Print "Servers stopped"
4. Exit cleanly

## Troubleshooting

### Frontend Won't Start
- Check if npm is installed: `npm --version`
- Check if dependencies are installed: `cd frontend; npm install`
- Check for port conflicts: Port 3000 might be in use
- Check the frontend debugger log in `/logs`

### Backend Won't Start
- Check if Python is available: `python --version`
- Check if virtual environment exists: `backend/venv/`
- Check if dependencies are installed: `cd backend; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt`
- Check for port conflicts: Port 5000 might be in use
- Check the backend debugger log in `/logs`

### Debuggers Report False Positives
- Review the individual log files for details
- LLM might misinterpret warnings as errors
- Check if projects actually run in browser/API client

### Need More Detail
- Check individual debugger logs in `/logs` directory
- Logs contain full error messages and analysis
- Logs show timestamp for each operation

## Best Practices

1. **Run After Implementation:** Use debugging agents after worker agents finish implementation
2. **Check Logs:** Always review the individual logs for detailed error info
3. **Manual Fixes:** Apply suggested fixes manually after reviewing them
4. **Re-run After Fixes:** Run `python start_and_debug.py` again after applying fixes
5. **Keep Logs:** Debugging reports are timestamped - you can compare before/after

## Advanced Usage

### Customize Ports

Edit `debugging_agents.py`:
```python
class FrontendDebugger(ProjectDebugger):
    def __init__(self, project_path: str):
        super().__init__(project_path, "frontend", "FE-DEBUG-1")
        self.port = 3000  # Change this

class BackendDebugger(ProjectDebugger):
    def __init__(self, project_path: str):
        super().__init__(project_path, "backend", "BE-DEBUG-1")
        self.port = 5000  # Change this
```

### Customize Wait Times

Edit startup functions:
```python
# Frontend - wait 30 seconds
time.sleep(30)  # Change this

# Backend - wait 10 seconds
time.sleep(10)  # Change this
```

### Add More Error Checks

Extend the `check_errors()` methods in `debugging_agents.py` to add custom error detection logic.
