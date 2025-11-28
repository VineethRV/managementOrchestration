import os
import json
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

load_dotenv()

def group_pages_by_similarity(pages: List[Dict]) -> List[List[Dict]]:
    """
    Group pages by similarity/functionality for better agent assignment.
    Uses LLM to intelligently group related pages together.
    """
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3, max_tokens=2048)
    
    pages_info = []
    for i, page in enumerate(pages):
        pages_info.append(f"{i}. {page['page_name']} - {page['description']}")
    
    grouping_prompt = f"""Group these pages into 3 logical groups based on functionality/similarity.
Pages should be grouped so related features are together.

Pages:
{chr(10).join(pages_info)}

Return a JSON array of 3 arrays, where each sub-array contains page indices:
[[0, 1, 2], [3, 4], [5, 6]]

JSON only:"""
    
    try:
        response = llm.invoke([HumanMessage(content=grouping_prompt)])
        content = response.content.strip().replace("```json", "").replace("```", "").strip()
        groups_indices = json.loads(content)
        
        # Convert indices to actual page objects
        groups = []
        for group_indices in groups_indices:
            group_pages = [pages[i] for i in group_indices if i < len(pages)]
            if group_pages:
                groups.append(group_pages)
        
        return groups
    except Exception as e:
        print(f"[WARNING] Auto-grouping failed: {e}. Using simple division.")
        # Fallback: simple division
        chunk_size = (len(pages) + 2) // 3
        return [pages[i:i+chunk_size] for i in range(0, len(pages), chunk_size)]


def group_endpoints_by_resource(endpoints: List[Dict]) -> List[List[Dict]]:
    """
    Group endpoints by resource/similarity for backend agents.
    """
    # Group by resource path
    resource_map = {}
    for endpoint in endpoints:
        path = endpoint.get('path', '')
        path_parts = path.strip('/').split('/')
        resource = path_parts[1] if len(path_parts) > 1 else path_parts[0]
        
        if resource not in resource_map:
            resource_map[resource] = []
        resource_map[resource].append(endpoint)
    
    # Distribute resources into 3 groups for 3 agents
    resources = list(resource_map.values())
    if len(resources) <= 3:
        return resources
    
    # Balance groups by endpoint count
    sorted_resources = sorted(resources, key=len, reverse=True)
    groups = [[], [], []]
    group_sizes = [0, 0, 0]
    
    for resource_endpoints in sorted_resources:
        # Assign to smallest group
        min_idx = group_sizes.index(min(group_sizes))
        groups[min_idx].extend(resource_endpoints)
        group_sizes[min_idx] += len(resource_endpoints)
    
    return [g for g in groups if g]


