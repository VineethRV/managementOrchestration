# Application Design & Generation System

🤖 Multi-agent system that automatically designs frontend pages and backend APIs from requirements, then generates complete **React** and **Flask** projects, **implements them with AI worker agents**, and **auto-starts with debugging agents**!

## ✨ Key Features

- 💬 **Interactive Requirements Gathering** - Chat with AI to define your app
- 🎨 **Automatic Frontend Design** - AI designs all pages with UI requirements
- 🔌 **Automatic Backend Design** - AI creates complete REST API specifications
- ⚛️ **React Project Generation** - Creates complete React app with all pages
- 🐍 **Flask Backend Generation** - Creates Flask API with all endpoints
- 🤖 **AI Worker Agents** - 3 frontend + 3 backend agents implement production-quality code
- 📊 **Intelligent Work Distribution** - Pages grouped by similarity, endpoints by resource
- 🐛 **Auto-Start & Debug** - Automatically starts both projects and deploys debugging agents
- 🔍 **Real-Time Error Detection** - AI agents monitor, detect, and suggest fixes for issues
- 🚀 **Ready to Run** - Fully implemented projects with database, API calls, error handling!

## Files

- `finalizer.py` - Requirements gathering agent (interactive chat)
- `frontend_backend_managers.py` - Frontend & backend design agents with logging
- `project_generator.py` - React & Flask project generator
- `worker_agents.py` - 3 frontend + 3 backend AI worker agents for implementation
- `debugging_agents.py` - Frontend & backend debugging agents (monitors running projects)
- `main.py` - Complete workflow orchestration
- `start_and_debug.py` - Standalone script to start and debug existing projects
- `logs/` - All agent interactions, stage outputs, and session logs

## How It Works

### Multi-Stage Pipeline

1. **Requirements Agent** (finalizer.py)
   - Interactive chat to gather requirements
   - Confirms detailed description and features
   - Finalizes requirements for design phase

2. **Design Agents** (frontend_backend_managers.py)
   - **Stage 1:** Frontend Agent lists all pages needed
   - **Stage 2:** Frontend Agent adds UI requirements to each page
   - **Stage 3:** Frontend Agent identifies endpoints for each page
   - **Stage 3.5:** System deduplicates endpoints (removes duplicates)
   - **Stage 4:** Backend Agent creates API specifications (batched by resource)
   - All interactions logged to `/logs` directory

3. **Project Generator** (project_generator.py)
   - **React Frontend:** Creates complete React app with all pages
   - **Flask Backend:** Creates Flask API with all endpoints
   - Sets up project structure, routing, dependencies

4. **Worker Agents** (worker_agents.py)
   - **3 Frontend Agents:** Implement React components in parallel
   - **3 Backend Agents:** Implement Flask endpoints in parallel
   - **Smart Grouping:** Pages grouped by similarity, endpoints by resource
   - **Production Quality:** Complete code with error handling, validation, database logic
   - **Database Setup:** Auto-generates SQLAlchemy models
   - **Independent Work:** Agents work in parallel, merge at completion

5. **Debugging Agents** (debugging_agents.py) - **NEW!**
   - **Frontend Debugger:** Monitors React dev server, detects compilation/runtime errors
   - **Backend Debugger:** Monitors Flask server, detects Python errors and crashes
   - **Auto-Start:** Automatically starts both projects
   - **Real-Time Analysis:** LLM analyzes errors and suggests fixes
   - **Comprehensive Logging:** Saves all debugging activity to logs
   - **Error Reports:** Generates JSON reports with found issues and suggested solutions

6. **Orchestrator** (main.py)
   - Runs requirements gathering
   - Triggers design workflow
   - Generates project scaffolding
   - Deploys worker agents for implementation
   - Auto-starts projects and debugging agents
   - Saves all outputs and logs

7. **Resume Script** (resume.py)
   - Detects current project state automatically
   - Resumes from where you left off
   - Skips completed steps
   - Can recover from interruptions
   - Works with any saved design in logs

## Usage

### Full Workflow (First Time)

```powershell
# Activate virtual environment
.\myenv\Scripts\Activate.ps1

# Run the complete workflow
python main.py
```

### Resume from Interruption

```powershell
# Check current status
python resume.py --status

# Resume building from where you left off
python resume.py
```

The resume script will:
- ✅ Detect what's already completed
- ✅ Skip finished steps automatically  
- ✅ Continue from project generation or implementation
- ✅ Use latest design from logs

### Full Workflow Steps

Running `python main.py` will:
1. Start interactive requirements chat
2. Automatically design pages and APIs after finalization
3. Save output to `application_design.json` and `/logs`
4. **Ask if you want to generate projects**
5. If yes, create React frontend and Flask backend scaffolding
6. **Ask if you want AI agents to implement the code**
7. If yes, deploy 3 frontend + 3 backend worker agents
8. Agents implement production-quality code in parallel
9. **Ask if you want to start projects and run debugging agents**
10. If yes, auto-start both servers and deploy 2 debugging agents
11. Debugging agents monitor for errors and suggest fixes
12. Projects run until you press Ctrl+C

### Start & Debug Existing Projects

If you've already generated and implemented projects:

```powershell
# Start both projects with debugging agents
python start_and_debug.py
```

This will:
- ✅ Start React dev server on port 3000
- ✅ Start Flask backend on port 5000
- ✅ Deploy frontend debugging agent
- ✅ Deploy backend debugging agent
- ✅ Monitor for errors and suggest fixes
- ✅ Generate debugging report in `/logs`
- ✅ Keep servers running until Ctrl+C

## Resume Scenarios

The resume script handles these situations:

**Scenario 1: Interrupted During Project Generation**
- Design is complete but no projects created
- Resume will: Generate React and Flask projects → Deploy workers

