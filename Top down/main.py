from finalizer import run_requirements_agent, finalized_requirements
from frontend_backend_managers import design_application
from project_generator import generate_projects
from worker_agents import implement_with_worker_agents
from debugging_agents import run_debugging_agents
import json
import os
import asyncio

print("Starting requirements gathering session...\n")
run_requirements_agent()

if not finalized_requirements["is_finalized"]:
    exit()

print(f"\nDetailed Description: {finalized_requirements['detailed_description']}")
print("\nFeatures: ", finalized_requirements['features'])

# Now run the design workflow with frontend and backend agents
print("\n\nProceeding to application design phase...\n")

design_result = design_application(
    description=finalized_requirements['detailed_description'],
    features=finalized_requirements['features']
)

# Save the complete design to a file
with open('application_design.json', 'w') as f:
    json.dump(design_result, f, indent=2)

print("\n\nComplete design has been saved to 'application_design.json'")

# Print summary
print("\n" + "="*70)
print("DESIGN SUMMARY")
print("="*70)
if design_result['frontend']['is_complete']:
    print(f"\n✓ Frontend Design: {len(design_result['frontend']['pages'])} pages designed")
    for page in design_result['frontend']['pages']:
        page_name = page.get('page_name', 'Unnamed Page')
        req_count = len(page.get('requirements', []))
        endpoint_count = len(page.get('backend_endpoints', []))
        print(f"  - {page_name} ({req_count} requirements, {endpoint_count} endpoints)")

if design_result['backend']['is_complete']:
    print(f"\n✓ Backend Design: {len(design_result['backend']['endpoints'])} endpoints designed")
    for endpoint in design_result['backend']['endpoints']:
        method = endpoint.get('method', 'N/A')
        path = endpoint.get('path', 'N/A')
        name = endpoint.get('endpoint_name', 'Unnamed')
        print(f"  - {method:6s} {path:30s} - {name}")

print("\n" + "="*70)

# Generate React and Flask projects
if design_result['frontend']['is_complete'] and design_result['backend']['is_complete']:
    user_input = input("\n\nWould you like to generate React frontend and Flask backend projects? (yes/no): ").strip().lower()
    
    if user_input in ['yes', 'y']:
        project_paths = generate_projects(design_result)
        
        # Ask if user wants to implement with worker agents
        implement_input = input("\n\nWould you like to implement the project with AI worker agents? (yes/no): ").strip().lower()
        
        if implement_input in ['yes', 'y']:
            react_path = project_paths.get('react')
            flask_path = project_paths.get('flask')
            
            if react_path and flask_path:
                implement_with_worker_agents(
                    design=design_result,
                    react_project_path=react_path,
                    flask_project_path=flask_path,
                    description=finalized_requirements['detailed_description']
                )
                
                # After implementation, ask about debugging
                debug_input = input("\n\nWould you like to start the projects and run debugging agents? (yes/no): ").strip().lower()
                
                if debug_input in ['yes', 'y']:
                    asyncio.run(run_debugging_agents(react_path, flask_path))
                else:
                    print("\nDebugging phase skipped.")
            else:
                print("\n⚠ Could not find generated project directories.")
                print(f"React path: {react_path}")
                print(f"Flask path: {flask_path}")
        else:
            print("\nWorker agent implementation skipped.")
    else:
        print("\nProject generation skipped. You can generate projects later using the design JSON.")
else:
    print("\n⚠ Design incomplete. Cannot generate projects.")