def implement_frontend_pages(agent_id: int, pages: List[Dict], project_path: str, all_endpoints: List[Dict], description: str) -> Dict[str, Any]:
    """
    Frontend worker agent that implements assigned pages with production-quality code.
    """
    logs_dir = "logs"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    agent_log = os.path.join(logs_dir, f"frontend_agent_{agent_id}_{timestamp}.log")
    
    def log_print(msg: str):
        print(msg)
        with open(agent_log, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    
    log_print(f"\n{'='*60}")
    log_print(f"FRONTEND AGENT {agent_id} - Starting Implementation")
    log_print(f"{'='*60}")
    log_print(f"Assigned Pages: {len(pages)}")
    for page in pages:
        log_print(f"  - {page['page_name']}")
    
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, max_tokens=8000)
    results = {"agent_id": agent_id, "pages_implemented": [], "errors": []}
    
    for idx, page in enumerate(pages, 1):
        page_name = page['page_name']
        log_print(f"\n[{idx}/{len(pages)}] Implementing: {page_name}")
        
        # Gather context
        requirements = page.get('requirements', [])
        page_endpoints = page.get('backend_endpoints', [])
        
        # Get full endpoint specs
        endpoint_specs = []
        for ep in page_endpoints:
            for full_ep in all_endpoints:
                if ep.get('path') == full_ep.get('path') and ep.get('method') == full_ep.get('method'):
                    endpoint_specs.append(full_ep)
                    break
        
        implementation_prompt = f"""You are a senior React developer implementing a production-quality page component.

APPLICATION CONTEXT:
{description}

PAGE: {page_name}
Description: {page.get('description', '')}

REQUIREMENTS:
{json.dumps(requirements, indent=2)}

BACKEND ENDPOINTS AVAILABLE:
{json.dumps(endpoint_specs, indent=2)}

IMPLEMENTATION REQUIREMENTS:
1. Create a complete, production-ready React functional component
2. Use React hooks (useState, useEffect, useCallback, useMemo where appropriate)
3. Implement proper error handling and loading states
4. Add form validation if forms are present
5. Use axios for API calls with proper error handling
6. Include PropTypes or TypeScript types in JSDoc comments
7. Add helpful comments for complex logic
8. Use semantic HTML and accessibility attributes
9. Include conditional rendering for different states
10. Handle edge cases (empty data, errors, loading)
11. Backend base URL should be 'http://localhost:5000'

Return ONLY the complete React component code (JSX), nothing else.
Do not include import for CSS or PropTypes.
Start directly with imports and component code."""

        try:
            log_print(f"  Generating implementation...")
            response = llm.invoke([HumanMessage(content=implementation_prompt)])
            component_code = response.content.strip()
            
            # Clean code blocks if present
            if "```" in component_code:
                component_code = component_code.split("```")[1]
                if component_code.startswith("jsx") or component_code.startswith("javascript"):
                    component_code = component_code.split('\n', 1)[1]
            
            # Add imports if missing
            if "import React" not in component_code:
                component_code = "import React, { useState, useEffect } from 'react';\nimport axios from 'axios';\n\n" + component_code
            
            # Save component file
            component_name = page_name.replace(" ", "").replace("-", "")
            component_file = os.path.join(project_path, "src", "pages", f"{component_name}.js")
            
            with open(component_file, 'w', encoding='utf-8') as f:
                f.write(component_code)
            
            log_print(f"  ✓ Implemented successfully: {component_file}")
            results["pages_implemented"].append({
                "page_name": page_name,
                "component_name": component_name,
                "file_path": component_file,
                "success": True
            })
            
        except Exception as e:
            log_print(f"  ✗ Error: {e}")
            results["errors"].append({
                "page_name": page_name,
                "error": str(e)
            })
    
    log_print(f"\n{'='*60}")
    log_print(f"FRONTEND AGENT {agent_id} - Completed")
    log_print(f"Successfully implemented: {len(results['pages_implemented'])}/{len(pages)}")
    log_print(f"Errors: {len(results['errors'])}")
    log_print(f"{'='*60}")
    
    return results


