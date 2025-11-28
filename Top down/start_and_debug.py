"""
Standalone script to start and debug existing React and Flask projects.
Run this after projects have been generated and implemented.
"""

import os
import asyncio
from debugging_agents import run_debugging_agents

# Get the current directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define project paths
react_path = os.path.join(base_dir, "frontend")
flask_path = os.path.join(base_dir, "backend")

# Check if projects exist
if not os.path.exists(react_path):
    print(f"Error: React project not found at {react_path}")
    exit(1)

if not os.path.exists(flask_path):
    print(f"Error: Flask project not found at {flask_path}")
    exit(1)

print("Found both projects:")
print(f"  React: {react_path}")
print(f"  Flask: {flask_path}")

# Run debugging agents
asyncio.run(run_debugging_agents(react_path, flask_path))
