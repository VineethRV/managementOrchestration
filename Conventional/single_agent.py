"""
Conventional Baseline: Single-Agent Orchestration
A single agent handles all phases sequentially:
1. Requirements gathering
2. Application design (frontend + backend)
3. Project generation
4. Implementation (all pages and endpoints)
5. Metrics tracking

This serves as the baseline for comparison with multi-agent approaches.
"""

import os
import json
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

# Load environment variables
load_dotenv()

# Check for GROQ_API_KEY
if not os.getenv("GROQ_API_KEY"):
    print("="*70)
    print("ERROR: GROQ_API_KEY not found!")
    print("="*70)
    print("\nPlease set up your Groq API key:")
    print("1. Create a .env file in the Conventional directory")
    print("2. Add: GROQ_API_KEY=your_api_key_here")
    print("3. Get your API key from: https://console.groq.com/")
    print("\nExample .env file:")
    print("  GROQ_API_KEY=gsk_your_key_here")
    print("="*70)
    raise ValueError("GROQ_API_KEY environment variable is required")

# Metrics tracking
class MetricsTracker:
    """Track metrics for comparison with other approaches."""
    def __init__(self):
        self.total_tokens = 0
        self.bugs_encountered = 0
        self.features_implemented = 0
        self.lines_of_code = 0
        self.start_time = datetime.now()
        
    def add_tokens(self, count: int):
        self.total_tokens += count
        
    def add_bug(self, description: str):
        self.bugs_encountered += 1
        
    def add_feature(self, feature_name: str):
        self.features_implemented += 1
        
    def add_lines_of_code(self, count: int):
        self.lines_of_code += count
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        return {
            "total_tokens": self.total_tokens,
            "bugs_encountered": self.bugs_encountered,
            "features_implemented": self.features_implemented,
            "lines_of_code": self.lines_of_code,
            "duration_seconds": duration,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    def save(self, filepath: str):
        """Save metrics to JSON file."""
        metrics = self.get_metrics()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)


# Cache for the agent instance
_single_agent_cache = None

def get_single_agent():
    """Get or create the single agent instance (lazy initialization)."""
    global _single_agent_cache
    if _single_agent_cache is None:
        _single_agent_cache = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=8000
        )
    return _single_agent_cache

# Initialize metrics tracker
metrics = MetricsTracker()

# Logs directory
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)


def log_and_print(message: str, log_file: str):
    """Helper to print and log simultaneously."""
    print(message)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')


def invoke_with_metrics(agent, messages, log_file: str = None):
    """Invoke agent and track token usage in metrics."""
    if agent is None:
        agent = get_single_agent()
    response = agent.invoke(messages)
    
    # Track token usage if available
    if hasattr(response, 'response_metadata') and response.response_metadata:
        token_usage = response.response_metadata.get('token_usage', {})
        if token_usage:
            total_tokens = token_usage.get('total_tokens', 0)
            if total_tokens:
                metrics.add_tokens(total_tokens)
                if log_file:
                    log_and_print(f"[Tokens: {total_tokens}]", log_file)
    
    return response


def gather_requirements_interactive() -> Dict[str, Any]:
    """
    Phase 1: Single agent gathers requirements interactively.
    Returns: {"detailed_description": str, "features": List[str]}
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"conventional_requirements_{timestamp}.log")
    
    print("="*70)
    print("CONVENTIONAL BASELINE: SINGLE-AGENT ORCHESTRATION")
    print("="*70)
    print("\nPhase 1: Requirements Gathering")
    print("-" * 70)
    
    requirements = {
        "detailed_description": None,
        "features": None,
        "is_finalized": False
    }
    
    conversation_history = [
        SystemMessage(content="""You are a requirements analyst gathering information about a software application.
