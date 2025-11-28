"""
Test the project generator with a sample design.
This creates a simple note-taking app without running the full workflow.
"""

import json
from project_generator import generate_projects

# Sample design for a simple note-taking app
sample_design = {
    "frontend": {
        "pages": [
            {
                "page_name": "Home Page",
                "description": "Landing page with app overview",
                "requirements": [
                    "Display welcome message",
                    "Show app features",
                    "Login/Register buttons"
                ],
                "backend_endpoints": []
            },
            {
                "page_name": "Login Page",
                "description": "User authentication page",
                "requirements": [
                    "Email input field",
                    "Password input field",
                    "Login button",
                    "Link to registration page"
                ],
                "backend_endpoints": [
                    {
                        "endpoint_name": "User Login",
                        "description": "Authenticate user credentials",
                        "method": "POST",
                        "path": "/api/auth/login"
                    }
                ]
            },
            {
                "page_name": "Notes List Page",
                "description": "Display all user notes",
                "requirements": [
                    "Display list of notes",
                    "Search functionality",
                    "Create new note button",
                    "Edit/Delete options for each note"
                ],
                "backend_endpoints": [
                    {
                        "endpoint_name": "Get All Notes",
                        "description": "Retrieve all notes for user",
                        "method": "GET",
                        "path": "/api/notes"
                    },
                    {
                        "endpoint_name": "Delete Note",
                        "description": "Delete a specific note",
                        "method": "DELETE",
                        "path": "/api/notes/{id}"
                    }
                ]
            },
            {
                "page_name": "Create Note Page",
                "description": "Create a new note",
                "requirements": [
                    "Title input field",
                    "Content text area",
                    "Save button",
                    "Cancel button"
                ],
                "backend_endpoints": [
                    {
                        "endpoint_name": "Create Note",
                        "description": "Create a new note",
                        "method": "POST",
                        "path": "/api/notes"
                    }
                ]
            }
        ],
        "is_complete": True
    },
    "backend": {
        "endpoints": [
            {
                "endpoint_name": "User Login",
                "description": "Authenticate user with email and password",
                "method": "POST",
                "path": "/api/auth/login",
                "request_body": "{ email: string, password: string }",
                "response": "{ token: string, user: { id, email, name } }",
                "page_context": "Login Page"
            },
            {
                "endpoint_name": "Get All Notes",
                "description": "Retrieve all notes for authenticated user",
                "method": "GET",
                "path": "/api/notes",
                "request_body": "N/A (requires auth token in header)",
                "response": "{ notes: [{ id, title, content, created_at }] }",
                "page_context": "Notes List Page"
            },
            {
                "endpoint_name": "Create Note",
                "description": "Create a new note for user",
                "method": "POST",
                "path": "/api/notes",
                "request_body": "{ title: string, content: string }",
                "response": "{ note: { id, title, content, created_at } }",
                "page_context": "Create Note Page"
            },
            {
                "endpoint_name": "Delete Note",
                "description": "Delete a specific note by ID",
                "method": "DELETE",
                "path": "/api/notes/{id}",
                "request_body": "N/A",
                "response": "{ message: 'Note deleted successfully' }",
                "page_context": "Notes List Page"
            }
        ],
        "is_complete": True
    }
}

if __name__ == "__main__":
    print("Testing Project Generator with Sample Design\n")
    print("=" * 70)
    print("Sample App: Note-Taking Application")
    print(f"Pages: {len(sample_design['frontend']['pages'])}")
    print(f"Endpoints: {len(sample_design['backend']['endpoints'])}")
    print("=" * 70)
    
    # Generate projects
    generate_projects(sample_design)
    
    print("\n\nTest complete! Check the 'frontend' and 'backend' directories.")