**Scenario 2: Projects Created, Not Implemented**
- Frontend and backend scaffolding exists
- Resume will: Skip generation → Deploy worker agents directly

**Scenario 3: Partially Implemented**
- Some agents completed, some failed
- Resume will: Check implementation status → Re-run only failed parts

**Scenario 4: Fully Complete**
- Everything is done
- Resume will: Show status → Provide run instructions

**Status Check Examples:**
```powershell
# Quick status check
python resume.py --status

# Output shows:
# ✅ Design phase
# ✅ Frontend scaffolding
# ✅ Backend scaffolding
# ❌ Frontend implementation  ← Need to resume here
# ❌ Backend implementation
```

## Generated & Implemented Projects

### React Frontend (`frontend/`)
**Scaffolding (Project Generator):**
- ✅ Complete React app with Create React App
- ✅ React Router configured with all pages
- ✅ Navigation menu
- ✅ CSS styling structure

**Implementation (Worker Agents):**
- ✅ Production-quality React components
- ✅ Complete API integration with axios
- ✅ Error handling and loading states
- ✅ Form validation
- ✅ Proper React hooks usage
- ✅ Accessibility attributes
- ✅ Ready to run with `npm start`

### Flask Backend (`backend/`)
**Scaffolding (Project Generator):**
- ✅ Complete Flask API structure
- ✅ CORS configured for React frontend
- ✅ Virtual environment setup
- ✅ Requirements.txt with dependencies

**Implementation (Worker Agents):**
- ✅ Production-quality Flask routes
- ✅ SQLAlchemy models with relationships
- ✅ Database setup and migrations
- ✅ Input validation and error handling
- ✅ Proper HTTP status codes
- ✅ JWT authentication (if needed)
- ✅ Database transactions
- ✅ Ready to run with `python app.py`

### Worker Agent Features

**Frontend Agents (3 agents):**
- Implement React components in parallel
- Pages grouped by similarity/functionality
- Complete API integration with error handling
- Loading states and user feedback
- Form validation and edge case handling

**Backend Agents (3 agents):**
- Implement Flask endpoints in parallel
- Endpoints grouped by resource (/api/users, /api/products, etc.)
- Complete database models and relationships
- Input validation and error handling
- External API integration if needed

**Logging & Tracking:**
- Each agent logs to separate file in `/logs`
- Implementation summary with success/error counts
- Full code generation history preserved

## Debugging Agents

The debugging agents automatically start your projects and monitor them for issues:

### What They Do

**Frontend Debugger:**
- Starts React dev server (`npm start`)
- Waits for server to initialize
- Monitors for compilation errors
- Checks for runtime errors in code
- Analyzes error output with LLM
- Suggests fixes for detected issues
- Logs all activity to `/logs/frontend_debugger_*.log`

**Backend Debugger:**
- Starts Flask server in virtual environment
- Waits for server to initialize
- Monitors for Python syntax errors
- Checks for crashes and exceptions
- Compiles all Python files to check validity
- Analyzes errors with LLM
- Suggests fixes for detected issues
- Logs all activity to `/logs/backend_debugger_*.log`

### Debugging Output

After running, you'll get:
- **Console Summary:** Issues found, fixes suggested, server status
- **Individual Logs:** Detailed logs for each debugger
- **Debugging Report:** JSON report at `/logs/debugging_report_*.json`

Example report structure:
```json
{
  "timestamp": "20250108_143022",
  "frontend": {
    "running": true,
    "errors_found": 1,
    "fixes_applied": 1,
    "log_file": "logs/frontend_debugger_20250108_143022.log"
  },
  "backend": {
    "running": true,
    "errors_found": 0,
    "fixes_applied": 0,
    "log_file": "logs/backend_debugger_20250108_143022.log"
  }
}
```

## Project Structure After Generation

```
Top down/
├── frontend/                    # React project
│   ├── src/
│   │   ├── pages/              # All page components
│   │   ├── App.js              # Routing configured
│   │   └── App.css
│   ├── package.json
│   └── FRONTEND_README.md
│
├── backend/                     # Flask project
│   ├── venv/                   # Virtual environment
│   ├── app.py                  # All API endpoints
│   ├── requirements.txt
│   ├── .env
│   └── BACKEND_README.md
│
├── logs/                        # All logs
│   ├── frontend_debugger_*.log
│   ├── backend_debugger_*.log
│   └── debugging_report_*.json
│
├── application_design.json      # Complete design spec
├── finalizer.py
├── frontend_backend_managers.py
├── project_generator.py
├── worker_agents.py
├── debugging_agents.py
├── start_and_debug.py
└── main.py
```

## Running Generated Projects

### Start Backend (Terminal 1):
```bash
cd backend
venv\Scripts\activate           # Windows
# source venv/bin/activate      # Mac/Linux
pip install -r requirements.txt
python app.py
```
Backend will run at http://localhost:5000

### Start Frontend (Terminal 2):
```bash
cd frontend
npm install                     # First time only
npm start
```
Frontend will run at http://localhost:3000

## Requirements

- Python 3.8+
- Node.js and npm (for React project generation)
- Virtual environment with dependencies
- `.env` file with `GROQ_API_KEY`

## Benefits

✅ **End-to-End Automation** - From chat to running projects  
✅ **Iterative Design** - 4-stage pipeline for better quality  
✅ **Complete Projects** - React + Flask ready to run  
✅ **Production Structure** - Best practices followed  
✅ **Comprehensive** - All pages and endpoints implemented  
✅ **Reliable** - Simple prompts per stage, high success rate  
✅ **Transparent** - Progress tracking at each stage  
✅ **Time Saving** - Skip hours of boilerplate setup
