"""
Project generator for React frontend and Flask backend.
Creates actual project files based on design specifications.
"""

import os
import json
import subprocess
from typing import Dict, Any, List


def check_prerequisites():
    """Check if Node.js/npm and Python are installed."""
    issues = []
    
    # Check Node.js and npm
    try:
        result = subprocess.run(
            "node --version",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ Node.js: {result.stdout.strip()}")
        else:
            issues.append("Node.js not found")
    except:
        issues.append("Node.js not found")
    
    try:
        result = subprocess.run(
            "npm --version",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ npm: {result.stdout.strip()}")
        else:
            issues.append("npm not found")
    except:
        issues.append("npm not found")
    
    # Check Python
    try:
        result = subprocess.run(
            "python --version",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ Python: {result.stdout.strip()}")
        else:
            issues.append("Python not found")
    except:
        issues.append("Python not found")
    
    if issues:
        print("\n⚠ Missing prerequisites:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease install missing tools:")
        if "Node.js" in str(issues) or "npm" in str(issues):
            print("  Node.js & npm: https://nodejs.org/")
        if "Python" in str(issues):
            print("  Python: https://www.python.org/")
        return False
    
    return True


def sanitize_filename(name: str) -> str:
    """Convert page/component name to valid filename."""
    # Remove special characters and convert to PascalCase
    words = name.replace('-', ' ').replace('_', ' ').split()
    return ''.join(word.capitalize() for word in words)


def sanitize_route_name(name: str) -> str:
    """Convert page name to URL route."""
    # Convert to lowercase and replace spaces with hyphens
    return name.lower().replace(' ', '-').replace('_', '-')


def create_react_project(design: Dict[str, Any], project_name: str = "frontend"):
    """
    Create a React project with pages based on design.
    
    Args:
        design: Complete design dictionary with frontend/backend
        project_name: Name of the React project folder
    """
    # Setup logging
    from datetime import datetime
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"react_project_generation_{timestamp}.log")
    
    def log_print(msg: str, also_stdout=True):
        """Log to file and optionally print to console."""
        if also_stdout:
            print(msg)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    
    log_print("\n" + "="*70)
    log_print("CREATING REACT FRONTEND PROJECT")
    log_print("="*70)
    log_print(f"Timestamp: {timestamp}")
    log_print(f"Project name: {project_name}")
    log_print(f"Log file: {log_file}")
    
    pages = design['frontend']['pages']
    log_print(f"Total pages to create: {len(pages)}")
    
    # Step 1: Create React app
    log_print(f"\n[1/5] Creating React app '{project_name}'...")
    log_print("  This may take a few minutes...")
    
    # Check if project directory already exists
    if os.path.exists(project_name):
        log_print(f"⚠ Warning: Directory '{project_name}' already exists")
        log_print(f"  Skipping project creation")
    else:
        # Use npx create-react-app (non-interactive and reliable)
        log_print(f"  Command: npx create-react-app {project_name}")
        
        try:
            log_print("  Executing command...")
            result = subprocess.run(
                f"npx create-react-app {project_name}",
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            log_print(f"  Return code: {result.returncode}")
            log_print(f"  stdout: {result.stdout[:500]}...")  # Log first 500 chars
            if result.stderr:
                log_print(f"  stderr: {result.stderr[:500]}...")
            log_print(f"✓ React app created successfully")
        except subprocess.CalledProcessError as e:
            log_print(f"✗ Failed to create React app.")
            log_print(f"  Error code: {e.returncode}")
            log_print(f"  stderr: {e.stderr[:500] if e.stderr else 'No stderr'}...")
            log_print(f"  stdout: {e.stdout[:500] if e.stdout else 'No stdout'}...")
            log_print("Please ensure Node.js and npm are installed.")
            log_print("Run: node --version && npm --version to verify.")
            return False
        except FileNotFoundError as e:
            log_print(f"✗ npm not found. FileNotFoundError: {str(e)}")
            log_print("Please install Node.js first.")
            log_print("Download from: https://nodejs.org/")
            return False
        except Exception as e:
            log_print(f"✗ Unexpected error: {str(e)}")
            return False
    
    # Step 2: Install dependencies
    log_print(f"\n[2/5] Installing dependencies (react-router-dom, axios)...")
    log_print(f"  Working directory: {os.path.abspath(project_name)}")
    log_print(f"  Command: npm install react-router-dom axios")
    
    try:
        log_print("  Executing npm install...")
        result = subprocess.run(
            "npm install react-router-dom axios",
            shell=True,
            cwd=project_name,
            check=True,
            capture_output=True,
            text=True
        )
        log_print(f"  Return code: {result.returncode}")
        log_print(f"  stdout: {result.stdout}")
        if result.stderr:
            log_print(f"  stderr: {result.stderr}")
        log_print(f"✓ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        log_print(f"⚠ Warning: Failed to install dependencies")
        log_print(f"  Error code: {e.returncode}")
        log_print(f"  stderr: {e.stderr if hasattr(e, 'stderr') and e.stderr else 'No stderr'}")
        log_print(f"  stdout: {e.stdout if hasattr(e, 'stdout') and e.stdout else 'No stdout'}")
        log_print(f"  You may need to run: cd {project_name} && npm install react-router-dom axios")
    except Exception as e:
        log_print(f"⚠ Unexpected error during npm install: {str(e)}")
    
    # Step 3: Create pages directory and page components
    log_print(f"\n[3/5] Creating page components...")
    pages_dir = os.path.join(project_name, "src", "pages")
    log_print(f"  Creating pages directory: {pages_dir}")
    
    try:
        os.makedirs(pages_dir, exist_ok=True)
        log_print(f"  ✓ Pages directory created")
    except Exception as e:
        log_print(f"  ✗ Failed to create pages directory: {str(e)}")
        return False
    
    for i, page in enumerate(pages, 1):
        page_name = page.get('page_name', f'Page{i}')
        component_name = sanitize_filename(page_name)
        description = page.get('description', '')
        requirements = page.get('requirements', [])
        endpoints = page.get('backend_endpoints', [])
        
        log_print(f"\n  [{i}/{len(pages)}] Creating component: {page_name}")
        log_print(f"    Component name: {component_name}")
        log_print(f"    Requirements: {len(requirements)}")
        log_print(f"    Endpoints: {len(endpoints)}")
        
        # Create component file
        requirements_comments = '\n'.join(f' * - {req}' for req in requirements)
        endpoints_comments = '\n'.join(f' * - {ep.get("method", "GET")} {ep.get("path", "")} - {ep.get("endpoint_name", "")}' for ep in endpoints)
        req_todos = '\n'.join(f'        {{/* {req} */}}' for req in requirements[:5])
        example_endpoint = endpoints[0].get("path", "") if endpoints else "/api/data"
        
        component_content = f'''import React, {{ useState, useEffect }} from 'react';
import './{component_name}.css';

/**
 * {page_name}
 * {description}
 * 
 * Requirements:
{requirements_comments}
 * 
 * Backend Endpoints:
{endpoints_comments}
 */
function {component_name}() {{
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {{
    // TODO: Fetch data from backend endpoints
    // Example:
    // fetch('http://localhost:5000{example_endpoint}')
    //   .then(response => response.json())
    //   .then(data => console.log(data))
    //   .catch(err => setError(err.message));
  }}, []);

  return (
    <div className="{component_name.lower()}-container">
      <h1>{page_name}</h1>
      <p>{description}</p>
      
      {{loading && <div className="loading">Loading...</div>}}
      {{error && <div className="error">Error: {{error}}</div>}}
      
      <div className="content">
        {{/* TODO: Implement page requirements */}}
{req_todos}
      </div>
    </div>
  );
}}

export default {component_name};
'''
        
        component_path = os.path.join(pages_dir, f"{component_name}.js")
        log_print(f"    Writing component file: {component_path}")
        
        try:
            with open(component_path, 'w', encoding='utf-8') as f:
                f.write(component_content)
            log_print(f"    ✓ Component file created ({len(component_content)} bytes)")
        except Exception as e:
            log_print(f"    ✗ Failed to write component file: {str(e)}")
            continue
        
        # Create CSS file
        css_content = f'''.{component_name.lower()}-container {{
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}}

.{component_name.lower()}-container h1 {{
  color: #333;
  margin-bottom: 10px;
}}

.{component_name.lower()}-container p {{
  color: #666;
  margin-bottom: 20px;
}}

.loading {{
  text-align: center;
  padding: 20px;
  color: #666;
}}

.error {{
  background-color: #fee;
  color: #c33;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 20px;
}}

.content {{
  background-color: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
}}
'''
        
        css_path = os.path.join(pages_dir, f"{component_name}.css")
        log_print(f"    Writing CSS file: {css_path}")
        
        try:
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(css_content)
            log_print(f"    ✓ CSS file created ({len(css_content)} bytes)")
            log_print(f"  ✓ Created {component_name}.js and {component_name}.css")
        except Exception as e:
            log_print(f"    ✗ Failed to write CSS file: {str(e)}")
    
    # Step 4: Create App.js with routing
    log_print(f"\n[4/5] Setting up routing in App.js...")
    log_print(f"  Generating imports for {len(pages)} pages")
    
    # Generate imports
    imports = '\n'.join(
        f"import {sanitize_filename(page.get('page_name', f'Page{i}'))} from './pages/{sanitize_filename(page.get('page_name', f'Page{i}'))}';"
        for i, page in enumerate(pages, 1)
    )
    
    # Generate navigation links
    nav_links = '\n'.join(
        f'            <li><Link to="/{sanitize_route_name(page.get("page_name", f"page{i}"))}">{page.get("page_name", f"Page {i}")}</Link></li>'
        for i, page in enumerate(pages, 1)
    )
    
    # Generate routes
    routes = '\n'.join(
        f'            <Route path="/{sanitize_route_name(page.get("page_name", f"page{i}"))}" element={{<{sanitize_filename(page.get("page_name", f"Page{i}"))} />}} />'
        for i, page in enumerate(pages, 1)
    )
    
    first_component = sanitize_filename(pages[0].get('page_name', 'Home'))
    
    app_js_content = f'''import React from 'react';
import {{ BrowserRouter as Router, Routes, Route, Link }} from 'react-router-dom';
import './App.css';

// Import all page components
{imports}

function App() {{
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <h2>Application Navigation</h2>
          <ul>
{nav_links}
          </ul>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={{<{first_component} />}} />
{routes}
          </Routes>
        </main>
      </div>
    </Router>
  );
}}

export default App;
'''
    
    app_js_path = os.path.join(project_name, "src", "App.js")
    log_print(f"  Writing App.js: {app_js_path}")
    log_print(f"  App.js size: {len(app_js_content)} bytes")
    
    try:
        with open(app_js_path, 'w', encoding='utf-8') as f:
            f.write(app_js_content)
        log_print(f"✓ Routing configured with {len(pages)} routes")
    except Exception as e:
        log_print(f"✗ Failed to write App.js: {str(e)}")
        return False
    
    # Step 5: Update App.css for better styling
    log_print(f"\n[5/5] Updating styles...")
    log_print(f"  Creating App.css")
    
    app_css_content = '''.App {
  min-height: 100vh;
  display: flex;
}

.navbar {
  width: 250px;
  background-color: #2c3e50;
  color: white;
  padding: 20px;
  min-height: 100vh;
}

.navbar h2 {
  margin-bottom: 20px;
  font-size: 1.2rem;
}

.navbar ul {
  list-style: none;
  padding: 0;
}

.navbar li {
  margin-bottom: 10px;
}

.navbar a {
  color: #ecf0f1;
  text-decoration: none;
  display: block;
  padding: 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.navbar a:hover {
  background-color: #34495e;
}

.main-content {
  flex: 1;
  padding: 20px;
  background-color: #ecf0f1;
}
'''
    
    app_css_path = os.path.join(project_name, "src", "App.css")
    log_print(f"  Writing App.css: {app_css_path}")
    
    try:
        with open(app_css_path, 'w', encoding='utf-8') as f:
            f.write(app_css_content)
        log_print(f"  App.css size: {len(app_css_content)} bytes")
        log_print(f"✓ Styles updated")
    except Exception as e:
        log_print(f"✗ Failed to write App.css: {str(e)}")
    
    # Create README for frontend
    log_print(f"\n[Finalization] Creating README...")
    pages_list = '\n'.join(
        f"{i}. **{page.get('page_name', f'Page {i}')}** - {page.get('description', 'No description')}"
        for i, page in enumerate(pages, 1)
    )
    
    readme_content = f'''# React Frontend

This project was automatically generated based on your application design.

## Pages Created

{pages_list}

## Getting Started

1. Navigate to the project directory:
   ```bash
   cd {project_name}
   ```

2. Install dependencies (if not already done):
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

## Backend Integration

The frontend is configured to communicate with the Flask backend at `http://localhost:5000`.
Make sure the backend is running before testing API integrations.

## Project Structure

```
{project_name}/
├── src/
│   ├── pages/          # All page components
│   ├── App.js          # Main app with routing
│   └── App.css         # Global styles
└── package.json
```

## Next Steps

- Implement the TODO comments in each page component
- Connect to backend API endpoints
- Add state management (Redux, Context API, etc.) if needed
- Implement authentication flows
- Add form validation
- Style components according to your design system
'''
    
    readme_path = os.path.join(project_name, "FRONTEND_README.md")
    log_print(f"  Writing README: {readme_path}")
    
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        log_print(f"  README size: {len(readme_content)} bytes")
        log_print(f"✓ README created")
    except Exception as e:
        log_print(f"✗ Failed to write README: {str(e)}")
    
    log_print("\n" + "="*70)
    log_print(f"✓ REACT PROJECT CREATED: ./{project_name}")
    log_print(f"✓ {len(pages)} page components created")
    log_print(f"✓ Routing configured")
    log_print(f"✓ Log file saved: {log_file}")
    log_print("="*70)
    
    return True


def create_flask_backend(design: Dict[str, Any], project_name: str = "backend"):
    """
    Create a Flask backend with API endpoints based on design.
    
    Args:
        design: Complete design dictionary with frontend/backend
        project_name: Name of the Flask project folder
    """
    print("\n" + "="*70)
    print("CREATING FLASK BACKEND PROJECT")
    print("="*70)
    
    endpoints = design['backend']['endpoints']
    
    # Step 1: Create project directory
    print(f"\n[1/5] Creating Flask project '{project_name}'...")
    os.makedirs(project_name, exist_ok=True)
    print(f"✓ Project directory created")
    
    # Step 2: Create virtual environment
    print(f"\n[2/5] Setting up virtual environment...")
    try:
        subprocess.run(
            ["python", "-m", "venv", "venv"],
            cwd=project_name,
            check=True,
            capture_output=True
        )
        print(f"✓ Virtual environment created")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create virtual environment: {e}")
    
    # Step 3: Create requirements.txt with all needed dependencies
    print(f"\n[3/5] Creating requirements.txt...")
    
    requirements_content = '''Flask==3.0.0
Flask-CORS==4.0.0
Flask-SQLAlchemy==3.1.1
Flask-JWT-Extended==4.6.0
python-dotenv==1.0.0
SQLAlchemy==2.0.23
requests==2.31.0
'''
    
    requirements_path = os.path.join(project_name, "requirements.txt")
    with open(requirements_path, 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    
    print(f"✓ requirements.txt created")
    
    # Step 3.5: Install dependencies in virtual environment
    print(f"\n[3.5/5] Installing Python dependencies...")
    print("  This may take a minute...")
    try:
        # Determine correct Python command in venv
        if os.name == 'nt':  # Windows
            pip_cmd = os.path.join(project_name, "venv", "Scripts", "pip.exe")
        else:  # Unix/Linux/Mac
            pip_cmd = os.path.join(project_name, "venv", "bin", "pip")
        
        # Install dependencies
        result = subprocess.run(
            f'"{pip_cmd}" install -r requirements.txt',
            shell=True,
            cwd=project_name,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ All Python dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠ Warning: Failed to auto-install dependencies")
        print(f"  Please run manually:")
        print(f"  cd {project_name}")
        print(f"  venv\\Scripts\\activate  (Windows) or source venv/bin/activate (Unix)")
        print(f"  pip install -r requirements.txt")
        print(f"  Error: {e.stderr if hasattr(e, 'stderr') and e.stderr else str(e)}")
    except FileNotFoundError:
        print(f"⚠ Warning: Could not find pip in virtual environment")
        print(f"  Please install dependencies manually")
    
    # Step 4: Create main Flask app
    print(f"\n[4/5] Creating Flask application...")
    
    # Group endpoints by resource/path
    endpoint_groups = {}
    for endpoint in endpoints:
        path = endpoint.get('path', '/api/unknown')
        # Extract base resource from path
        base_path = '/'.join(path.split('/')[:3])  # e.g., /api/users
        if base_path not in endpoint_groups:
            endpoint_groups[base_path] = []
        endpoint_groups[base_path].append(endpoint)
    
    # Generate route handlers
    route_handlers = []
    for base_path, eps in endpoint_groups.items():
        for ep in eps:
            method = ep.get('method', 'GET')
            path = ep.get('path', '/api/unknown')
            endpoint_name = ep.get('endpoint_name', 'Unknown')
            description = ep.get('description', '')
            request_body = ep.get('request_body', 'N/A')
            response = ep.get('response', 'N/A')
            
            # Convert Flask-style path parameters
            flask_path = path.replace('{', '<').replace('}', '>')
            flask_path = flask_path.replace(':id', '<int:id>').replace(':noteId', '<int:note_id>')
            
            function_name = sanitize_filename(endpoint_name).replace(' ', '_').lower()
            
            route_handler = f'''
@app.route('{flask_path}', methods=['{method}'])
def {function_name}():
    """
    {endpoint_name}
    {description}
    
    Request: {request_body}
    Response: {response}
    """
    # TODO: Implement {endpoint_name}
    try:
        '''
            
            if method == 'GET':
                route_handler += f'''
        # TODO: Fetch data from database
        data = {{"message": "GET {path} - Not implemented yet"}}
        return jsonify(data), 200
'''
            elif method == 'POST':
                route_handler += f'''
        data = request.get_json()
        # TODO: Validate and save data to database
        response_data = {{"message": "POST {path} - Not implemented yet", "received": data}}
        return jsonify(response_data), 201
'''
            elif method == 'PUT' or method == 'PATCH':
                route_handler += f'''
        data = request.get_json()
        # TODO: Update data in database
        response_data = {{"message": "PUT {path} - Not implemented yet", "received": data}}
        return jsonify(response_data), 200
'''
            elif method == 'DELETE':
                route_handler += f'''
        # TODO: Delete data from database
        response_data = {{"message": "DELETE {path} - Not implemented yet"}}
        return jsonify(response_data), 200
'''
            
            route_handler += f'''
    except Exception as e:
        return jsonify({{"error": str(e)}}), 500
'''
            
            route_handlers.append(route_handler)
    
    # Generate endpoint list for home route
    endpoint_list = '\n'.join(
        f'    endpoints_list.append({{"method": "{ep.get("method", "GET")}", "path": "{ep.get("path", "")}", "description": "{ep.get("endpoint_name", "")}"}})'
        for ep in endpoints
    )
    
    # Join all route handlers
    all_route_handlers = '\n'.join(route_handlers)
    
    app_py_content = f'''from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes (allows React frontend to communicate)
CORS(app, resources={{r"/api/*": {{"origins": "http://localhost:3000"}}}})

# Configuration
app.config['DEBUG'] = True
app.config['JSON_SORT_KEYS'] = False

# Home route
@app.route('/')
def home():
    """API Home - List all available endpoints"""
    endpoints_list = []
{endpoint_list}
    
    return jsonify({{
        "message": "Flask Backend API",
        "total_endpoints": len(endpoints_list),
        "endpoints": endpoints_list
    }})

{all_route_handlers}

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({{"error": "Endpoint not found"}}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({{"error": "Internal server error"}}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
'''
    
    app_py_path = os.path.join(project_name, "app.py")
    with open(app_py_path, 'w', encoding='utf-8') as f:
        f.write(app_py_content)
    
    print(f"✓ Flask app created with {len(endpoints)} endpoints")
    
    # Step 5: Create .env file
    print(f"\n[5/5] Creating configuration files...")
    
    env_content = '''# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
PORT=5000

# Database Configuration (add your database URL)
# DATABASE_URL=sqlite:///app.db

# Secret Key (change this in production)
SECRET_KEY=your-secret-key-here
'''
    
    env_path = os.path.join(project_name, ".env")
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✓ .env file created")
    
    # Create README for backend
    endpoints_list = '\n'.join(
        f"{i}. **{ep.get('method', 'GET')} {ep.get('path', '')}** - {ep.get('endpoint_name', '')}"
        for i, ep in enumerate(endpoints, 1)
    )
    
    readme_content = f'''# Flask Backend API

This Flask backend was automatically generated based on your application design.

## Endpoints Created

{endpoints_list}

## Getting Started

1. Navigate to the backend directory:
   ```bash
   cd {project_name}
   ```

2. Activate virtual environment:
   
   **Windows:**
   ```bash
   venv\\Scripts\\activate
   ```
   
   **Mac/Linux:**
   ```bash
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the Flask server:
   ```bash
   python app.py
   ```

5. API will be available at [http://localhost:5000](http://localhost:5000)

## API Documentation

Visit `http://localhost:5000/` to see a list of all available endpoints.

## Project Structure

```
{project_name}/
├── venv/              # Virtual environment
├── app.py             # Main Flask application
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

## Next Steps

- Implement the TODO comments in each endpoint
- Add database integration (SQLAlchemy recommended)
- Add authentication/authorization (JWT, Flask-Login, etc.)
- Add input validation
- Add logging
- Write unit tests
- Set up database migrations
- Add API documentation (Swagger/OpenAPI)

## CORS Configuration

CORS is enabled for `http://localhost:3000` to allow the React frontend to communicate with this backend.
Update the CORS configuration in `app.py` if your frontend runs on a different port.

## Environment Variables

Configure your environment in the `.env` file:
- `PORT`: Server port (default: 5000)
- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: Database connection string (if using a database)
'''
    
    readme_path = os.path.join(project_name, "BACKEND_README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("\n" + "="*70)
    print(f"✓ FLASK PROJECT CREATED: ./{project_name}")
    print(f"✓ {len(endpoints)} API endpoints created")
    print(f"✓ CORS configured for React frontend")
    print("="*70)
    
    return True


def generate_projects(design: Dict[str, Any]):
    """
    Generate both React frontend and Flask backend projects.
    
    Args:
        design: Complete design dictionary with frontend/backend
    
    Returns:
        Dict with project paths: {"react": path, "flask": path}
    """
    print("\n" + "="*70)
    print("PROJECT GENERATION")
    print("="*70)
    
    # Check prerequisites first
    print("\nChecking prerequisites...")
    if not check_prerequisites():
        print("\n⚠ Cannot proceed without required tools.")
        return {"react": None, "flask": None}
    
    print("\n✓ All prerequisites satisfied\n")
    
    # Generate React frontend
    frontend_success = create_react_project(design, "frontend")
    
    # Generate Flask backend
    backend_success = create_flask_backend(design, "backend")
    
    # Final summary
    print("\n" + "="*70)
    print("PROJECT GENERATION COMPLETE")
    print("="*70)
    
    if frontend_success and backend_success:
        print("\n✓ Both projects created successfully!")
        print("\nNext steps:")
        print("\n1. Start the backend:")
        print("   cd backend")
        print("   venv\\Scripts\\activate  (Windows)")
        print("   pip install -r requirements.txt")
        print("   python app.py")
        print("\n2. Start the frontend (in a new terminal):")
        print("   cd frontend")
        print("   npm start")
        print("\n3. Open http://localhost:3000 in your browser")
    else:
        print("\n⚠ Some projects failed to create. Check the errors above.")
    
    print("\n" + "="*70)
    
    return {
        "react": os.path.abspath("frontend") if frontend_success else None,
        "flask": os.path.abspath("backend") if backend_success else None
    }