def implement_backend_endpoints(agent_id: int, endpoints: List[Dict], project_path: str, description: str, db_type: str = "sqlite") -> Dict[str, Any]:
    """
    Backend worker agent that implements assigned endpoints with production-quality code.
    """
    logs_dir = "logs"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    agent_log = os.path.join(logs_dir, f"backend_agent_{agent_id}_{timestamp}.log")
    
    def log_print(msg: str):
        print(msg)
        with open(agent_log, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    
    log_print(f"\n{'='*60}")
    log_print(f"BACKEND AGENT {agent_id} - Starting Implementation")
    log_print(f"{'='*60}")
    log_print(f"Assigned Endpoints: {len(endpoints)}")
    for ep in endpoints:
        log_print(f"  - {ep.get('method', 'N/A')} {ep.get('path', 'N/A')}")
    
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, max_tokens=8000)
    results = {"agent_id": agent_id, "endpoints_implemented": [], "errors": []}
    
    # Group by resource for context
    resource_groups = {}
    for ep in endpoints:
        path = ep.get('path', '')
        path_parts = path.strip('/').split('/')
        resource = path_parts[1] if len(path_parts) > 1 else 'general'
        
        if resource not in resource_groups:
            resource_groups[resource] = []
        resource_groups[resource].append(ep)
    
    for resource, resource_endpoints in resource_groups.items():
        log_print(f"\n[Resource: /{resource}] Implementing {len(resource_endpoints)} endpoints")
        
        endpoints_info = []
        for ep in resource_endpoints:
            endpoints_info.append({
                "endpoint_name": ep.get('endpoint_name', ''),
                "method": ep.get('method', ''),
                "path": ep.get('path', ''),
                "description": ep.get('description', ''),
                "request_body": ep.get('request_body', ''),
                "response": ep.get('response', '')
            })
        
        implementation_prompt = f"""You are a senior Flask backend developer implementing production-quality API endpoints.

APPLICATION CONTEXT:
{description}

DATABASE: {db_type.upper()} with SQLAlchemy ORM

RESOURCE: /{resource}
ENDPOINTS TO IMPLEMENT:
{json.dumps(endpoints_info, indent=2)}

IMPLEMENTATION REQUIREMENTS:
1. Create complete, production-ready Flask route handlers
2. Use SQLAlchemy models with proper relationships
3. Implement proper error handling (try-except blocks)
4. Add input validation using request.json validation
5. Return proper HTTP status codes (200, 201, 400, 404, 500)
6. Add database transactions with commit/rollback
7. Include helpful docstrings for each endpoint
8. Handle edge cases (missing data, invalid IDs, duplicates)
9. Use proper RESTful patterns
10. Add authentication decorators if needed (use JWT tokens)
11. Include logging for errors

Return Python code with:
1. SQLAlchemy model definitions (if new models needed)
2. Complete Flask route implementations
3. Helper functions if needed

Format:
```python
# Models (if needed)
# ... SQLAlchemy models ...

# Routes
# ... Flask route handlers ...
```

Return ONLY the Python code, nothing else."""

        try:
            log_print(f"  Generating implementation for /{resource}...")
            response = llm.invoke([HumanMessage(content=implementation_prompt)])
            code = response.content.strip()
            
            # Clean code blocks
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0]
            elif "```" in code:
                code = code.split("```")[1].split("```")[0]
            
            # Save to resource-specific file
            resource_file = os.path.join(project_path, "routes", f"{resource}_routes.py")
            os.makedirs(os.path.dirname(resource_file), exist_ok=True)
            
            with open(resource_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            log_print(f"  ✓ Implemented successfully: {resource_file}")
            
            for ep in resource_endpoints:
                results["endpoints_implemented"].append({
                    "endpoint": f"{ep.get('method')} {ep.get('path')}",
                    "resource": resource,
                    "file_path": resource_file,
                    "success": True
                })
            
        except Exception as e:
            log_print(f"  ✗ Error: {e}")
            for ep in resource_endpoints:
                results["errors"].append({
                    "endpoint": f"{ep.get('method')} {ep.get('path')}",
                    "error": str(e)
                })
    
    log_print(f"\n{'='*60}")
    log_print(f"BACKEND AGENT {agent_id} - Completed")
    log_print(f"Successfully implemented: {len(results['endpoints_implemented'])} endpoints")
    log_print(f"Errors: {len(results['errors'])}")
    log_print(f"{'='*60}")
    
    return results


def implement_with_worker_agents(design: Dict[str, Any], react_project_path: str, flask_project_path: str, description: str):
    """
    Main function to coordinate 3 frontend and 3 backend worker agents.
    """
    print("\n" + "="*70)
    print("WORKER AGENTS IMPLEMENTATION PHASE")
    print("="*70)
    
    pages = design['frontend']['pages']
    endpoints = design['backend']['endpoints']
    
    # Group pages for frontend agents
    print("\n[Phase 1] Grouping pages for frontend agents...")
    frontend_groups = group_pages_by_similarity(pages)
    
    print(f"✓ Created {len(frontend_groups)} frontend agent groups:")
    for i, group in enumerate(frontend_groups, 1):
        page_names = [p['page_name'] for p in group]
        print(f"  Frontend Agent {i}: {len(group)} pages - {', '.join(page_names)}")
    
    # Group endpoints for backend agents
    print("\n[Phase 2] Grouping endpoints for backend agents...")
    backend_groups = group_endpoints_by_resource(endpoints)
    
    print(f"✓ Created {len(backend_groups)} backend agent groups:")
    for i, group in enumerate(backend_groups, 1):
        ep_info = [f"{e.get('method')} {e.get('path')}" for e in group]
        print(f"  Backend Agent {i}: {len(group)} endpoints")
        for ep in ep_info[:3]:
            print(f"    - {ep}")
        if len(ep_info) > 3:
            print(f"    ... and {len(ep_info) - 3} more")
    
    # Deploy frontend agents
    print("\n" + "="*60)
    print("[Phase 3] DEPLOYING FRONTEND WORKER AGENTS")
    print("="*60)
    
    frontend_results = []
    for i, group in enumerate(frontend_groups, 1):
        result = implement_frontend_pages(i, group, react_project_path, endpoints, description)
        frontend_results.append(result)
    
    # Deploy backend agents
    print("\n" + "="*60)
    print("[Phase 4] DEPLOYING BACKEND WORKER AGENTS")
    print("="*60)
    
    backend_results = []
    for i, group in enumerate(backend_groups, 1):
        result = implement_backend_endpoints(i, group, flask_project_path, description)
        backend_results.append(result)
    
    # Create database setup file
    print("\n[Phase 5] Creating database setup...")
    create_database_setup(flask_project_path, endpoints, description)
    
    # Update main app.py to include all routes
    print("\n[Phase 6] Updating Flask app.py with all routes...")
    update_flask_app_with_routes(flask_project_path, backend_groups)
    
    # Save implementation summary
    logs_dir = "logs"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = os.path.join(logs_dir, f"implementation_summary_{timestamp}.json")
    
    summary = {
        "timestamp": timestamp,
        "frontend_agents": len(frontend_groups),
        "backend_agents": len(backend_groups),
        "total_pages": len(pages),
        "total_endpoints": len(endpoints),
        "frontend_results": frontend_results,
        "backend_results": backend_results
    }
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n" + "="*70)
    print("IMPLEMENTATION COMPLETE")
    print("="*70)
    
    total_pages_success = sum(len(r['pages_implemented']) for r in frontend_results)
    total_pages_errors = sum(len(r['errors']) for r in frontend_results)
    total_endpoints_success = sum(len(r['endpoints_implemented']) for r in backend_results)
    total_endpoints_errors = sum(len(r['errors']) for r in backend_results)
    
    print(f"\n✓ Frontend: {total_pages_success}/{len(pages)} pages implemented")
    print(f"✓ Backend: {total_endpoints_success}/{len(endpoints)} endpoints implemented")
    
    if total_pages_errors > 0 or total_endpoints_errors > 0:
        print(f"\n⚠ Errors encountered:")
        print(f"  - Frontend errors: {total_pages_errors}")
        print(f"  - Backend errors: {total_endpoints_errors}")
        print(f"\nCheck logs in /logs directory for details.")
    
    print(f"\n📁 Implementation summary: {summary_path}")
    print("\n" + "="*70)


def create_database_setup(project_path: str, endpoints: List[Dict], description: str):
    """Create database models and initialization file."""
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, max_tokens=8000)
    
    # Gather all endpoint info
    endpoints_info = [
        f"{ep.get('method')} {ep.get('path')} - {ep.get('description', '')}"
        for ep in endpoints
    ]
    
    prompt = f"""Create complete SQLAlchemy database models for this application.

APPLICATION: {description}

ENDPOINTS:
{chr(10).join(endpoints_info)}

Create:
1. All necessary SQLAlchemy models with relationships
2. Database initialization code
3. Sample data seeding (optional but useful)

Include proper:
- Primary keys and foreign keys
- Relationships (one-to-many, many-to-many)
- Timestamps (created_at, updated_at)
- Indexes where appropriate
- Constraints (unique, nullable)

Return complete Python code for models.py file:"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        code = response.content.strip()
        
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        models_file = os.path.join(project_path, "models.py")
        with open(models_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f"✓ Database models created: {models_file}")
    except Exception as e:
        print(f"✗ Error creating database models: {e}")


def update_flask_app_with_routes(project_path: str, backend_groups: List[List[Dict]]):
    """Update app.py to register all route blueprints."""
    
    # Collect all unique resources
    resources = set()
    for group in backend_groups:
        for ep in group:
            path = ep.get('path', '')
            path_parts = path.strip('/').split('/')
            resource = path_parts[1] if len(path_parts) > 1 else 'general'
            resources.add(resource)
    
    app_py_path = os.path.join(project_path, "app.py")
    
    # Read existing app.py
    try:
        with open(app_py_path, 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Add imports for route modules
        import_lines = []
        register_lines = []
        
        for resource in sorted(resources):
            import_lines.append(f"from routes.{resource}_routes import {resource}_bp")
            register_lines.append(f"app.register_blueprint({resource}_bp, url_prefix='/api/{resource}')")
        
        # Insert imports after other imports
        if "from flask import" in app_content:
            parts = app_content.split("from flask import", 1)
            rest = parts[1].split('\n', 1)
            app_content = parts[0] + "from flask import" + rest[0] + "\n" + "\n".join(import_lines) + "\n" + rest[1]
        
        # Insert blueprint registrations after app creation
        if "app = Flask(__name__)" in app_content:
            parts = app_content.split("app = Flask(__name__)", 1)
            config_section = parts[1].split("# Home route", 1)[0]
            rest = parts[1].split("# Home route", 1)[1] if "# Home route" in parts[1] else ""
            
            app_content = (parts[0] + "app = Flask(__name__)" + config_section + 
                          "\n# Register blueprints\n" + "\n".join(register_lines) + "\n\n# Home route" + rest)
        
        with open(app_py_path, 'w', encoding='utf-8') as f:
            f.write(app_content)
        
        print(f"✓ Updated Flask app with {len(resources)} route blueprints")
        
    except Exception as e:
        print(f"✗ Error updating Flask app: {e}")