Your job is to:
1. Ask clarifying questions about the application
2. Understand the key features and requirements
3. Summarize what you've understood
4. Confirm with the user that you have the complete picture
5. Once confirmed, output the final requirements in this exact JSON format:
{
    "detailed_description": "full description of the application",
    "features": ["feature1", "feature2", "feature3"]
}
Be thorough and ask specific questions.""")
    ]
    
    # Initial greeting
    agent = get_single_agent()
    initial_response = invoke_with_metrics(
        agent,
        conversation_history + [HumanMessage(content="Hello, I'd like to discuss my application idea.")],
        log_file
    )
    print(f"\nAgent: {initial_response.content}\n")
    conversation_history.append(HumanMessage(content="Hello, I'd like to discuss my application idea."))
    conversation_history.append(initial_response)
    
    # Interactive loop
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'done']:
            break
        if not user_input:
            continue
            
        conversation_history.append(HumanMessage(content=user_input))
        
        agent = get_single_agent()
        response = invoke_with_metrics(agent, conversation_history, log_file)
        print(f"\nAgent: {response.content}\n")
        conversation_history.append(response)
        
        # Try to extract JSON from response if user has confirmed
        content = response.content.strip()
        if "{" in content and "detailed_description" in content:
            try:
                # Extract JSON from response
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    parsed = json.loads(json_str)
                    if "detailed_description" in parsed and "features" in parsed:
                        requirements = parsed
                        requirements["is_finalized"] = True
                        print("\n✓ Requirements finalized!")
                        break
            except json.JSONDecodeError:
                pass
        
        log_and_print(f"User: {user_input}", log_file)
        log_and_print(f"Agent: {content}", log_file)
    
    if not requirements["is_finalized"]:
        print("\n⚠ Requirements not finalized. Please run again.")
        return requirements
    
    log_and_print(f"\n✓ Finalized Requirements:", log_file)
    log_and_print(json.dumps(requirements, indent=2), log_file)
    
    return requirements


def design_application(description: str, features: List[str]) -> Dict[str, Any]:
    """
    Phase 2: Single agent designs the entire application (frontend + backend).
    Returns: Complete design dictionary with pages and endpoints.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"conventional_design_{timestamp}.log")
    
    print("\n" + "="*70)
    print("Phase 2: Application Design (Frontend + Backend)")
    print("-" * 70)
    
    design_prompt = f"""Design a complete software application based on these requirements.

Application Description: {description}

Features: {json.dumps(features, indent=2)}

Design the complete application including:
1. All frontend pages/screens needed
2. UI requirements for each page
3. All backend API endpoints needed
4. Full API specifications (request/response)

Return a complete JSON design in this exact format:
{{
    "frontend": {{
        "pages": [
            {{
                "page_name": "Page Name",
                "description": "Page description",
                "requirements": ["requirement1", "requirement2"],
                "backend_endpoints": [
                    {{
                        "endpoint_name": "Endpoint Name",
                        "method": "GET|POST|PUT|DELETE",
                        "path": "/api/resource",
                        "description": "Endpoint description",
                        "request_body": "Request body structure",
                        "response": "Response structure"
                    }}
                ]
            }}
        ],
        "is_complete": true
    }},
    "backend": {{
        "endpoints": [
            {{
                "endpoint_name": "Endpoint Name",
                "method": "GET|POST|PUT|DELETE",
                "path": "/api/resource",
                "description": "Endpoint description",
                "request_body": "Request body structure",
                "response": "Response structure"
            }}
        ],
        "is_complete": true
    }}
}}

Be comprehensive and detailed. Include ALL pages and endpoints needed for the application."""

    log_and_print(f"\n[Agent Request] Designing application...", log_file)
    
    agent = get_single_agent()
    response = invoke_with_metrics(agent, [HumanMessage(content=design_prompt)], log_file)
    content = response.content.strip()
    
    log_and_print(f"\n[Agent Response]\n{content[:1000]}...", log_file)
    
    # Extract JSON from response
    try:
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            design = json.loads(json_str)
            
            # Ensure structure is complete
            if "frontend" not in design:
                design["frontend"] = {"pages": [], "is_complete": False}
            if "backend" not in design:
                design["backend"] = {"endpoints": [], "is_complete": False}
            
            log_and_print(f"\n✓ Design complete: {len(design.get('frontend', {}).get('pages', []))} pages, {len(design.get('backend', {}).get('endpoints', []))} endpoints", log_file)
            return design
    except json.JSONDecodeError as e:
        log_and_print(f"\n✗ Failed to parse design JSON: {e}", log_file)
        return {"frontend": {"pages": [], "is_complete": False}, "backend": {"endpoints": [], "is_complete": False}}
    
    return {"frontend": {"pages": [], "is_complete": False}, "backend": {"endpoints": [], "is_complete": False}}


def generate_project_scaffolding(design: Dict[str, Any], react_path: str = "frontend", flask_path: str = "backend") -> Dict[str, str]:
    """
    Phase 3: Generate project scaffolding (React + Flask).
    Uses the same project generator logic as Top-Down approach.
    """
    print("\n" + "="*70)
    print("Phase 3: Project Scaffolding Generation")
    print("-" * 70)
    
    # Import project generator from Top down directory
    import sys
    topdown_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Top down")
    sys.path.insert(0, topdown_path)
    from project_generator import generate_projects
    
    project_paths = generate_projects(design)
    return project_paths


