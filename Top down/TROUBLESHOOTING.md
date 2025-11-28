# Troubleshooting Guide

## Common Issues and Solutions

### 1. "npm/npx not found" Error

**Problem:** The system cannot find npm or npx commands.

**Solutions:**

#### Option A: Add npm to PATH (Recommended)
1. Find your Node.js installation folder (usually `C:\Program Files\nodejs\`)
2. Add it to your PATH environment variable:
   ```powershell
   # Check if npm is accessible
   npm --version
   
   # If not found, add to PATH temporarily
   $env:Path += ";C:\Program Files\nodejs\"
   
   # Or add permanently (run as Administrator)
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\nodejs\", "Machine")
   ```

#### Option B: Reinstall Node.js
1. Download from: https://nodejs.org/
2. Choose LTS version
3. During installation, check "Add to PATH"
4. Restart PowerShell/Terminal
5. Verify: `node --version && npm --version`

#### Option C: Use Full Path
Edit the script to use full path:
```python
# Instead of just "npm"
subprocess.run("C:\\Program Files\\nodejs\\npm.cmd install ...", ...)
```

### 2. Python Virtual Environment Issues

**Problem:** Failed to create or activate virtual environment.

**Solutions:**

```powershell
# Ensure Python is installed
python --version

# Create venv manually
cd backend
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# If execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt
```

### 3. Dependency Installation Failures

**Problem:** npm or pip fails to install dependencies.

**Frontend (React) - Manual Installation:**
```powershell
cd frontend
npm install
npm install react-router-dom axios
```

**Backend (Flask) - Manual Installation:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install Flask Flask-CORS Flask-SQLAlchemy Flask-JWT-Extended python-dotenv
```

### 4. "Command not found" in PowerShell

**Problem:** Commands work in CMD but not PowerShell.

**Solution:**
```powershell
# Use .cmd or .exe extension
npm.cmd install
npx.cmd create-react-app frontend

# Or switch to CMD
cmd
npm install
```

### 5. Permission Denied Errors

**Problem:** Cannot write files or create directories.

**Solutions:**
```powershell
# Run PowerShell as Administrator
# Or change directory permissions
icacls "C:\Users\ASUS\Desktop\Codes\POME\Top down" /grant Users:F /t
```

### 6. Port Already in Use

**Problem:** React (3000) or Flask (5000) port is occupied.

**Solutions:**

**Find and kill process using port:**
```powershell
# Find process on port 3000
netstat -ano | findstr :3000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Or use different ports:**

React:
```powershell
# In frontend directory
$env:PORT=3001
npm start
```

Flask:
```python
# In backend/app.py
app.run(host='0.0.0.0', port=5001, debug=True)
```

### 7. CORS Errors in Browser

**Problem:** Frontend cannot connect to backend API.

**Solution:**

Ensure Flask backend has CORS enabled:
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
```

### 8. Module Import Errors

**Problem:** Python cannot find installed modules.

**Solution:**
```powershell
# Ensure virtual environment is activated
cd backend
.\venv\Scripts\Activate.ps1

# Check Python is using venv
where python
# Should show: ...\backend\venv\Scripts\python.exe

# Reinstall if needed
pip install -r requirements.txt
```

### 9. React Build/Start Failures

**Problem:** `npm start` or `npm run build` fails.

**Solutions:**

```powershell
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install

# Update npm
npm install -g npm@latest
```

### 10. Worker Agents Not Implementing Code

**Problem:** Agents run but no code is generated.

**Checklist:**
1. Check logs in `/logs` directory for errors
2. Verify Groq API key in `.env` file
3. Ensure projects were generated first
4. Check project paths are correct
5. Look for rate limiting messages

**Solution:**
```powershell
# Check logs
Get-Content logs\frontend_agent_1_*.log
Get-Content logs\backend_agent_1_*.log

# Verify project structure
Test-Path frontend\src\pages
Test-Path backend\routes
```

## Quick Diagnostic Commands

Run these to diagnose issues:

```powershell
# Check all prerequisites
node --version
npm --version
python --version
pip --version

# Check environment
$env:Path
Get-Command npm
Get-Command python

# Test network (for npm/pip)
Test-NetConnection registry.npmjs.org -Port 443
Test-NetConnection pypi.org -Port 443

# Check Groq API
$env:GROQ_API_KEY
```

## Getting Help

If issues persist:

1. Check the logs in `/logs` directory
2. Run with verbose output
3. Check Node.js and Python are latest LTS versions
4. Ensure antivirus is not blocking
5. Try running PowerShell as Administrator

## Useful Resources

- Node.js Download: https://nodejs.org/
- Python Download: https://www.python.org/
- npm Documentation: https://docs.npmjs.com/
- Flask Documentation: https://flask.palletsprojects.com/
- React Documentation: https://react.dev/
