import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from typing import List, Dict, Any

# Load environment variables from .env file
load_dotenv()

def design_application_iterative(description: str, features: List[str]) -> Dict[str, Any]:
    """
    Iterative multi-stage design approach - better quality and more reliable.
    
    Pipeline:
    1. List all pages (simple text)
    2. For each page, add requirements
    3. For each page, identify endpoints needed
    4. For each endpoint, create full API spec
    
    Args:
        description: Detailed description of the application
        features: List of features required in the application
    
    Returns:
        Dictionary containing both frontend and backend designs
    """
    # Create logs directory
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create session log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_log_path = os.path.join(logs_dir, f"session_{timestamp}.log")
    
    def log_and_print(message: str, also_to_file: bool = True):
        """Helper to print and log simultaneously"""
        print(message)
        if also_to_file:
            with open(session_log_path, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
    
    log_and_print("\n" + "="*70)
    log_and_print("ITERATIVE APPLICATION DESIGN WORKFLOW")
    log_and_print("="*70)
    log_and_print(f"\nDescription: {description}")
    log_and_print(f"\nFeatures: {json.dumps(features, indent=2)}")
    log_and_print(f"\nSession Log: {session_log_path}")
    
    # Initialize result structure
    design = {
        "frontend": {"pages": [], "is_complete": False},
        "backend": {"endpoints": [], "is_complete": False}
    }
    
    # Stage 1: List all pages
    log_and_print("\n" + "="*60)
    log_and_print("STAGE 1: LISTING ALL PAGES")
    log_and_print("Agent: Frontend Engineer")
    log_and_print("="*60)
    
    page_list_agent = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.4, max_tokens=2048)
    page_list_prompt = f"""List all pages/screens needed for this application.

Application: {description}
Features: {json.dumps(features)}

Return a simple numbered list with page name and brief description (one line each).
Example format:
1. Login Page - User authentication
2. Dashboard - Main user interface
3. Settings - User preferences

Just the list, no extra text:"""
    
    try:
        log_and_print("\n[Agent Request] Sending prompt to Frontend Engineer...")
        response = page_list_agent.invoke([HumanMessage(content=page_list_prompt)])
        page_list_text = response.content.strip()
        log_and_print(f"\n[Agent Response]\n{page_list_text}")
        
        # Save stage 1 output
        stage1_path = os.path.join(logs_dir, f"stage1_pages_list_{timestamp}.txt")
        with open(stage1_path, 'w', encoding='utf-8') as f:
            f.write(f"STAGE 1: PAGE LIST\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"{'='*60}\n\n")
            f.write(page_list_text)
        log_and_print(f"\n💾 Stage 1 output saved: {stage1_path}")
        
        # Parse the page list
        import re
        page_matches = re.findall(r'\d+\.\s*(.+?)\s*-\s*(.+?)(?:\n|$)', page_list_text)
        
        if not page_matches:
            log_and_print("\n[ERROR] Failed to parse page list")
            return design
        
        # Initialize page objects
        for page_name, page_desc in page_matches:
            design["frontend"]["pages"].append({
                "page_name": page_name.strip(),
                "description": page_desc.strip(),
                "requirements": [],
                "backend_endpoints": []
            })
        
        log_and_print(f"\n✓ {len(design['frontend']['pages'])} pages initialized")
        
    except Exception as e:
        log_and_print(f"\n[ERROR] Stage 1 failed: {e}")
        return design
    
    # Stage 2: Add requirements to each page
    log_and_print("\n" + "="*60)
    log_and_print("STAGE 2: ADDING REQUIREMENTS TO EACH PAGE")
    log_and_print("Agent: Frontend Engineer")
    log_and_print("="*60)
    
    requirements_agent = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.4, max_tokens=2048)
    stage2_results = []
    
    for i, page in enumerate(design["frontend"]["pages"], 1):
        log_and_print(f"\n  [{i}/{len(design['frontend']['pages'])}] Processing: {page['page_name']}")
        
        req_prompt = f"""List UI requirements for this page.

Page: {page['page_name']}
Description: {page['description']}
App Context: {description}
Features: {json.dumps(features)}

Return a JSON array of requirement strings:
["requirement 1", "requirement 2", "requirement 3"]

JSON array only:"""
        
        try:
            response = requirements_agent.invoke([HumanMessage(content=req_prompt)])
            content = response.content.strip().replace("```json", "").replace("```", "").strip()
            requirements = json.loads(content)
            page["requirements"] = requirements
            log_and_print(f"     ✓ Added {len(requirements)} requirements")
            
            stage2_results.append({
                "page": page['page_name'],
                "requirements": requirements,
                "raw_response": content
            })
        except Exception as e:
            log_and_print(f"     ✗ Failed: {e}")
            page["requirements"] = []
    
    # Save stage 2 output
    stage2_path = os.path.join(logs_dir, f"stage2_page_requirements_{timestamp}.json")
    with open(stage2_path, 'w', encoding='utf-8') as f:
        json.dump({
            "stage": "Stage 2: Page Requirements",
            "timestamp": timestamp,
            "pages": design["frontend"]["pages"]
        }, f, indent=2, ensure_ascii=False)
    log_and_print(f"\n💾 Stage 2 output saved: {stage2_path}")
    
    # Stage 3: Identify endpoints for each page
    log_and_print("\n" + "="*60)
    log_and_print("STAGE 3: IDENTIFYING ENDPOINTS FOR EACH PAGE")
    log_and_print("Agent: Frontend Engineer")
    log_and_print("="*60)
    
    endpoint_id_agent = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.4, max_tokens=2048)
    
    for i, page in enumerate(design["frontend"]["pages"], 1):
        log_and_print(f"\n  [{i}/{len(design['frontend']['pages'])}] Processing: {page['page_name']}")
        
        endpoint_prompt = f"""Identify backend endpoints needed for this page.

Page: {page['page_name']}
Description: {page['description']}
Requirements: {json.dumps(page['requirements'])}

Return a JSON array of endpoint objects:
[{{"endpoint_name": "...", "description": "...", "method": "GET|POST|PUT|DELETE", "path": "/api/..."}}]

JSON array only:"""
        
        try:
            response = endpoint_id_agent.invoke([HumanMessage(content=endpoint_prompt)])
            content = response.content.strip().replace("```json", "").replace("```", "").strip()
            endpoints = json.loads(content)
            page["backend_endpoints"] = endpoints
            log_and_print(f"     ✓ Identified {len(endpoints)} endpoints")
        except Exception as e:
            log_and_print(f"     ✗ Failed: {e}")
            page["backend_endpoints"] = []
    
    # Save stage 3 output
    stage3_path = os.path.join(logs_dir, f"stage3_endpoints_identified_{timestamp}.json")
    with open(stage3_path, 'w', encoding='utf-8') as f:
        json.dump({
            "stage": "Stage 3: Endpoints Identified",
            "timestamp": timestamp,
            "pages_with_endpoints": design["frontend"]["pages"]
        }, f, indent=2, ensure_ascii=False)
    log_and_print(f"\n💾 Stage 3 output saved: {stage3_path}")
    
    design["frontend"]["is_complete"] = True
    
    # Stage 3.5: Deduplicate endpoints across all pages
    log_and_print("\n" + "="*60)
    log_and_print("STAGE 3.5: DEDUPLICATING ENDPOINTS")
    log_and_print("Agent: System (Automatic)")
    log_and_print("="*60)
    
    # Collect all unique endpoints from all pages
    endpoint_map = {}  # key: method+path, value: full spec
    total_endpoints_before = 0
    
    for page in design["frontend"]["pages"]:
        total_endpoints_before += len(page["backend_endpoints"])
        for endpoint in page["backend_endpoints"]:
            key = f"{endpoint['method']}:{endpoint['path']}"
            if key not in endpoint_map:
                endpoint_map[key] = {
                    "endpoint_name": endpoint["endpoint_name"],
                    "description": endpoint["description"],
                    "method": endpoint["method"],
                    "path": endpoint["path"],
                    "request_body": "",
                    "response": "",
                    "page_context": page["page_name"]
                }
            else:
                # Add to page context
                if page["page_name"] not in endpoint_map[key]["page_context"]:
                    endpoint_map[key]["page_context"] += f", {page['page_name']}"
    
    duplicates_removed = total_endpoints_before - len(endpoint_map)
    log_and_print(f"\n  Total endpoints identified: {total_endpoints_before}")
    log_and_print(f"  Unique endpoints after deduplication: {len(endpoint_map)}")
    log_and_print(f"  Duplicates removed: {duplicates_removed}")
    
    # Save stage 3.5 output
    stage35_path = os.path.join(logs_dir, f"stage3.5_unique_endpoints_{timestamp}.json")
    with open(stage35_path, 'w', encoding='utf-8') as f:
        json.dump({
            "stage": "Stage 3.5: Endpoint Deduplication",
            "timestamp": timestamp,
            "total_endpoints_before": total_endpoints_before,
            "unique_endpoints": len(endpoint_map),
            "duplicates_removed": duplicates_removed,
            "endpoints": list(endpoint_map.values())
        }, f, indent=2, ensure_ascii=False)
    log_and_print(f"\n💾 Stage 3.5 output saved: {stage35_path}")
    
    # Stage 4: Create full API specs for each endpoint (batch by resource)
    log_and_print("\n" + "="*60)
    log_and_print("STAGE 4: CREATING FULL API SPECIFICATIONS")
    log_and_print("Agent: Backend Engineer")
    log_and_print("="*60)
    
    backend_spec_agent = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.4, max_tokens=4096)
    
    # Group endpoints by resource (e.g., /api/cart, /api/menu, /api/user)
    resource_groups = {}
    for key, endpoint in endpoint_map.items():
        # Extract resource from path (e.g., /api/cart/items -> cart)
        path_parts = endpoint['path'].strip('/').split('/')
        resource = path_parts[1] if len(path_parts) > 1 else path_parts[0]
        
        if resource not in resource_groups:
            resource_groups[resource] = []
        resource_groups[resource].append((key, endpoint))
    
    log_and_print(f"\n  Grouped {len(endpoint_map)} endpoints into {len(resource_groups)} resources")
    log_and_print(f"  Resources: {', '.join(resource_groups.keys())}")
    
    # Process each resource group as a batch
    batch_num = 0
    batch_interactions = []
    
    for resource, endpoints_list in resource_groups.items():
        batch_num += 1
        log_and_print(f"\n  [Batch {batch_num}/{len(resource_groups)}] Processing resource: /{resource} ({len(endpoints_list)} endpoints)")
        
        # Build batch prompt with all endpoints in this resource
        endpoints_info = []
        for idx, (key, ep) in enumerate(endpoints_list, 1):
            endpoints_info.append(f"""
{idx}. Endpoint: {ep['endpoint_name']}
   Method: {ep['method']}
   Path: {ep['path']}
   Description: {ep['description']}
   Used by pages: {ep['page_context']}""")
        
        batch_prompt = f"""Create full API specifications for ALL endpoints in the /{resource} resource.

Application Context: {description}

Endpoints to specify:
{"".join(endpoints_info)}

Return a JSON array with specifications for each endpoint in order:
[
  {{"request_body": "describe parameters/body for endpoint 1", "response": "describe response structure for endpoint 1"}},
  {{"request_body": "describe parameters/body for endpoint 2", "response": "describe response structure for endpoint 2"}},
  ...
]

JSON array only:"""
        
        try:
            log_and_print(f"\n[Agent Request] Sending batch to Backend Engineer for /{resource}...")
            response = backend_spec_agent.invoke([HumanMessage(content=batch_prompt)])
            content = response.content.strip().replace("```json", "").replace("```", "").strip()
            specs = json.loads(content)
            
            # Apply specs to endpoints
            for idx, (key, endpoint) in enumerate(endpoints_list):
                if idx < len(specs):
                    endpoint["request_body"] = specs[idx].get("request_body", "N/A")
                    endpoint["response"] = specs[idx].get("response", "N/A")
                else:
                    endpoint["request_body"] = "N/A"
                    endpoint["response"] = "N/A"
            
            log_and_print(f"     ✓ Batch complete: {len(specs)} specifications generated")
            
            batch_interactions.append({
                "resource": resource,
                "endpoints_count": len(endpoints_list),
                "request": batch_prompt,
                "response": content,
                "success": True
            })
        except Exception as e:
            log_and_print(f"     ✗ Batch failed: {e}")
            # Fallback to N/A for all endpoints in this batch
            for key, endpoint in endpoints_list:
                endpoint["request_body"] = "N/A"
                endpoint["response"] = "N/A"
            
            batch_interactions.append({
                "resource": resource,
                "endpoints_count": len(endpoints_list),
                "error": str(e),
                "success": False
            })
    
    # Save stage 4 output
    stage4_path = os.path.join(logs_dir, f"stage4_api_specifications_{timestamp}.json")
    with open(stage4_path, 'w', encoding='utf-8') as f:
        json.dump({
            "stage": "Stage 4: API Specifications",
            "timestamp": timestamp,
            "resource_groups": len(resource_groups),
            "total_endpoints": len(endpoint_map),
            "batch_interactions": batch_interactions,
            "endpoints": list(endpoint_map.values())
        }, f, indent=2, ensure_ascii=False)
    log_and_print(f"\n💾 Stage 4 output saved: {stage4_path}")
    
    design["backend"]["endpoints"] = list(endpoint_map.values())
    design["backend"]["is_complete"] = True
    
    # Save final complete design
    final_design_path = os.path.join(logs_dir, f"final_design_{timestamp}.json")
    with open(final_design_path, 'w', encoding='utf-8') as f:
        json.dump(design, f, indent=2, ensure_ascii=False)
    log_and_print(f"\n💾 Final design saved: {final_design_path}")
    
    log_and_print("\n" + "="*70)
    log_and_print("ITERATIVE DESIGN WORKFLOW COMPLETED")
    log_and_print("="*70)
    log_and_print(f"\n✓ {len(design['frontend']['pages'])} pages with full specifications")
    log_and_print(f"✓ {len(design['backend']['endpoints'])} unique API endpoints")
    log_and_print(f"\n📁 All logs and outputs saved in: {logs_dir}/")
    log_and_print(f"📄 Session log: {session_log_path}")
    
    return design


def design_application(description: str, features: List[str]) -> Dict[str, Any]:
    """
    Main function that coordinates frontend and backend agents to design an application.
    Uses iterative approach for better quality and reliability.
    
    Pipeline:
    1. List all pages (simple text)
    2. For each page, add requirements
    3. For each page, identify endpoints needed
    4. For each endpoint, create full API spec
    
    Args:
        description: Detailed description of the application
        features: List of features required in the application
    
    Returns:
        Dictionary containing both frontend and backend designs:
        {
            "frontend": {
                "pages": [...],
                "is_complete": bool
            },
            "backend": {
                "endpoints": [...],
                "is_complete": bool
            }
        }
    """
    return design_application_iterative(description, features)