def implement_all_code(design: Dict[str, Any], react_path: str, flask_path: str, description: str):
    """
    Phase 4: Single agent implements ALL frontend pages and backend endpoints sequentially.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"conventional_implementation_{timestamp}.log")
    
    print("\n" + "="*70)
    print("Phase 4: Code Implementation (Single Agent)")
    print("-" * 70)
    
    pages = design.get("frontend", {}).get("pages", [])
    endpoints = design.get("backend", {}).get("endpoints", [])
    
    log_and_print(f"\nImplementing {len(pages)} frontend pages and {len(endpoints)} backend endpoints sequentially...", log_file)
    
    # Implement frontend pages one by one
    print(f"\n[Frontend] Implementing {len(pages)} pages...")
    for i, page in enumerate(pages, 1):
        print(f"  [{i}/{len(pages)}] {page.get('page_name', 'Unknown')}")
        implement_frontend_page(page, react_path, endpoints, description, log_file)
    
    # Implement backend endpoints one by one
    print(f"\n[Backend] Implementing {len(endpoints)} endpoints...")
    for i, endpoint in enumerate(endpoints, 1):
        print(f"  [{i}/{len(endpoints)}] {endpoint.get('method', 'GET')} {endpoint.get('path', '/')}")
        implement_backend_endpoint(endpoint, flask_path, description, log_file)
    
    print("\n✓ Implementation complete!")


def implement_frontend_page(page: Dict, project_path: str, all_endpoints: List[Dict], description: str, log_file: str):
    """Single agent implements one frontend page."""
    page_name = page.get('page_name', 'Unknown')
    requirements = page.get('requirements', [])
    page_endpoints = page.get('backend_endpoints', [])
    
    # Get full endpoint specs
    endpoint_specs = []
    for ep in page_endpoints:
        for full_ep in all_endpoints:
            if ep.get('path') == full_ep.get('path') and ep.get('method') == full_ep.get('method'):
                endpoint_specs.append(full_ep)
                break
    
    prompt = f"""Implement a production-quality React component for this page.

APPLICATION CONTEXT: {description}

PAGE: {page_name}
Description: {page.get('description', '')}

REQUIREMENTS:
{json.dumps(requirements, indent=2)}

BACKEND ENDPOINTS:
{json.dumps(endpoint_specs, indent=2)}

