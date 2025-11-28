"""
Resume project generation and implementation from logs.
This script reads the latest design from logs and continues from project generation.
"""

import os
import json
import glob
from datetime import datetime
from project_generator import generate_projects
from worker_agents import implement_with_worker_agents


def find_latest_design():
    """Find the most recent final design file in logs."""
    logs_dir = "logs"
    
    if not os.path.exists(logs_dir):
        print("❌ No logs directory found. Please run main.py first.")
        return None
    
    # Look for final design files
    design_files = glob.glob(os.path.join(logs_dir, "final_design_*.json"))
    
    if not design_files:
        # Fallback to application_design.json in root
        root_design = "application_design.json"
        if os.path.exists(root_design):
            print(f"📄 Found design file: {root_design}")
            return root_design
        else:
            print("❌ No design files found. Please run main.py first.")
            return None
    
    # Get the most recent file
    latest_file = max(design_files, key=os.path.getmtime)
    print(f"📄 Found latest design: {latest_file}")
    return latest_file


def load_design(file_path):
    """Load design from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            design = json.load(f)
        
        # Validate design structure
        if 'frontend' not in design or 'backend' not in design:
            print("❌ Invalid design file structure")
            return None
        
        return design
    except Exception as e:
        print(f"❌ Error loading design file: {e}")
        return None


def check_project_status():
    """Check what stage the project is at."""
    status = {
        "design_exists": False,
        "frontend_scaffolding": False,
        "backend_scaffolding": False,
        "frontend_implemented": False,
        "backend_implemented": False,
        "description": None
    }
    
    # Check for design
    design_file = find_latest_design()
    if design_file:
        status["design_exists"] = True
        design = load_design(design_file)
        if design:
            # Try to extract description from logs
            logs_dir = "logs"
            session_logs = glob.glob(os.path.join(logs_dir, "session_*.log"))
            if session_logs:
                latest_log = max(session_logs, key=os.path.getmtime)
                try:
                    with open(latest_log, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract description from log
                        if "Description:" in content:
                            desc_line = [line for line in content.split('\n') if line.startswith('Description:')]
                            if desc_line:
                                status["description"] = desc_line[0].replace('Description:', '').strip()
                except:
                    pass
    
    # Check for frontend scaffolding
    if os.path.exists("frontend") and os.path.exists("frontend/src"):
        status["frontend_scaffolding"] = True
        
        # Check if implemented (look for pages with actual code)
        pages_dir = os.path.join("frontend", "src", "pages")
        if os.path.exists(pages_dir):
            page_files = glob.glob(os.path.join(pages_dir, "*.js"))
            if page_files:
                # Check if files have substantial code (not just TODOs)
                for page_file in page_files[:1]:  # Check first file
                    try:
                        with open(page_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # If file has axios imports and substantial code, it's implemented
                            if "axios" in content and len(content) > 500:
                                status["frontend_implemented"] = True
                                break
                    except:
                        pass
    
    # Check for backend scaffolding
    if os.path.exists("backend") and os.path.exists("backend/app.py"):
        status["backend_scaffolding"] = True
        
        # Check if implemented (look for routes directory)
        routes_dir = os.path.join("backend", "routes")
        if os.path.exists(routes_dir):
            route_files = glob.glob(os.path.join(routes_dir, "*_routes.py"))
            if route_files:
                status["backend_implemented"] = True
    
    return status


def display_status(status):
    """Display current project status."""
    print("\n" + "="*70)
    print("PROJECT STATUS")
    print("="*70)
    
    print("\n✅" if status["design_exists"] else "\n❌", "Design phase")
    print("✅" if status["frontend_scaffolding"] else "❌", "Frontend scaffolding")
    print("✅" if status["backend_scaffolding"] else "❌", "Backend scaffolding")
    print("✅" if status["frontend_implemented"] else "❌", "Frontend implementation")
    print("✅" if status["backend_implemented"] else "❌", "Backend implementation")
    
    print("\n" + "="*70)


def resume_project():
    """Main function to resume project from where it left off."""
    print("\n" + "="*70)
    print("RESUME PROJECT")
    print("="*70)
    
    # Check current status
    print("\n[Step 1] Checking project status...")
    status = check_project_status()
    display_status(status)
    
    if not status["design_exists"]:
        print("\n❌ No design found. Please run main.py first to create the design.")
        return
    
    # Load design
    print("\n[Step 2] Loading design...")
    design_file = find_latest_design()
    design = load_design(design_file)
    
    if not design:
        print("\n❌ Failed to load design file.")
        return
    
    print(f"✓ Design loaded successfully")
    print(f"  - Frontend: {len(design['frontend']['pages'])} pages")
    print(f"  - Backend: {len(design['backend']['endpoints'])} endpoints")
    
    # Determine what to do next
    if not status["frontend_scaffolding"] or not status["backend_scaffolding"]:
        # Need to generate projects
        print("\n[Step 3] Generating project scaffolding...")
        user_input = input("\nGenerate React and Flask projects? (yes/no): ").strip().lower()
        
        if user_input not in ['yes', 'y']:
            print("\n⏸ Project generation skipped.")
            return
        
        project_paths = generate_projects(design)
        
        if not project_paths.get('react') or not project_paths.get('flask'):
            print("\n❌ Project generation failed.")
            return
        
        print("\n✓ Projects generated successfully")
        status["frontend_scaffolding"] = True
        status["backend_scaffolding"] = True
        status = check_project_status()  # Refresh status
    
    # Check if implementation is needed
    if not status["frontend_implemented"] or not status["backend_implemented"]:
        print("\n[Step 4] Ready for AI worker agent implementation...")
        
        implement_input = input("\nDeploy AI worker agents to implement the code? (yes/no): ").strip().lower()
        
        if implement_input not in ['yes', 'y']:
            print("\n⏸ Implementation skipped.")
            return
        
        # Get description for worker agents
        description = status.get("description")
        if not description:
            description = input("\nEnter application description: ").strip()
            if not description:
                description = "Full-stack application"
        
        # Get project paths
        react_path = os.path.abspath("frontend")
        flask_path = os.path.abspath("backend")
        
        print(f"\nReact project: {react_path}")
        print(f"Flask project: {flask_path}")
        
        # Deploy worker agents
        implement_with_worker_agents(
            design=design,
            react_project_path=react_path,
            flask_project_path=flask_path,
            description=description
        )
        
        print("\n✓ Implementation completed by worker agents")
    else:
        print("\n✅ Project is fully implemented!")
        print("\nNext steps:")
        print("\n1. Start the backend:")
        print("   cd backend")
        print("   .\\venv\\Scripts\\activate")
        print("   python app.py")
        print("\n2. Start the frontend (in a new terminal):")
        print("   cd frontend")
        print("   npm start")
        print("\n3. Open http://localhost:3000 in your browser")
    
    print("\n" + "="*70)
    print("RESUME COMPLETE")
    print("="*70)


def quick_status():
    """Quick status check without prompts."""
    status = check_project_status()
    display_status(status)
    
    if status["design_exists"]:
        design_file = find_latest_design()
        design = load_design(design_file)
        if design:
            print(f"\nDesign: {len(design['frontend']['pages'])} pages, {len(design['backend']['endpoints'])} endpoints")
    
    print("\nTo continue: python resume.py")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        quick_status()
    else:
        resume_project()