Create a complete React functional component with:
1. React hooks (useState, useEffect, useCallback where appropriate)
2. Error handling and loading states
3. Form validation if forms are present
4. Axios for API calls (backend at http://localhost:5000)
5. Proper comments and documentation
6. Semantic HTML and accessibility
7. Handle edge cases

Return ONLY the complete React component code (JSX), nothing else. Start with imports."""

    try:
        agent = get_single_agent()
        response = invoke_with_metrics(agent, [HumanMessage(content=prompt)], log_file)
        component_code = response.content.strip()
        
        # Clean code blocks
        if "```" in component_code:
            component_code = component_code.split("```")[1]
            if component_code.startswith("jsx") or component_code.startswith("javascript"):
                component_code = component_code.split('\n', 1)[1]
            component_code = component_code.split("```")[0]
        
        # Add imports if missing
        if "import React" not in component_code:
            component_code = "import React, { useState, useEffect } from 'react';\nimport axios from 'axios';\n\n" + component_code
        
        # Save component file
        component_name = page_name.replace(" ", "").replace("-", "")
        component_file = os.path.join(project_path, "src", "pages", f"{component_name}.js")
        os.makedirs(os.path.dirname(component_file), exist_ok=True)
        
        with open(component_file, 'w', encoding='utf-8') as f:
            f.write(component_code)
        
        # Track metrics
        lines = len(component_code.split('\n'))
        metrics.add_lines_of_code(lines)
        metrics.add_feature(f"Frontend: {page_name}")
        
        log_and_print(f"  ✓ Implemented {page_name} ({lines} lines)", log_file)
        
    except Exception as e:
        log_and_print(f"  ✗ Error implementing {page_name}: {e}", log_file)
        metrics.add_bug(f"Frontend {page_name}: {str(e)}")


def implement_backend_endpoint(endpoint: Dict, project_path: str, description: str, log_file: str):
    """Single agent implements one backend endpoint."""
    path = endpoint.get('path', '')
    method = endpoint.get('method', 'GET')
    
    prompt = f"""Implement a production-quality Flask route handler for this endpoint.

APPLICATION CONTEXT: {description}

ENDPOINT SPECIFICATION:
{json.dumps(endpoint, indent=2)}

Create a complete Flask route with:
1. Proper error handling (try-except)
2. Input validation
3. Correct HTTP status codes
4. Database operations using SQLAlchemy (if needed)
5. Proper docstrings
6. Handle edge cases

Return ONLY Python code for the route handler. Use SQLite with SQLAlchemy.
Format as: @app.route('...', methods=['...'])\ndef ...(): ..."""

    try:
        agent = get_single_agent()
        response = invoke_with_metrics(agent, [HumanMessage(content=prompt)], log_file)
        code = response.content.strip()
        
        # Clean code blocks
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        # Determine file path based on resource
        path_parts = path.strip('/').split('/')
        resource = path_parts[1] if len(path_parts) > 1 else 'general'
        resource_file = os.path.join(project_path, "routes", f"{resource}_routes.py")
        os.makedirs(os.path.dirname(resource_file), exist_ok=True)
        
        # Append to file or create new
        if os.path.exists(resource_file):
            with open(resource_file, 'a', encoding='utf-8') as f:
                f.write("\n\n" + code)
        else:
            with open(resource_file, 'w', encoding='utf-8') as f:
                f.write("from flask import Flask, request, jsonify\n\n" + code)
        
        # Track metrics
        lines = len(code.split('\n'))
        metrics.add_lines_of_code(lines)
        metrics.add_feature(f"Backend: {method} {path}")
        
        log_and_print(f"  ✓ Implemented {method} {path} ({lines} lines)", log_file)
        
    except Exception as e:
        log_and_print(f"  ✗ Error implementing {method} {path}: {e}", log_file)
        metrics.add_bug(f"Backend {method} {path}: {str(e)}")


def main():
    """Main orchestrator for conventional single-agent baseline."""
    print("\n" + "="*70)
    print("CONVENTIONAL BASELINE: SINGLE-AGENT ORCHESTRATION")
    print("="*70)
    print("\nThis baseline uses ONE agent to handle all phases sequentially.")
    print("Phases: Requirements → Design → Scaffolding → Implementation")
    print("="*70)
    
    # Phase 1: Requirements
    requirements = gather_requirements_interactive()
    if not requirements.get("is_finalized"):
        print("\n⚠ Cannot proceed without finalized requirements.")
        return
    
    # Phase 2: Design
    design = design_application(
        requirements["detailed_description"],
        requirements["features"]
    )
    
    # Save design
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    design_path = os.path.join(logs_dir, f"conventional_design_{timestamp}.json")
    with open(design_path, 'w', encoding='utf-8') as f:
        json.dump(design, f, indent=2)
    print(f"\n✓ Design saved to: {design_path}")
    
    # Ask if user wants to generate projects
    user_input = input("\n\nWould you like to generate React and Flask projects? (yes/no): ").strip().lower()
    if user_input not in ['yes', 'y']:
        print("\nProject generation skipped.")
        return
    
    # Phase 3: Generate scaffolding
    project_paths = generate_project_scaffolding(design)
    
    react_path = project_paths.get('react')
    flask_path = project_paths.get('flask')
    
    if not react_path or not flask_path:
        print("\n⚠ Failed to generate projects.")
        return
    
    # Ask if user wants to implement code
    user_input = input("\n\nWould you like the agent to implement all code? (yes/no): ").strip().lower()
    if user_input not in ['yes', 'y']:
        print("\nImplementation skipped.")
        return
    
    # Phase 4: Implementation
    implement_all_code(design, react_path, flask_path, requirements["detailed_description"])
    
    # Save metrics
    metrics_path = os.path.join(logs_dir, f"conventional_metrics_{timestamp}.json")
    metrics.save(metrics_path)
    
    print("\n" + "="*70)
    print("CONVENTIONAL BASELINE COMPLETE")
    print("="*70)
    print(f"\n✓ Metrics saved to: {metrics_path}")
    print(f"\nMetrics Summary:")
    metrics_dict = metrics.get_metrics()
    print(f"  - Total Tokens: {metrics_dict['total_tokens']}")
    print(f"  - Bugs Encountered: {metrics_dict['bugs_encountered']}")
    print(f"  - Features Implemented: {metrics_dict['features_implemented']}")
    print(f"  - Lines of Code: {metrics_dict['lines_of_code']}")
    print(f"  - Duration: {metrics_dict['duration_seconds']:.2f} seconds")
    print("="*70)


if __name__ == "__main__":
    main()

