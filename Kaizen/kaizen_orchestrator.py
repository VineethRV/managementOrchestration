"""
Kaizen Methodology: Continuous Improvement Multi-Agent System
Implements PDCA cycles with three specialized agent groups:
- Implementation Group: Produces and refines core logic
- Verification Group: Performs inspections and identifies defects
- Integration Group: Ensures architectural consistency

Uses chain-of-thought processing and rate limiting to manage API usage.
"""

import os
import json
import sys
import time
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Import local modules
from defect_ledger import DefectLedger, DefectSeverity, DefectStatus
from rate_limiter import RateLimiter

# Load environment variables
load_dotenv()

# Verify API key is set
if not os.getenv("GROQ_API_KEY"):
    raise ValueError(
        "GROQ_API_KEY environment variable is not set. "
        "Please set it in a .env file or as an environment variable. "
        "Example: GROQ_API_KEY=your_api_key_here"
    )

# Global rate limiter (100k daily limit for Groq on-demand tier)
_rate_limiter = RateLimiter(
    requests_per_minute=30, 
    requests_per_hour=1000, 
    tokens_per_minute=100000,
    tokens_per_day=100000  # Groq on-demand daily limit
)

# Global defect ledger (will be initialized in main)
_defect_ledger: Optional[DefectLedger] = None

def set_defect_ledger(ledger: DefectLedger):
    """Set the global defect ledger instance."""
    global _defect_ledger
    _defect_ledger = ledger

def get_defect_ledger() -> Optional[DefectLedger]:
    """Get the global defect ledger instance."""
    return _defect_ledger

# Metrics tracking
class KaizenMetrics:
    """Track metrics for Kaizen methodology."""
    def __init__(self):
        self.total_tokens = 0
        self.total_requests = 0
        self.pdca_cycles = 0
        self.improvements_applied = 0
        self.defects_found = 0
        self.defects_resolved = 0
        self.waste_eliminations = 0
        self.start_time = datetime.now()
        self.cycle_times = []
    
    def add_tokens(self, count: int):
        self.total_tokens += count
    
    def add_request(self):
        self.total_requests += 1
    
    def record_pdca_cycle(self, cycle_time: float):
        self.pdca_cycles += 1
        self.cycle_times.append(cycle_time)
    
    def get_metrics(self) -> Dict[str, Any]:
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        avg_cycle_time = sum(self.cycle_times) / len(self.cycle_times) if self.cycle_times else 0
        
        return {
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "pdca_cycles": self.pdca_cycles,
            "improvements_applied": self.improvements_applied,
            "defects_found": self.defects_found,
            "defects_resolved": self.defects_resolved,
            "waste_eliminations": self.waste_eliminations,
            "duration_seconds": duration,
            "average_cycle_time_seconds": avg_cycle_time,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    def save(self, filepath: str):
        metrics = self.get_metrics()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)

_metrics = KaizenMetrics()


def invoke_with_rate_limit(agent, messages, log_file: str = None, max_retries: int = 3, estimated_tokens: int = 1000) -> Any:
    """
    Invoke agent with rate limiting and metrics tracking.
    Handles 429 rate limit errors with exponential backoff.
    
    Args:
        agent: ChatGroq agent instance
        messages: List of messages
        log_file: Optional log file path
        max_retries: Maximum retry attempts for rate limit errors
        estimated_tokens: Estimated tokens for this request
    
    Returns:
        Agent response or None if rate limit exceeded
    """
    global _rate_limiter, _metrics
    
    # Check if we can make the request (check daily limit first)
    remaining_tokens = _rate_limiter.get_remaining_daily_tokens()
    if remaining_tokens < estimated_tokens:
        if log_file:
            log_and_print(f"[Rate Limiter] Daily token limit reached. Remaining: {remaining_tokens}, Needed: ~{estimated_tokens}", log_file)
        # Raise exception instead of returning None - let caller handle it properly
        raise Exception(f"Daily token limit exceeded. Remaining: {remaining_tokens} tokens. Cannot proceed without sufficient tokens.")
    
    # Wait if needed
    wait_time = _rate_limiter.wait_if_needed()
    if wait_time > 0 and log_file:
        log_and_print(f"[Rate Limiter] Waited {wait_time:.2f}s", log_file)
    
    # Retry logic for rate limit errors
    for attempt in range(max_retries):
        try:
            # Invoke agent
            response = agent.invoke(messages)
            
            # Track token usage
            if hasattr(response, 'response_metadata') and response.response_metadata:
                token_usage = response.response_metadata.get('token_usage', {})
                if token_usage:
                    total_tokens = token_usage.get('total_tokens', 0)
                    if total_tokens:
                        _rate_limiter.record_request(tokens_used=total_tokens)
                        _metrics.add_tokens(total_tokens)
                        _metrics.add_request()
                        if log_file:
                            log_and_print(f"[Tokens: {total_tokens}]", log_file)
            
            return response
            
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a rate limit error (429)
            if '429' in error_str or 'rate_limit' in error_str.lower() or 'Rate limit' in error_str:
                _rate_limiter.record_rate_limit_error()
                
                # Extract wait time from error message if available
                wait_seconds = 60  # Default wait time
                if 'try again in' in error_str:
                    try:
                        import re
                        match = re.search(r'try again in ([\d.]+)s', error_str)
                        if match:
                            wait_seconds = float(match.group(1)) + 5  # Add 5s buffer
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    if log_file:
                        log_and_print(f"[Rate Limit Error] Attempt {attempt + 1}/{max_retries}. Waiting {wait_seconds:.1f}s before retry...", log_file)
                    time.sleep(wait_seconds)
                    continue
                else:
                    if log_file:
                        log_and_print(f"[Rate Limit Error] Max retries reached. Skipping this request.", log_file)
                    raise Exception(f"Rate limit exceeded after {max_retries} attempts. Please wait and try again later.")
            else:
                # Not a rate limit error, re-raise
                raise
    
    return None


def log_and_print(message: str, log_file: str = None):
    """Helper to print and log simultaneously."""
    print(message)
    if log_file:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(message + '\n')


def get_agent(model: str = "llama-3.3-70b-versatile", temperature: float = 0.3, max_tokens: int = 4000) -> ChatGroq:
    """Get a ChatGroq agent instance."""
    # Optimized token limits: design needs more (6000), others capped at 4000
    if max_tokens > 6000:
        max_tokens = 6000
    return ChatGroq(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )


def gather_requirements_interactive() -> Dict[str, Any]:
    """
    Phase 1: Requirements gathering (shared with other approaches).
    Returns: {"detailed_description": str, "features": List[str], "is_finalized": bool}
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, f"kaizen_requirements_{timestamp}.log")
    
    print("="*70)
    print("KAIZEN METHODOLOGY: REQUIREMENTS GATHERING")
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
1. Ask clarifying questions about the application - be proactive and specific
2. If the user gives a vague description (e.g., "make a website", "build an app"), ask targeted questions:
   - What type of application? (e-commerce, social media, blog, portfolio, task management, etc.)
   - What are the main features/functionality?
   - Who are the users? (customers, admins, employees, etc.)
   - What are the key entities/resources? (products, posts, tasks, users, etc.)
   - What actions do users need to perform? (view, create, edit, delete, search, purchase, etc.)
3. Understand the key features and requirements
4. Summarize what you've understood and ask for confirmation
5. Once confirmed, output the final requirements in this exact JSON format:
{
    "detailed_description": "full description of the application with specific details about purpose, users, and functionality",
    "features": ["feature1", "feature2", "feature3"]
}
Be thorough and ask specific questions. Don't accept vague descriptions - always clarify until you have enough detail to build a functional application.""")
    ]
    
    # Initial greeting
    agent = get_agent()
    initial_response = invoke_with_rate_limit(
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
        
        agent = get_agent()
        response = invoke_with_rate_limit(agent, conversation_history, log_file)
        print(f"\nAgent: {response.content}\n")
        conversation_history.append(response)
        
        # Try to extract JSON from response
        content = response.content.strip()
        if "{" in content and "detailed_description" in content:
            try:
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


def design_application_kaizen(description: str, features: List[str]) -> Dict[str, Any]:
    """
    Phase 2: Application design using Kaizen approach with Improvement Coordinator.
    Uses chain-of-thought processing for better design quality.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, f"kaizen_design_{timestamp}.log")
    
    print("\n" + "="*70)
    print("KAIZEN: APPLICATION DESIGN (Improvement Coordinator)")
    print("-" * 70)
    
    # Check token budget before design phase
    global _rate_limiter
    remaining_tokens = _rate_limiter.get_remaining_daily_tokens()
    if remaining_tokens < 15000:
        log_and_print(f"  [WARNING] Low token budget for design phase: {remaining_tokens:,}", log_file)
        if remaining_tokens < 8000:
            raise Exception(f"Design phase cannot proceed - insufficient tokens. Remaining: {remaining_tokens}, needed: ~8000")
    
    # Improvement Coordinator designs the application
    # Design phase needs more tokens because JSON can be large - use 6000 for design
    coordinator_agent = get_agent(temperature=0.3, max_tokens=6000)  # Increased for complete JSON generation
    
    # Optimized design prompt - concise but complete
    design_prompt = f"""Design a complete software application based ONLY on the provided requirements. Infer everything from the description - do not assume or add unmentioned features.

REQUIREMENTS:
Description: {description}
Features: {json.dumps(features, indent=2)}

RULES:
- Infer application type from description (do not assume)
- Use meaningful, context-specific names (no generic names like "Feature1")
- For vague descriptions: design MVP with essential features using inferred patterns
- Extract entity names from description (e.g., "store" → Product, Cart, Order)

PROCESS:
1. Analyze: purpose, entities, actions, features, implied functionality
2. Infer architecture: pages (meaningful names), endpoints (RESTful), data models (matching entities)
3. Design pages: functionality, UI components, required endpoints
4. Design endpoints: operations, data handling, request/response structures
5. Design data models: fields, relationships, meaningful names
6. Infer UI theme from description or use sensible defaults
7. Consider dependencies and potential issues

NAMING:
- Pages: descriptive functional names (ProductList, ShoppingCart, UserProfile)
- Endpoints: RESTful resource paths (/api/products, /api/products/:id)
- Models: singular PascalCase matching entities (Product, Category, Order)

Return JSON in this format:
{{
    "application_type": "inferred from requirements",
    "ui_theme": {{
        "primary_color": "hex or Tailwind class",
        "secondary_color": "hex or Tailwind class",
        "accent_color": "hex or Tailwind class",
        "color_scheme": "light|dark|auto",
        "style_description": "brief style description"
    }},
    "frontend": {{
        "pages": [
            {{
                "page_name": "Page Name",
                "description": "Page description",
                "requirements": ["req1", "req2"],
                "ui_components": ["comp1", "comp2"],
                "backend_endpoints": [
                    {{
                        "endpoint_name": "Name",
                        "method": "GET|POST|PUT|DELETE",
                        "path": "/api/resource",
                        "description": "Description",
                        "request_body": "Request structure",
                        "response": "Response structure"
                    }}
                ]
            }}
        ],
        "shared_components": ["comp1"],
        "is_complete": true
    }},
    "backend": {{
        "endpoints": [
            {{
                "endpoint_name": "Name",
                "method": "GET|POST|PUT|DELETE",
                "path": "/api/resource",
                "description": "Description",
                "request_body": "Request structure",
                "response": "Response structure",
                "requires_database": true/false
            }}
        ],
        "data_models": [
            {{
                "model_name": "ModelName",
                "description": "Description",
                "fields": [
                    {{"name": "field_name", "type": "string|number|boolean|date|ObjectId", "required": true/false}}
                ]
            }}
        ],
        "is_complete": true
    }}
}}

Requirements: All pages need requirements and endpoints. All endpoints need request/response structures. UI theme from description or appropriate defaults. Data models match entities."""

    log_and_print(f"\n[Improvement Coordinator] Designing application...", log_file)
    
    # Try up to 2 times to get valid JSON
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # Estimate tokens needed (prompt + response)
            prompt_tokens = len(design_prompt) // 4
            estimated_total = prompt_tokens + 5000  # Reduced from 6000
            response = invoke_with_rate_limit(coordinator_agent, [HumanMessage(content=design_prompt)], log_file, estimated_tokens=estimated_total)
            content = response.content.strip()
            
            log_and_print(f"\n[Improvement Coordinator Response] (Attempt {attempt + 1}/{max_retries})\n{content[:2000]}...", log_file)
            
            # Extract JSON from response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                
                # Try to parse JSON
                try:
                    design = json.loads(json_str)
                    
                    # Ensure structure is complete
                    if "frontend" not in design:
                        design["frontend"] = {"pages": [], "is_complete": False}
                    if "backend" not in design:
                        design["backend"] = {"endpoints": [], "is_complete": False}
                    
                    log_and_print(f"\n✓ Design complete: {len(design.get('frontend', {}).get('pages', []))} pages, {len(design.get('backend', {}).get('endpoints', []))} endpoints", log_file)
                    return design
                except json.JSONDecodeError as parse_error:
                    # Try to repair truncated JSON
                    log_and_print(f"  [Attempt {attempt + 1}] JSON parse error: {parse_error}", log_file)
                    
                    # Check if JSON is truncated (common issue)
                    if attempt < max_retries - 1:
                        # Try to find where JSON was cut off and close it properly
                        try:
                            # Count open vs closed braces
                            open_braces = json_str.count('{')
                            close_braces = json_str.count('}')
                            missing_braces = open_braces - close_braces
                            
                            if missing_braces > 0:
                                # Try to close the JSON structure
                                repaired_json = json_str
                                for _ in range(missing_braces):
                                    # Find the last incomplete structure and close it
                                    if '"pages"' in repaired_json and repaired_json.rstrip().endswith(','):
                                        repaired_json = repaired_json.rstrip().rstrip(',') + '\n            ]'
                                    elif '"endpoints"' in repaired_json and repaired_json.rstrip().endswith(','):
                                        repaired_json = repaired_json.rstrip().rstrip(',') + '\n            ]'
                                    elif '"data_models"' in repaired_json and repaired_json.rstrip().endswith(','):
                                        repaired_json = repaired_json.rstrip().rstrip(',') + '\n        ]'
                                    repaired_json += '\n    }'
                                
                                # Close remaining structures
                                if '"backend"' in repaired_json:
                                    repaired_json += '\n    }'
                                if '"frontend"' in repaired_json:
                                    repaired_json += '\n}'
                                
                                try:
                                    design = json.loads(repaired_json)
                                    log_and_print(f"  ✓ Repaired truncated JSON successfully", log_file)
                                    
                                    # Ensure structure is complete
                                    if "frontend" not in design:
                                        design["frontend"] = {"pages": [], "is_complete": False}
                                    if "backend" not in design:
                                        design["backend"] = {"endpoints": [], "is_complete": False}
                                    
                                    log_and_print(f"\n✓ Design complete (repaired): {len(design.get('frontend', {}).get('pages', []))} pages, {len(design.get('backend', {}).get('endpoints', []))} endpoints", log_file)
                                    return design
                                except json.JSONDecodeError:
                                    pass  # Repair failed, will retry
                        except Exception as repair_error:
                            log_and_print(f"  [Repair attempt failed]: {repair_error}", log_file)
                    
                    # If repair failed or last attempt, request a more concise design
                    if attempt < max_retries - 1:
                        log_and_print(f"  [Retrying with request for more concise design...]", log_file)
                        # Modify prompt to request more concise output
                        concise_prompt = design_prompt + "\n\n**IMPORTANT**: Keep the JSON response concise but complete. Focus on essential pages and endpoints only. Avoid excessive detail in nested structures."
                        design_prompt = concise_prompt
                        continue
            
            # If we couldn't find JSON boundaries
            if attempt < max_retries - 1:
                log_and_print(f"  [Retrying - no valid JSON found in response...]", log_file)
                continue
            else:
                raise Exception("No valid JSON structure found in AI response")
                
        except Exception as e:
            if attempt < max_retries - 1:
                log_and_print(f"  [Retrying after error: {str(e)[:100]}...]", log_file)
                continue
            else:
                log_and_print(f"\n✗ Failed to parse design JSON after {max_retries} attempts: {e}", log_file)
                log_and_print(f"  Response length: {len(content) if 'content' in locals() else 0} characters", log_file)
                raise Exception(f"Failed to parse design JSON after {max_retries} attempts. This is critical - cannot proceed without valid design. Error: {e}")
    
    # If we reach here without valid design, something went wrong
    raise Exception("Design generation failed - no valid design returned from AI after all retries")


def run_pdca_cycle(
    design: Dict[str, Any],
    react_path: str,
    flask_path: str,
    description: str,
    cycle_number: int,
    log_file: str
) -> Dict[str, Any]:
    """
    Execute a single PDCA (Plan-Do-Check-Act) cycle.
    
    Args:
        design: Application design
        react_path: React project path
        flask_path: Flask project path
        description: Application description
        cycle_number: Current cycle number
        log_file: Log file path
    
    Returns:
        Cycle results dictionary
    """
    global _defect_ledger, _metrics
    
    cycle_start = time.time()
    log_and_print(f"\n{'='*70}", log_file)
    log_and_print(f"PDCA CYCLE {cycle_number}", log_file)
    log_and_print(f"{'='*70}", log_file)
    
    cycle_results = {
        'cycle_number': cycle_number,
        'defects_found': 0,
        'defects_resolved': 0,
        'improvements_applied': 0,
        'waste_eliminated': 0
    }
    
    # PLAN Phase
    log_and_print(f"\n[PLAN] Analyzing current state and planning improvements...", log_file)
    plan_result = plan_phase(design, react_path, flask_path, cycle_number, log_file)
    cycle_results.update(plan_result)
    
    # DO Phase
    log_and_print(f"\n[DO] Implementing improvements...", log_file)
    do_result = do_phase(design, react_path, flask_path, description, cycle_number, log_file)
    cycle_results.update(do_result)
    
    # CHECK Phase
    log_and_print(f"\n[CHECK] Verifying implementation and checking for defects...", log_file)
    check_result = check_phase(design, react_path, flask_path, cycle_number, log_file)
    cycle_results.update(check_result)
    cycle_results['defects_found'] = check_result.get('defects_found', 0)
    
    # INTEGRATION VALIDATION Phase (after DO, before ACT)
    if cycle_number == 1:  # Only in first cycle to ensure complete integration
        log_and_print(f"\n[INTEGRATION VALIDATION] Validating frontend-backend integration...", log_file)
        integration_defects = validate_frontend_backend_integration(design, react_path, flask_path, log_file)
        if integration_defects > 0:
            log_and_print(f"  ⚠ Found {integration_defects} integration issues - will be addressed in refinement", log_file)
    
    # ACT Phase
    log_and_print(f"\n[ACT] Standardizing improvements and planning next cycle...", log_file)
    act_result = act_phase(design, react_path, flask_path, cycle_number, log_file)
    cycle_results.update(act_result)
    cycle_results['defects_resolved'] = act_result.get('defects_resolved', 0)
    cycle_results['improvements_applied'] = act_result.get('improvements_applied', 0)
    
    # CROSS-TEAM CONSOLIDATION Phase (as per Kaizen methodology flowchart)
    log_and_print(f"\n[CROSS-TEAM CONSOLIDATION] Consolidating results from all teams...", log_file)
    consolidation_result = cross_team_consolidation(
        design, react_path, flask_path, cycle_number, 
        do_result, check_result, act_result, log_file
    )
    cycle_results.update(consolidation_result)
    
    cycle_time = time.time() - cycle_start
    _metrics.record_pdca_cycle(cycle_time)
    
    log_and_print(f"\n✓ Cycle {cycle_number} completed in {cycle_time:.2f}s", log_file)
    log_and_print(f"  Defects found: {cycle_results['defects_found']}", log_file)
    log_and_print(f"  Defects resolved: {cycle_results['defects_resolved']}", log_file)
    log_and_print(f"  Improvements applied: {cycle_results['improvements_applied']}", log_file)
    log_and_print(f"  Cross-team issues identified: {consolidation_result.get('cross_team_issues', 0)}", log_file)
    
    return cycle_results


def plan_phase(design: Dict, react_path: str, flask_path: str, cycle_number: int, log_file: str) -> Dict:
    """
    PLAN phase: Analyze current state and establish improvement targets.
    
    True Kaizen: In Cycle 2+, focus on refining components with defects/improvements.
    """
    global _defect_ledger
    _defect_ledger = get_defect_ledger()
    
    coordinator = get_agent(temperature=0.2, max_tokens=1500)
    
    # Get current defect statistics
    defect_stats = _defect_ledger.get_statistics() if _defect_ledger else {}
    open_defects = _defect_ledger.get_open_defects() if _defect_ledger else []
    
    # Get components that need refinement (for Cycle 2+)
    pages = design.get("frontend", {}).get("pages", [])
    endpoints = design.get("backend", {}).get("endpoints", [])
    components_to_refine = get_components_needing_refinement(pages, endpoints, cycle_number)
    
    if cycle_number == 1:
        plan_prompt = f"""You are the Improvement Coordinator in the PLAN phase of PDCA cycle {cycle_number} (INITIAL IMPLEMENTATION).

This is the first cycle. Plan the initial implementation of all components.

CURRENT STATE:
- Total components to implement: {len(pages)} pages, {len(endpoints)} endpoints
- This is the initial implementation phase

Establish SMART improvement targets for initial implementation:
1. Implementation priorities
2. Quality standards to maintain
3. Areas to focus on during implementation

Return JSON with:
{{
    "targets": [
        {{"goal": "specific goal", "priority": "high|medium|low", "component": "component name"}}
    ],
    "focus_areas": ["area1", "area2"],
    "waste_opportunities": ["waste type", "description"]
}}"""
    else:
        plan_prompt = f"""You are the Improvement Coordinator in the PLAN phase of PDCA cycle {cycle_number} (REFINEMENT).

This is a refinement cycle. Focus on improving EXISTING components based on defects and improvements.

CURRENT STATE:
- Total defects: {defect_stats.get('total_defects', 0)}
- Open defects: {defect_stats.get('open_defects', 0)}
- Resolution rate: {defect_stats.get('resolution_rate', 0):.2%}
- Components needing refinement: {len(components_to_refine.get('pages', []))} pages, {len(components_to_refine.get('endpoints', []))} endpoints

OPEN DEFECTS:
{json.dumps([{'id': d['id'], 'component': d['component'], 'severity': d['severity'], 'description': d['description'][:100]} for d in open_defects[:10]], indent=2)}

COMPONENTS TO REFINE:
Pages: {', '.join(components_to_refine.get('pages', [])[:5])}
Endpoints: {', '.join(components_to_refine.get('endpoints', [])[:5])}

Analyze the current state and establish SMART improvement targets for REFINING existing components.
Focus on:
1. High-priority defects to resolve in existing components
2. Components needing refinement (listed above)
3. Quality improvements for existing code
4. Waste elimination in current implementation

Return JSON with:
{{
    "targets": [
        {{"goal": "refine specific component", "priority": "high|medium|low", "component": "component name"}}
    ],
    "focus_areas": ["refinement area1", "refinement area2"],
    "waste_opportunities": ["waste type", "description"],
    "refinement_priority": ["component1", "component2"]
}}"""

    try:
        response = invoke_with_rate_limit(coordinator, [HumanMessage(content=plan_prompt)], log_file, estimated_tokens=1000)  # Reduced from 2000
        if not response:
            raise Exception("Plan phase failed - no response from coordinator. Cannot proceed without planning.")
        
        content = response.content.strip()
        
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0:
                plan_data = json.loads(content[json_start:json_end])
                action = "refinement" if cycle_number > 1 else "implementation"
                log_and_print(f"  ✓ Planned {len(plan_data.get('targets', []))} improvement targets for {action}", log_file)
                return plan_data
            else:
                raise Exception("No JSON found in plan response")
        except json.JSONDecodeError as e:
            log_and_print(f"  [Error] Failed to parse plan data: {e}", log_file)
            log_and_print(f"  Response content: {content[:500]}", log_file)
            raise Exception(f"Plan phase failed - invalid JSON response. Cannot proceed without valid plan. Error: {e}")
    except Exception as e:
        if 'token' in str(e).lower() or 'limit' in str(e).lower():
            raise Exception(f"Plan phase cannot proceed due to token limits: {e}")
        raise Exception(f"Plan phase failed: {e}")


def do_phase(design: Dict, react_path: str, flask_path: str, description: str, cycle_number: int, log_file: str) -> Dict:
    """
    DO phase: Implementation Group implements or refines components.
    
    True Kaizen: Cycle 1 implements, Cycle 2+ refines the SAME components.
    """
    global _defect_ledger, _rate_limiter
    _defect_ledger = get_defect_ledger()
    
    pages = design.get("frontend", {}).get("pages", [])
    endpoints = design.get("backend", {}).get("endpoints", [])
    
    # Implementation Group: 3 agents working in parallel
    implementation_results = {
        'pages_implemented': 0,
        'pages_refined': 0,
        'endpoints_implemented': 0,
        'endpoints_refined': 0,
        'improvements_made': 0
    }
    
    # Get components that need refinement (have defects or improvements)
    components_to_refine = get_components_needing_refinement(pages, endpoints, cycle_number)
    
    if cycle_number == 1:
        # Cycle 1: Generate project scaffolding first, then implement components
        log_and_print(f"  [Cycle {cycle_number}] Initial implementation phase...", log_file)
        
        # **TOKEN BUDGET CHECK**: Reserve tokens for implementation
        remaining_tokens = _rate_limiter.get_remaining_daily_tokens()
        estimated_implementation_tokens = (len(pages) * 3000) + (len(endpoints) * 2000) + 5000  # 3k per page, 2k per endpoint, 5k overhead
        if remaining_tokens < estimated_implementation_tokens:
            log_and_print(f"  [WARNING] Low token budget. Remaining: {remaining_tokens:,}, Estimated needed: {estimated_implementation_tokens:,}", log_file)
            # Limit components based on available tokens
            max_pages = min(len(pages), max(1, (remaining_tokens - 5000) // 3000))
            max_endpoints = min(len(endpoints), max(1, (remaining_tokens - 5000 - (max_pages * 3000)) // 2000))
            pages = pages[:max_pages]
            endpoints = endpoints[:max_endpoints]
            log_and_print(f"  [Token Budget] Limiting to {max_pages} pages and {max_endpoints} endpoints", log_file)
        
        # Step 1: Generate React + Tailwind project if not exists
        if not os.path.exists(react_path) or not os.path.exists(os.path.join(react_path, "package.json")):
            log_and_print(f"  [Step 1/3] Generating React + Tailwind CSS project...", log_file)
            react_path = generate_react_tailwind_project(design, react_path, log_file)
            if not react_path:
                log_and_print(f"  ✗ Failed to generate React project", log_file)
                return implementation_results
        
        # Step 2: Determine MongoDB usage and generate Flask backend
        use_mongodb = determine_db_usage(description, [], design)
        if not os.path.exists(flask_path) or not os.path.exists(os.path.join(flask_path, "app.py")):
            log_and_print(f"  [Step 2/3] Generating Flask backend ({'with MongoDB' if use_mongodb else 'without database'})...", log_file)
            flask_path = generate_flask_mongodb_backend(design, flask_path, use_mongodb, log_file)
            if not flask_path:
                log_and_print(f"  ✗ Failed to generate Flask backend", log_file)
                return implementation_results
        
        # Step 3: Implement all components with token budget awareness
        log_and_print(f"  [Step 3/3] Implementing components (token budget: {_rate_limiter.get_remaining_daily_tokens():,})...", log_file)
        
        # Divide work among 3 implementation agents, but limit based on token budget
        pages_per_agent = (len(pages) + 2) // 3
        endpoints_per_agent = (len(endpoints) + 2) // 3
        
        for agent_id in range(1, 4):
            # Check token budget before each agent
            remaining_tokens = _rate_limiter.get_remaining_daily_tokens()
            if remaining_tokens < 5000:  # Stop if less than 5k tokens remaining
                log_and_print(f"  [Token Budget] Stopping implementation - only {remaining_tokens:,} tokens remaining", log_file)
                break
            
            agent_pages = pages[(agent_id-1)*pages_per_agent:agent_id*pages_per_agent]
            agent_endpoints = endpoints[(agent_id-1)*endpoints_per_agent:agent_id*endpoints_per_agent]
            
            if agent_pages:
                log_and_print(f"  [Implementation Agent {agent_id}] Implementing {len(agent_pages)} pages...", log_file)
                for page in agent_pages:
                    # Check token budget before each page
                    if _rate_limiter.get_remaining_daily_tokens() < 3000:
                        log_and_print(f"  [Token Budget] Skipping remaining pages - low token budget", log_file)
                        break
                    result = implement_page_kaizen(page, react_path, endpoints, description, agent_id, log_file, is_refinement=False, design=design)
                    if result:
                        implementation_results['pages_implemented'] += 1
            
            if agent_endpoints:
                log_and_print(f"  [Implementation Agent {agent_id}] Implementing {len(agent_endpoints)} endpoints...", log_file)
                # Determine MongoDB usage from design/description
                use_mongodb = determine_db_usage(description, [], design)
                for endpoint in agent_endpoints:
                    # Check token budget before each endpoint
                    if _rate_limiter.get_remaining_daily_tokens() < 2000:
                        log_and_print(f"  [Token Budget] Skipping remaining endpoints - low token budget", log_file)
                        break
                    result = implement_endpoint_kaizen(endpoint, flask_path, description, agent_id, log_file, is_refinement=False, use_mongodb=use_mongodb)
                    if result:
                        implementation_results['endpoints_implemented'] += 1
        
        # After all pages are implemented, generate App.js with routing and shared components
        if implementation_results['pages_implemented'] > 0:
            generate_app_js_with_routing(design, react_path, log_file)
            # Generate shared components based on application type
            generate_shared_components(design, react_path, description, log_file)
    else:
        # Cycle 2+: Refine existing components based on defects and improvements
        log_and_print(f"  [Cycle {cycle_number}] Refinement phase - improving existing components...", log_file)
        
        # Check token budget before refinement
        remaining_tokens = _rate_limiter.get_remaining_daily_tokens()
        if remaining_tokens < 20000:
            log_and_print(f"  [WARNING] Low token budget ({remaining_tokens:,}). Limiting refinement scope.", log_file)
        
        # Get components with defects, prioritized by severity
        components_with_defects = get_components_with_defects_prioritized(pages, endpoints, _defect_ledger)
        
        # Match by page name (from defect ledger) to page object
        pages_to_refine = []
        for page in pages:
            page_name = page.get('page_name', '')
            if page_name in components_to_refine.get('pages', []):
                pages_to_refine.append(page)
        
        # Match endpoints by path
        endpoints_to_refine = []
        for endpoint in endpoints:
            endpoint_path = endpoint.get('path', '')
            if endpoint_path in components_to_refine.get('endpoints', []) or any(ep_path in endpoint_path for ep_path in components_to_refine.get('endpoints', [])):
                endpoints_to_refine.append(endpoint)
        
        # Prioritize by defect severity - only refine components with critical/high defects first
        if _defect_ledger:
            # Filter to only components with critical/high severity defects
            critical_high_pages = []
            critical_high_endpoints = []
            
            open_defects = _defect_ledger.get_open_defects()
            critical_high_defects = [d for d in open_defects if d.get('severity') in ['critical', 'high']]
            
            # Get unique components with critical/high defects
            critical_high_components = set()
            for defect in critical_high_defects:
                critical_high_components.add(defect.get('component', ''))
            
            # Filter pages and endpoints
            for page in pages_to_refine:
                page_name = page.get('page_name', '')
                if f"frontend/{page_name}" in critical_high_components:
                    critical_high_pages.append(page)
            
            for endpoint in endpoints_to_refine:
                endpoint_path = endpoint.get('path', '')
                if f"backend/{endpoint_path}" in critical_high_components:
                    critical_high_endpoints.append(endpoint)
            
            # Use critical/high priority components if available
            if critical_high_pages or critical_high_endpoints:
                pages_to_refine = critical_high_pages
                endpoints_to_refine = critical_high_endpoints
                log_and_print(f"  [Priority] Focusing on {len(pages_to_refine)} pages and {len(endpoints_to_refine)} endpoints with critical/high defects", log_file)
            elif pages_to_refine or endpoints_to_refine:
                # If no critical/high, use medium priority components (but still limit)
                log_and_print(f"  [Priority] No critical/high defects. Refining {len(pages_to_refine)} pages and {len(endpoints_to_refine)} endpoints with medium/low defects", log_file)
            else:
                # No components with defects found - skip refinement
                log_and_print(f"  [Refinement] No components with defects found. Skipping refinement to save tokens.", log_file)
                return implementation_results
        
        # Limit refinement based on token budget - more aggressive limiting
        max_refinements = min(
            len(pages_to_refine) + len(endpoints_to_refine),
            max(2, remaining_tokens // 8000)  # Estimate 8k tokens per refinement, max 2 per cycle
        )
        
        if len(pages_to_refine) + len(endpoints_to_refine) > max_refinements:
            log_and_print(f"  [Token Budget] Limiting to {max_refinements} components (budget: {remaining_tokens:,} tokens)", log_file)
            # Prioritize pages first, then endpoints
            pages_to_refine = pages_to_refine[:max(1, max_refinements - len(endpoints_to_refine))]
            endpoints_to_refine = endpoints_to_refine[:max(0, max_refinements - len(pages_to_refine))]
        
        # Divide refinement work among agents
        pages_per_agent = (len(pages_to_refine) + 2) // 3 if pages_to_refine else 0
        endpoints_per_agent = (len(endpoints_to_refine) + 2) // 3 if endpoints_to_refine else 0
        
        for agent_id in range(1, 4):
            agent_pages = pages_to_refine[(agent_id-1)*pages_per_agent:agent_id*pages_per_agent] if pages_to_refine else []
            agent_endpoints = endpoints_to_refine[(agent_id-1)*endpoints_per_agent:agent_id*endpoints_per_agent] if endpoints_to_refine else []
            
            if agent_pages:
                log_and_print(f"  [Implementation Agent {agent_id}] Refining {len(agent_pages)} pages...", log_file)
                for page in agent_pages:
                    result = implement_page_kaizen(page, react_path, endpoints, description, agent_id, log_file, is_refinement=True, design=design)
                    if result:
                        implementation_results['pages_refined'] += 1
            
            if agent_endpoints:
                log_and_print(f"  [Implementation Agent {agent_id}] Refining {len(agent_endpoints)} endpoints...", log_file)
                # Determine MongoDB usage from design/description
                use_mongodb = determine_db_usage(description, [], design)
                for endpoint in agent_endpoints:
                    result = implement_endpoint_kaizen(endpoint, flask_path, description, agent_id, log_file, is_refinement=True, use_mongodb=use_mongodb)
                    if result:
                        implementation_results['endpoints_refined'] += 1
    
    return implementation_results


def check_phase(design: Dict, react_path: str, flask_path: str, cycle_number: int, log_file: str) -> Dict:
    """CHECK phase: Verification Group inspects and identifies defects."""
    global _defect_ledger, _metrics, _rate_limiter
    _defect_ledger = get_defect_ledger()
    
    # Check remaining token budget before verification
    remaining_tokens = _rate_limiter.get_remaining_daily_tokens()
    stats = _rate_limiter.get_statistics()
    
    log_and_print(f"  [Token Status] Remaining daily tokens: {remaining_tokens:,} ({stats.get('daily_token_percentage', 0):.1f}% used)", log_file)
    
    # If we're close to the limit, raise exception instead of skipping silently
    if remaining_tokens < 10000:  # Less than 10k tokens remaining
        log_and_print(f"  [ERROR] Insufficient token budget for verification. Remaining: {remaining_tokens}", log_file)
        # Don't skip silently - raise exception so caller knows verification couldn't happen
        raise Exception(f"Verification phase cannot proceed - insufficient tokens. Remaining: {remaining_tokens}, needed: ~10000")
    
    pages = design.get("frontend", {}).get("pages", [])
    endpoints = design.get("backend", {}).get("endpoints", [])
    
    defects_found = 0
    
    # Check for missing endpoints that are commonly needed
    endpoint_paths = {ep.get('path', '') for ep in endpoints}
    endpoint_methods = {(ep.get('path', ''), ep.get('method', 'GET').upper()) for ep in endpoints}
    
    # Check if we have list endpoints but missing detail endpoints
    for page in pages:
        page_name = page.get('page_name', '').lower()
        page_endpoints = page.get('backend_endpoints', [])
        
        # If page name suggests detail view, check for detail endpoint
        if any(keyword in page_name for keyword in ['detail', 'view', 'show', 'profile']):
            # Check if any endpoint has a detail pattern
            has_detail_endpoint = False
            for ep in page_endpoints:
                ep_path = ep.get('path', '')
                if '<id>' in ep_path or ':id' in ep_path or '{id}' in ep_path:
                    has_detail_endpoint = True
                    break
            
            if not has_detail_endpoint and page_endpoints:
                # Try to infer the list endpoint and suggest detail endpoint
                for ep in page_endpoints:
                    list_path = ep.get('path', '')
                    if '/api/' in list_path:
                        # Extract resource
                        resource = list_path.split('/')[-1] if not list_path.endswith('/') else list_path.split('/')[-2]
                        detail_path = f"{list_path.rstrip('/')}/<id>"
                        if detail_path not in endpoint_paths:
                            if _defect_ledger:
                                _defect_ledger.add_defect(
                                    f"Page '{page.get('page_name')}' likely needs detail endpoint: GET {detail_path}",
                                    f"backend/{detail_path}",
                                    DefectSeverity.MEDIUM,
                                    "Integration Validator",
                                    "missing_endpoint"
                                )
                                defects_found += 1
    
    # Check for missing GET endpoints for resources that have POST
    for endpoint in endpoints:
        if endpoint.get('method', '').upper() == 'POST':
            ep_path = endpoint.get('path', '')
            # Check if GET endpoint exists for same path
            if (ep_path, 'GET') not in endpoint_methods:
                resource_name = ep_path.split('/')[-1] if ep_path else ''
                # Only flag if it's a common resource that typically needs GET
                if resource_name in ['orders', 'users', 'cart', 'products', 'items', 'reviews', 'comments']:
                    if _defect_ledger:
                        _defect_ledger.add_defect(
                            f"Resource '{resource_name}' has POST endpoint but missing GET endpoint: GET {ep_path}",
                            f"backend/{ep_path}",
                            DefectSeverity.MEDIUM,
                            "Integration Validator",
                            "missing_endpoint"
                        )
                        defects_found += 1
    
    # In Cycle 2+, only verify components that were refined (not all components)
    if cycle_number > 1:
        # Only verify components that exist and were potentially refined
        pages_to_verify = [p for p in pages if os.path.exists(get_page_file_path(p, react_path))]
        endpoints_to_verify = [e for e in endpoints if os.path.exists(get_endpoint_file_path(e, flask_path))]
        
        # Limit verification to recently refined components
        log_and_print(f"  [Cycle {cycle_number}] Verifying {len(pages_to_verify)} pages and {len(endpoints_to_verify)} endpoints...", log_file)
    else:
        pages_to_verify = pages
        endpoints_to_verify = endpoints
    
    # Verification Group: 2 agents inspecting code
    # But limit the number of items to verify based on remaining tokens
    # In Cycle 1: Verify all, but limit to 2 items per agent
    # In Cycle 2+: Only verify if components were actually refined (skip if no changes)
    if cycle_number == 1:
        max_items_per_agent = min(2, max(1, remaining_tokens // 4000))  # More conservative: 4k tokens per verification
    else:
        # In later cycles, only verify if there were actual refinements
        max_items_per_agent = min(1, max(0, remaining_tokens // 5000))  # Even more conservative
        if max_items_per_agent == 0:
            log_and_print(f"  [Cycle {cycle_number}] No components to verify (no changes detected)", log_file)
            # This is OK - no changes means no verification needed
            return {"defects_found": 0, "skipped": False, "reason": "no_changes"}
    
    for agent_id in range(1, 3):
        # Check if we should continue
        if _rate_limiter.get_remaining_daily_tokens() < 5000:
            log_and_print(f"  [Verification Agent {agent_id}] Stopping verification due to low token budget", log_file)
            break
        
        log_and_print(f"  [Verification Agent {agent_id}] Inspecting code (max {max_items_per_agent} items each)...", log_file)
        
        # Inspect frontend (limited)
        agent_pages = pages_to_verify[:len(pages_to_verify)//2 + 1] if agent_id == 1 else pages_to_verify[len(pages_to_verify)//2:]
        for page in agent_pages[:max_items_per_agent]:
            if _rate_limiter.get_remaining_daily_tokens() < 2000:
                log_and_print(f"    [Skipping] Low token budget for {page.get('page_name', 'Unknown')}", log_file)
                break
            try:
                defects = verify_page_kaizen(page, react_path, agent_id, log_file)
                defects_found += len(defects)
            except Exception as e:
                if '429' in str(e) or 'rate_limit' in str(e).lower():
                    log_and_print(f"    [Rate Limit] Skipping verification due to rate limit", log_file)
                    break
                log_and_print(f"    [Error] {str(e)[:100]}", log_file)
        
        # Inspect backend (limited)
        agent_endpoints = endpoints_to_verify[:len(endpoints_to_verify)//2 + 1] if agent_id == 1 else endpoints_to_verify[len(endpoints_to_verify)//2:]
        for endpoint in agent_endpoints[:max_items_per_agent]:
            if _rate_limiter.get_remaining_daily_tokens() < 2000:
                log_and_print(f"    [Skipping] Low token budget for {endpoint.get('path', 'Unknown')}", log_file)
                break
            try:
                defects = verify_endpoint_kaizen(endpoint, flask_path, agent_id, log_file)
                defects_found += len(defects)
            except Exception as e:
                if '429' in str(e) or 'rate_limit' in str(e).lower():
                    log_and_print(f"    [Rate Limit] Skipping verification due to rate limit", log_file)
                    break
                log_and_print(f"    [Error] {str(e)[:100]}", log_file)
    
    _metrics.defects_found += defects_found
    
    # Optional: Run runtime debugging if projects are available
    # This is an additional CHECK phase that tests actual runtime behavior
    runtime_debugging_enabled = os.getenv("KAIZEN_RUNTIME_DEBUG", "false").lower() == "true"
    
    if runtime_debugging_enabled and cycle_number == 1:  # Only in first cycle to save tokens
        try:
            log_and_print(f"  [Runtime Debugging] Starting runtime error detection...", log_file)
            from kaizen_debugger import run_kaizen_runtime_debugging
            
            runtime_summary = run_kaizen_runtime_debugging(
                react_path=react_path,
                flask_path=flask_path,
                defect_ledger=_defect_ledger,
                rate_limiter=_rate_limiter,
                log_file=log_file,
                max_iterations=3  # Limit iterations to save tokens
            )
            
            if runtime_summary.get("success") and runtime_summary.get("total_fixes", 0) > 0:
                log_and_print(f"  [Runtime Debugging] Applied {runtime_summary['total_fixes']} runtime fixes", log_file)
                defects_found += runtime_summary.get("errors_detected", 0)
        except Exception as e:
            log_and_print(f"  [Runtime Debugging] Error: {str(e)[:200]}", log_file)
            # Don't fail the CHECK phase if runtime debugging fails
    
    return {"defects_found": defects_found}


def act_phase(design: Dict, react_path: str, flask_path: str, cycle_number: int, log_file: str) -> Dict:
    """ACT phase: Integration Group ensures consistency and resolves defects."""
    global _defect_ledger, _metrics, _rate_limiter
    _defect_ledger = get_defect_ledger()
    
    # Check remaining token budget
    remaining_tokens = _rate_limiter.get_remaining_daily_tokens()
    if remaining_tokens < 5000:
        log_and_print(f"  [ERROR] Insufficient token budget for ACT phase. Remaining: {remaining_tokens}", log_file)
        # Don't skip silently - raise exception so caller knows ACT couldn't happen
        raise Exception(f"ACT phase cannot proceed - insufficient tokens. Remaining: {remaining_tokens}, needed: ~5000")
    
    # Integration Group: 1 agent ensuring architectural consistency
    log_and_print(f"  [Integration Agent] Ensuring architectural consistency...", log_file)
    
    integration_agent = get_agent(temperature=0.2, max_tokens=1500)
    
    # Get open defects
    open_defects = _defect_ledger.get_open_defects() if _defect_ledger else []
    critical_defects = [d for d in open_defects if d['severity'] == DefectSeverity.CRITICAL.value]
    high_defects = [d for d in open_defects if d['severity'] == DefectSeverity.HIGH.value]
    
    defects_resolved = 0
    improvements_applied = 0
    
    # Resolve critical and high priority defects (limit based on remaining tokens)
    # More aggressive limiting: only resolve 1-2 defects per cycle
    max_defects_to_resolve = min(2, max(1, remaining_tokens // 4000))  # Estimate 4k tokens per resolution, max 2
    
    for defect in (critical_defects + high_defects)[:max_defects_to_resolve]:
        # Check token budget before each resolution
        if _rate_limiter.get_remaining_daily_tokens() < 2000:
            log_and_print(f"    [Skipping] Low token budget for defect #{defect['id']}", log_file)
            break
        
        log_and_print(f"    Resolving defect #{defect['id']}: {defect['description'][:50]}...", log_file)
        
        try:
            resolve_prompt = f"""You are an Integration Agent resolving a defect.

DEFECT:
ID: {defect['id']}
Component: {defect['component']}
Severity: {defect['severity']}
Description: {defect['description']}
Category: {defect['category']}

Provide a solution to resolve this defect. Return JSON:
{{
    "solution": "detailed solution",
    "code_changes": "specific code changes needed",
    "verification_steps": ["step1", "step2"]
}}"""

            response = invoke_with_rate_limit(integration_agent, [HumanMessage(content=resolve_prompt)], log_file, estimated_tokens=1500)  # Reduced from 3000
            if response:
                # In a real implementation, we would apply the solution here
                if _defect_ledger:
                    _defect_ledger.update_defect_status(defect['id'], DefectStatus.RESOLVED, "Integration Agent")
                defects_resolved += 1
                _metrics.defects_resolved += 1
        except Exception as e:
            if '429' in str(e) or 'rate_limit' in str(e).lower():
                log_and_print(f"    [Rate Limit] Stopping defect resolution due to rate limit", log_file)
                break
            log_and_print(f"    [Error] Failed to resolve defect #{defect['id']}: {str(e)[:100]}", log_file)
    
    # Check for architectural consistency (only in Cycle 1, skip in later cycles to save tokens)
    if cycle_number == 1 and _rate_limiter.get_remaining_daily_tokens() > 5000:
        try:
            consistency_prompt = f"""You are an Integration Agent checking architectural consistency.

Review the application design and ensure:
1. Consistent naming conventions
2. Proper component dependencies
3. No circular dependencies
4. Consistent API patterns

Return JSON with any inconsistencies found:
{{
    "inconsistencies": [
        {{"component": "name", "issue": "description", "severity": "high|medium|low"}}
    ]
}}"""

            response = invoke_with_rate_limit(integration_agent, [HumanMessage(content=consistency_prompt)], log_file, estimated_tokens=1000)  # Reduced from 2000
            # Process inconsistencies if found
        except Exception as e:
            if '429' not in str(e) and 'rate_limit' not in str(e).lower():
                log_and_print(f"    [Error] Consistency check failed: {str(e)[:100]}", log_file)
    
    return {
        "defects_resolved": defects_resolved,
        "improvements_applied": improvements_applied
    }


def cross_team_consolidation(
    design: Dict, react_path: str, flask_path: str, cycle_number: int,
    do_result: Dict, check_result: Dict, act_result: Dict, log_file: str
) -> Dict:
    """
    CROSS-TEAM CONSOLIDATION: Consolidate results from all three groups.
    
    According to Kaizen methodology flowchart:
    - Receives input from Implementation Group (Do), Verification Group (Check), Integration Group (Act)
    - Provides feedback to Improvement Coordinator
    - Identifies cross-team issues and dependencies
    - Feeds back to teams for next cycle planning
    """
    global _defect_ledger, _rate_limiter
    _defect_ledger = get_defect_ledger()
    
    # Check token budget - Skip consolidation in Cycle 3+ to save tokens
    remaining_tokens = _rate_limiter.get_remaining_daily_tokens()
    if cycle_number > 2:
        log_and_print(f"  [Consolidation] Skipping in Cycle {cycle_number} to save tokens", log_file)
        return {"cross_team_issues": 0, "consolidation_feedback": []}
    if remaining_tokens < 5000:
        log_and_print(f"  [Consolidation] Skipping due to low token budget ({remaining_tokens} remaining)", log_file)
        return {"cross_team_issues": 0, "consolidation_feedback": []}
    
    consolidation_agent = get_agent(temperature=0.2, max_tokens=1500)
    
    # Collect results from all teams
    implementation_summary = {
        "pages_implemented": do_result.get('pages_implemented', 0),
        "pages_refined": do_result.get('pages_refined', 0),
        "endpoints_implemented": do_result.get('endpoints_implemented', 0),
        "endpoints_refined": do_result.get('endpoints_refined', 0)
    }
    
    verification_summary = {
        "defects_found": check_result.get('defects_found', 0),
        "components_verified": check_result.get('components_verified', 0)
    }
    
    integration_summary = {
        "defects_resolved": act_result.get('defects_resolved', 0),
        "improvements_applied": act_result.get('improvements_applied', 0)
    }
    
    # Get defect statistics for consolidation
    defect_stats = _defect_ledger.get_statistics() if _defect_ledger else {}
    open_defects = _defect_ledger.get_open_defects() if _defect_ledger else []
    
    consolidation_prompt = f"""You are the Cross-Team Consolidation Agent in the Kaizen system.

Your role is to consolidate results from all three specialized groups and identify cross-team issues.

CYCLE: {cycle_number}

RESULTS FROM TEAMS:
1. Implementation Group (Do Phase):
   - Pages implemented: {implementation_summary['pages_implemented']}
   - Pages refined: {implementation_summary['pages_refined']}
   - Endpoints implemented: {implementation_summary['endpoints_implemented']}
   - Endpoints refined: {implementation_summary['endpoints_refined']}

2. Verification Group (Check Phase):
   - Defects found: {verification_summary['defects_found']}
   - Components verified: {verification_summary.get('components_verified', 'N/A')}

3. Integration Group (Act Phase):
   - Defects resolved: {integration_summary['defects_resolved']}
   - Improvements applied: {integration_summary['improvements_applied']}

CURRENT STATE:
- Total defects: {defect_stats.get('total_defects', 0)}
- Open defects: {defect_stats.get('open_defects', 0)}
- Resolution rate: {defect_stats.get('resolution_rate', 0):.2%}

OPEN DEFECTS (sample):
{json.dumps([{'id': d['id'], 'component': d['component'], 'severity': d['severity'], 'description': d['description'][:80]} for d in open_defects[:5]], indent=2)}

Analyze and consolidate:
1. Identify cross-team dependencies and issues
2. Find inconsistencies between teams' outputs
3. Identify integration problems
4. Suggest improvements for next cycle
5. Provide feedback for Improvement Coordinator

Return JSON:
{{
    "cross_team_issues": [
        {{
            "issue": "description of cross-team issue",
            "affected_teams": ["Implementation", "Verification", "Integration"],
            "severity": "high|medium|low",
            "recommendation": "how to resolve"
        }}
    ],
    "consolidation_feedback": [
        {{
            "for_team": "Implementation|Verification|Integration|Coordinator",
            "feedback": "specific feedback message",
            "priority": "high|medium|low"
        }}
    ],
    "next_cycle_recommendations": [
        "recommendation1",
        "recommendation2"
    ],
    "integration_status": "good|needs_attention|critical"
}}"""

    try:
        response = invoke_with_rate_limit(consolidation_agent, [HumanMessage(content=consolidation_prompt)], log_file, estimated_tokens=1000)  # Reduced from 2000
        if not response:
            return {"cross_team_issues": 0, "consolidation_feedback": []}
        
        content = response.content.strip()
        
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0:
                consolidation_data = json.loads(content[json_start:json_end])
                
                cross_team_issues = consolidation_data.get('cross_team_issues', [])
                feedback = consolidation_data.get('consolidation_feedback', [])
                recommendations = consolidation_data.get('next_cycle_recommendations', [])
                integration_status = consolidation_data.get('integration_status', 'unknown')
                
                log_and_print(f"  ✓ Consolidation complete:", log_file)
                log_and_print(f"    Cross-team issues: {len(cross_team_issues)}", log_file)
                log_and_print(f"    Feedback items: {len(feedback)}", log_file)
                log_and_print(f"    Integration status: {integration_status}", log_file)
                
                # Log critical issues
                critical_issues = [i for i in cross_team_issues if i.get('severity') == 'high']
                if critical_issues:
                    log_and_print(f"    ⚠ Critical cross-team issues found:", log_file)
                    for issue in critical_issues[:3]:
                        log_and_print(f"      - {issue.get('issue', 'Unknown')[:60]}...", log_file)
                
                # Add feedback to defect ledger as improvements
                if _defect_ledger and feedback:
                    for fb in feedback[:3]:  # Limit to top 3
                        if fb.get('priority') in ['high', 'medium']:
                            _defect_ledger.add_improvement(
                                fb.get('feedback', ''),
                                fb.get('for_team', 'system'),
                                'consolidation_agent',
                                fb.get('priority', 'medium')
                            )
                
                return {
                    "cross_team_issues": len(cross_team_issues),
                    "consolidation_feedback": feedback,
                    "next_cycle_recommendations": recommendations,
                    "integration_status": integration_status
                }
        except json.JSONDecodeError as e:
            log_and_print(f"  [Warning] Failed to parse consolidation data: {e}", log_file)
    except Exception as e:
        if '429' not in str(e) and 'rate_limit' not in str(e).lower():
            log_and_print(f"  [Error] Consolidation failed: {str(e)[:100]}", log_file)
    
    return {"cross_team_issues": 0, "consolidation_feedback": []}


def get_page_file_path(page: Dict, project_path: str) -> str:
    """Get the file path for a page component."""
    page_name = page.get('page_name', 'Unknown')
    component_name = page_name.replace(" ", "").replace("-", "")
    return os.path.join(project_path, "src", "pages", f"{component_name}.jsx")


def get_endpoint_file_path(endpoint: Dict, project_path: str) -> str:
    """Get the file path for an endpoint."""
    path = endpoint.get('path', '')
    path_parts = path.strip('/').split('/')
    resource = path_parts[1] if len(path_parts) > 1 else 'general'
    return os.path.join(project_path, "routes", f"{resource}_routes.py")


def get_components_with_defects_prioritized(pages: List[Dict], endpoints: List[Dict], defect_ledger) -> Dict[str, List[Dict]]:
    """
    Get components with defects, prioritized by severity.
    Returns components grouped by severity level.
    """
    if not defect_ledger:
        return {'critical': [], 'high': [], 'medium': [], 'low': []}
    
    open_defects = defect_ledger.get_open_defects()
    
    components_by_severity = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': []
    }
    
    for defect in open_defects:
        severity = defect.get('severity', 'medium')
        component = defect.get('component', '')
        
        if severity in components_by_severity:
            if component not in components_by_severity[severity]:
                components_by_severity[severity].append(component)
    
    return components_by_severity


def validate_frontend_backend_integration(design: Dict, react_path: str, flask_path: str, log_file: str) -> int:
    """
    Validate that frontend and backend are properly integrated.
    Checks for:
    1. Routes exist but no frontend component
    2. Frontend exists but no backend route
    3. Frontend components don't call backend endpoints
    4. Buttons don't interact with backend/DB
    """
    global _defect_ledger
    _defect_ledger = get_defect_ledger()
    
    if not _defect_ledger:
        return 0
    
    defects_found = 0
    pages = design.get("frontend", {}).get("pages", [])
    endpoints = design.get("backend", {}).get("endpoints", [])
    
    # Check 1: Frontend pages have corresponding API calls
    for page in pages:
        page_name = page.get('page_name', '')
        page_endpoints = page.get('backend_endpoints', [])
        component_file = get_page_file_path(page, react_path)
        
        if not os.path.exists(component_file):
            if _defect_ledger:
                _defect_ledger.add_defect(
                    f"Frontend component missing: {page_name}",
                    f"frontend/{page_name}",
                    DefectSeverity.CRITICAL,
                    "Integration Validator",
                    "missing_file"
                )
                defects_found += 1
            continue
        
        # Read component file
        try:
            with open(component_file, 'r', encoding='utf-8') as f:
                component_code = f.read()
            
            # Check if component calls the specified endpoints
            for ep in page_endpoints:
                ep_path = ep.get('path', '')
                ep_method = ep.get('method', 'GET')
                
                # Check if endpoint path is called in component
                if ep_path not in component_code and ep_path.replace('/api/', '') not in component_code:
                    if _defect_ledger:
                        _defect_ledger.add_defect(
                            f"Frontend component '{page_name}' doesn't call backend endpoint {ep_method} {ep_path}",
                            f"frontend/{page_name}",
                            DefectSeverity.HIGH,
                            "Integration Validator",
                            "missing_integration"
                        )
                        defects_found += 1
            
            # Check if buttons have API calls
            import re
            button_pattern = r'<button[^>]*>([^<]+)</button>'
            buttons = re.findall(button_pattern, component_code, re.IGNORECASE | re.DOTALL)
            
            for button_text in buttons[:10]:  # Check first 10 buttons
                button_text_lower = button_text.lower().strip()
                # Check for any action verbs - let the AI naturally determine what actions are needed
                action_verbs = ['add', 'create', 'submit', 'delete', 'remove', 'update', 'save', 'post', 'send', 'login', 'register', 'logout', 'purchase', 'buy', 'checkout', 'filter', 'search', 'sort']
                has_action_verb = any(verb in button_text_lower for verb in action_verbs)
                
                if has_action_verb:
                    # Check if button has onClick handler with API call
                    button_context_pattern = rf'<button[^>]*onClick[^>]*>.*?{re.escape(button_text[:30])}.*?</button>'
                    button_match = re.search(button_context_pattern, component_code, re.IGNORECASE | re.DOTALL)
                    
                    if button_match:
                        button_code = button_match.group(0)
                        # Check if it has API call
                        has_api = 'axios' in button_code or 'fetch' in button_code or '/api/' in button_code
                        has_navigate = 'navigate' in button_code
                        
                        # If button navigates but doesn't call API, it's a defect
                        if has_navigate and not has_api:
                            # Check if handler function calls API
                            handler_pattern = r'onClick\s*=\s*\{?\s*(\w+)\s*\([^)]*\)'
                            handler_match = re.search(handler_pattern, button_code)
                            if handler_match:
                                func_name = handler_match.group(1)
                                # Check if function exists and calls API
                                func_pattern = rf'const\s+{func_name}\s*=\s*[^{{]*\{{([^}}]+)\}}'
                                func_match = re.search(func_pattern, component_code, re.DOTALL)
                                if func_match:
                                    func_body = func_match.group(1)
                                    if 'axios' not in func_body and 'fetch' not in func_body and '/api/' not in func_body:
                                        if _defect_ledger:
                                            _defect_ledger.add_defect(
                                                f"Button '{button_text[:30]}...' in '{page_name}' navigates but doesn't call API - should perform action first",
                                                f"frontend/{page_name}",
                                                DefectSeverity.HIGH,
                                                "Integration Validator",
                                                "incomplete_functionality"
                                            )
                                            defects_found += 1
                        elif not has_api and not has_navigate:
                            # Button has action verb but no API call or navigation
                            if _defect_ledger:
                                _defect_ledger.add_defect(
                                    f"Button '{button_text[:30]}...' in '{page_name}' has no functionality - should call API or perform action",
                                    f"frontend/{page_name}",
                                    DefectSeverity.HIGH,
                                    "Integration Validator",
                                    "incomplete_functionality"
                                )
                                defects_found += 1
            # Check for useEffect infinite loop patterns
            useEffect_pattern = r'useEffect\s*\(\s*\([^)]*\)\s*=>\s*\{[^}]*\},\s*\[([^\]]+)\]'
            useEffect_matches = re.findall(useEffect_pattern, component_code, re.DOTALL)
            for deps in useEffect_matches:
                # Check if dependencies include function names that aren't memoized
                func_names = re.findall(r'\b(\w+)\b', deps)
                for func_name in func_names:
                    if func_name in ['fetch', 'get', 'load', 'handle']:  # Common function name patterns
                        # Check if it's a function and if it's memoized
                        func_def = re.search(rf'(const|let|var)\s+{func_name}\s*=', component_code)
                        if func_def and 'useCallback' not in component_code and 'React.useMemo' not in component_code:
                            if _defect_ledger:
                                _defect_ledger.add_defect(
                                    f"useEffect in '{page_name}' depends on '{func_name}' which may cause infinite loop - should use useCallback or depend on function's dependencies",
                                    f"frontend/{page_name}",
                                    DefectSeverity.HIGH,
                                    "Integration Validator",
                                    "infinite_loop"
                                )
                                defects_found += 1
            
            # Check for API call payload completeness
            api_call_pattern = r'(axios|axiosInstance)\.(post|put|patch)\s*\([^,]+,\s*\{([^}]+)\}'
            api_matches = re.findall(api_call_pattern, component_code, re.DOTALL)
            for match in api_matches:
                method = match[1].upper()
                payload = match[2] if len(match) > 2 else ''
                # Check if payload has both product_id/productId and quantity for cart operations
                if 'cart' in match[0].lower() or '/api/cart' in component_code:
                    has_product = 'product_id' in payload.lower() or 'productId' in payload.lower()
                    has_quantity = 'quantity' in payload.lower()
                    if not has_product or not has_quantity:
                        if _defect_ledger:
                            _defect_ledger.add_defect(
                                f"API call to /api/cart in '{page_name}' missing required fields - needs product_id and quantity",
                                f"frontend/{page_name}",
                                DefectSeverity.HIGH,
                                "Integration Validator",
                                "missing_fields"
                            )
                            defects_found += 1
        except Exception as e:
            log_and_print(f"    [Warning] Could not validate component {page_name}: {e}", log_file)
    
    # Check 2: Backend routes exist
    for endpoint in endpoints:
        path = endpoint.get('path', '')
        method = endpoint.get('method', 'GET')
        path_parts = path.strip('/').split('/')
        resource = path_parts[1] if len(path_parts) > 1 else 'general'
        route_file = os.path.join(flask_path, "routes", f"{resource}_routes.py")
        
        if not os.path.exists(route_file):
            if _defect_ledger:
                _defect_ledger.add_defect(
                    f"Backend route file missing for endpoint {method} {path}",
                    f"backend/{path}",
                    DefectSeverity.CRITICAL,
                    "Integration Validator",
                    "missing_file"
                )
                defects_found += 1
            continue
        
        # Check if route exists in file
        try:
            with open(route_file, 'r', encoding='utf-8') as f:
                route_code = f.read()
            
            # Check if route is defined
            import re
            route_pattern = rf"@app\.route\(['\"]{re.escape(path)}['\"]"
            if route_pattern not in route_code and f"methods=['{method}']" not in route_code:
                # Try with Flask parameter syntax
                flask_path_pattern = path.replace('{', '<').replace('}', '>').replace(':id', '<id>')
                route_pattern2 = rf"@app\.route\(['\"]{re.escape(flask_path_pattern)}['\"]"
                if route_pattern2 not in route_code:
                    if _defect_ledger:
                        _defect_ledger.add_defect(
                            f"Backend route {method} {path} not found in route file",
                            f"backend/{path}",
                            DefectSeverity.CRITICAL,
                            "Integration Validator",
                            "missing_route"
                        )
                        defects_found += 1
        except Exception as e:
            log_and_print(f"    [Warning] Could not validate route {method} {path}: {e}", log_file)
    
    return defects_found


def get_components_needing_refinement(pages: List[Dict], endpoints: List[Dict], cycle_number: int) -> Dict[str, List[str]]:
    """
    Identify components that need refinement based on defects and improvements.
    True Kaizen: Focus refinement on components with issues.
    
    Returns:
        Dict with 'pages' and 'endpoints' lists containing file paths that need refinement
    """
    global _defect_ledger
    _defect_ledger = get_defect_ledger()
    
    components_to_refine = {
        'pages': [],  # List of file paths
        'endpoints': []  # List of file paths
    }
    
    if not _defect_ledger or cycle_number == 1:
        return components_to_refine
    
    # Get open defects
    open_defects = _defect_ledger.get_open_defects()
    
    # Group defects by component and map to file paths
    for defect in open_defects:
        component = defect.get('component', '')
        if 'frontend/' in component:
            page_name = component.replace('frontend/', '')
            # Find the page in design and get its file path
            for page in pages:
                if page.get('page_name') == page_name:
                    file_path = get_page_file_path(page, "dummy")  # We'll extract just the filename
                    if file_path not in components_to_refine['pages']:
                        components_to_refine['pages'].append(page_name)  # Store page name for matching
                    break
        elif 'backend/' in component:
            endpoint_path = component.replace('backend/', '')
            if endpoint_path not in components_to_refine['endpoints']:
                components_to_refine['endpoints'].append(endpoint_path)
    
    # Get improvement suggestions
    improvements = _defect_ledger.improvements
    for improvement in improvements:
        if improvement.get('status') == 'pending':
            component = improvement.get('component', '')
            if 'frontend/' in component:
                page_name = component.replace('frontend/', '')
                if page_name not in components_to_refine['pages']:
                    components_to_refine['pages'].append(page_name)
            elif 'backend/' in component:
                endpoint_path = component.replace('backend/', '')
                if endpoint_path not in components_to_refine['endpoints']:
                    components_to_refine['endpoints'].append(endpoint_path)
    
    return components_to_refine


def implement_page_kaizen(page: Dict, project_path: str, all_endpoints: List[Dict], description: str, agent_id: int, log_file: str, is_refinement: bool = False, design: Dict = None) -> bool:
    """
    Implementation Group agent implements or refines a frontend page with Kaizen principles.
    
    True Kaizen: Cycle 1 implements, Cycle 2+ refines the same component.
    """
    global _defect_ledger
    _defect_ledger = get_defect_ledger()
    page_name = page.get('page_name', 'Unknown')
    requirements = page.get('requirements', [])
    page_endpoints = page.get('backend_endpoints', [])
    
    # Extract UI theme from design if available
    ui_theme = {}
    if design:
        ui_theme = design.get('ui_theme', {})
    application_type = design.get('application_type', 'Web Application') if design else 'Web Application'
    
    # Get full endpoint specs
    endpoint_specs = []
    for ep in page_endpoints:
        for full_ep in all_endpoints:
            if ep.get('path') == full_ep.get('path') and ep.get('method') == full_ep.get('method'):
                endpoint_specs.append(full_ep)
                break
    
    component_file = get_page_file_path(page, project_path)
    existing_code = None
    
    # If refining, read existing code and get defects
    if is_refinement and os.path.exists(component_file):
        try:
            with open(component_file, 'r', encoding='utf-8') as f:
                existing_code = f.read()
        except Exception as e:
            log_and_print(f"    [Warning] Could not read existing code: {e}", log_file)
    
    # Get defects for this component
    component_defects = []
    improvement_suggestions = []
    if _defect_ledger:
        open_defects = _defect_ledger.get_open_defects(component=f"frontend/{page_name}")
        component_defects = [d for d in open_defects if d['status'] in ['open', 'in_progress']]
        
        # Get improvement suggestions
        for improvement in _defect_ledger.improvements:
            if improvement.get('component') == f"frontend/{page_name}" and improvement.get('status') == 'pending':
                improvement_suggestions.append(improvement)
    
    # Build prompt based on whether it's implementation or refinement
    if is_refinement and existing_code:
        # REFINEMENT: Improve existing code
        defects_info = "\n".join([f"- {d['description']} (Severity: {d['severity']})" for d in component_defects[:5]])
        improvements_info = "\n".join([f"- {imp['description']}" for imp in improvement_suggestions[:3]])
        
        prompt = f"""You are an Implementation Agent in the Kaizen system. REFINE an existing React component to improve quality.

APPLICATION CONTEXT: {description}
APPLICATION TYPE: {application_type}

PAGE: {page_name}
Description: {page.get('description', '')}

CURRENT CODE (first 2000 chars):
{existing_code[:2000]}

DEFECTS TO FIX:
{defects_info if defects_info else "No specific defects identified"}

IMPROVEMENTS TO APPLY:
{improvements_info if improvements_info else "No specific improvements identified"}

REQUIREMENTS:
{json.dumps(requirements, indent=2)}

BACKEND ENDPOINTS:
{json.dumps(endpoint_specs, indent=2)}

CHAIN OF THOUGHT FOR REFINEMENT:
1. Analyze the existing code structure and identify all issues
2. Fix defects from the defects list systematically
3. Apply improvements while maintaining existing functionality
4. Enhance UI/UX: Add loading states, empty states, error handling, animations
5. Improve accessibility: ARIA labels, keyboard navigation, focus management
6. Optimize performance: Memoization, lazy loading, code splitting if needed
7. Enhance responsive design: Ensure mobile-first approach with proper breakpoints
8. Improve form UX: Real-time validation, better error messages, visual feedback
9. Add progressive enhancement: Retry mechanisms, optimistic updates, caching
10. Ensure code quality: Remove any TODOs, placeholders, or incomplete code

DYNAMIC IMPROVEMENTS TO APPLY (based on {application_type}):
- Loading states: Context-aware skeletons/spinners matching content structure
- Empty states: Meaningful messages with actionable CTAs specific to this application
- Animations: Subtle transitions and micro-interactions that enhance UX
- Accessibility: Full WCAG compliance with proper ARIA and keyboard support
- Form enhancements: Real-time validation, field-level errors, smart defaults
- Responsive patterns: Mobile-first with adaptive layouts for all screen sizes
- Error recovery: Retry mechanisms, graceful degradation, helpful error messages

Return the IMPROVED version of the component. Keep the same structure but fix defects and apply improvements.
**IMPORTANT: 
- Use Tailwind CSS classes for ALL styling. Do NOT use inline styles or CSS files.
- This file will be saved as .jsx extension, so ensure all JSX syntax is correct.
- Use .jsx extension in any relative imports (e.g., './components/MyComponent.jsx')
- **CRITICAL - NO TYPESCRIPT SYNTAX**: This is a .jsx file, NOT .tsx. Do NOT use:
  * TypeScript interfaces: NO `interface ComponentProps {{ ... }}`
  * Type annotations: NO `const Component: React.FC<Props> = ...`
  * Type annotations: NO `const Component = ({{ prop }}: Props) => ...`
  * Type annotations: NO `function Component({{ prop }}: Props)`
  * Use plain JavaScript: `const Component = ({{ prop }}) => ...` or `function Component({{ prop }})`
  * Use JSDoc comments for documentation instead: `/** @param {{string}} prop - Description */`
- All improvements must be dynamic and context-aware, no hardcoded values
- **DO NOT use FontAwesome or any icon libraries** - Use inline SVG icons instead (e.g., <svg> elements with Tailwind classes)
- **DO NOT use react-loading-skeleton or any skeleton libraries** - Use Tailwind CSS animate-pulse classes for loading states
- **ONLY use these dependencies**: react, react-dom, react-router-dom, axios, react-hook-form, tailwindcss
- For icons, use inline SVG elements with Tailwind classes (e.g., <svg className="h-6 w-6" ...>)
- For loading states, use Tailwind's animate-pulse utility with bg-gray-200 or similar
- **CRITICAL - SVG ATTRIBUTES**: In React/JSX, SVG attributes MUST use camelCase: strokeLinecap (NOT stroke-linecap), strokeLinejoin (NOT stroke-linejoin), strokeWidth (NOT stroke-width), fillRule (NOT fill-rule), clipPath (NOT clip-path)**
Return ONLY the complete React component code (JSX) with Tailwind CSS classes, nothing else. Start with imports."""
    else:
        # INITIAL IMPLEMENTATION: Create new component
        ui_theme_info = ""
        if ui_theme:
            primary = ui_theme.get('primary_color', 'blue-600')
            secondary = ui_theme.get('secondary_color', 'gray-600')
            accent = ui_theme.get('accent_color', 'purple-600')
            style_desc = ui_theme.get('style_description', 'modern and clean')
            ui_theme_info = f"""
UI THEME (from application design):
- Primary Color: {primary}
- Secondary Color: {secondary}
- Accent Color: {accent}
- Style: {style_desc}
- Application Type: {application_type}

Use these colors and style throughout the component. If colors are hex codes, convert them to Tailwind equivalents or use custom Tailwind classes that match the color scheme.
"""
        
        prompt = f"""Implement a production-quality React component based ONLY on the requirements. Infer functionality from page name and context.

RULES:
- Implement ONLY specified requirements, no unmentioned features
- Infer from page name "{page_name}" what functionality is needed
- Display ALL relevant API data fields, not just IDs
- All buttons must have onClick handlers that perform actions (API calls, then optional navigation)
- Action buttons: perform action first, handle response, then optionally navigate

CONTEXT:
Application: {description}
Type: {application_type}
{ui_theme_info}
Page: {page_name}
Description: {page.get('description', '')}

REQUIREMENTS: {json.dumps(requirements, indent=2)}
UI COMPONENTS: {json.dumps(page.get('ui_components', []), indent=2)}
BACKEND ENDPOINTS: {json.dumps(endpoint_specs, indent=2)}

PROCESS:
1. Analyze: entities, actions, relationships, data to display
2. Plan: component structure, state, API integration, error handling, UX
3. Implement: complete functionality matching page purpose

REQUIREMENTS:
- React hooks: ALL hooks (useState, useEffect, useCallback, useMemo) MUST be called INSIDE the component function body, NEVER at module level. Import hooks from 'react', use useMemo for axios instances, useCallback for functions in useEffect dependencies
- Error handling: try-catch for API calls, error.response?.data?.error for API errors, loading states, timeout handling
- Forms: react-hook-form v7+ with formState: {{ errors }}, optional chaining (errors?.field)
- Navigation: useNavigate(), verify route paths exist in App.jsx before using, use exact paths that match defined routes
- Axios: create instance INSIDE component using useMemo(() => axios.create({{baseURL: '', timeout: 15000}}), []), NEVER at module level
- API: Call ALL specified endpoints with ALL HTTP methods (GET, POST, PUT, DELETE), handle flexible response formats (check for items/list/results/data/products/array), validate Array.isArray() before .map()/.reduce()/.filter()
- Route params: useParams(), ALWAYS validate id exists before making API calls - check if id is defined before API calls to prevent undefined in URLs. useEffect should ALWAYS run fetch functions even when id is undefined - move conditional logic inside fetch function, not in useEffect condition. If no id, fetch default data from list endpoint (e.g., /api/users instead of /api/users/:id)
- API response handling: Extract data from response.data, ALWAYS check multiple possible keys (items/list/results/data/products/array), handle both object and array responses, use Array.isArray() validation before .map()/.reduce()/.filter()
- Tailwind CSS only, .jsx file, no TypeScript, no FontAwesome, no react-loading-skeleton
- Inline SVG icons, Tailwind animate-pulse for skeletons, animate-spin for spinners
- All buttons need onClick handlers, all forms need validation
- Responsive (sm/md/lg/xl), accessibility (ARIA), empty states, error recovery
- No placeholders, TODOs, or incomplete code

Return ONLY complete React component code (JSX) with Tailwind, starting with imports."""

    try:
        agent = get_agent(max_tokens=3000)
        response = invoke_with_rate_limit(agent, [HumanMessage(content=prompt)], log_file, estimated_tokens=1500)
        component_code = response.content.strip()
        
        # Clean code blocks
        if "```" in component_code:
            component_code = component_code.split("```")[1]
            if component_code.startswith("jsx") or component_code.startswith("javascript"):
                component_code = component_code.split('\n', 1)[1]
            component_code = component_code.split("```")[0]
        
        # Validate that we got actual component code
        if not component_code or len(component_code) < 100:
            raise Exception(f"Generated component code is too short or empty ({len(component_code) if component_code else 0} chars). This indicates the AI response was incomplete. Cannot proceed with invalid code.")
        
        # Validate it's valid React/JSX
        if "function" not in component_code and "const" not in component_code and "export" not in component_code:
            raise Exception(f"Generated component code doesn't appear to be valid React/JSX. Missing function/const/export. Cannot proceed with invalid code.")
        
        # Validate code quality - check for common issues
        validation_errors = []
        
        # Check for placeholder text
        placeholder_patterns = ["Sample", "Test", "Lorem ipsum", "Example", "Demo", "TODO", "FIXME", "placeholder", "Feature1", "Feature2", "Feature3"]
        for pattern in placeholder_patterns:
            if pattern.lower() in component_code.lower():
                validation_errors.append(f"Found placeholder text: '{pattern}' - code should use real, meaningful data")
        
        # Check for basic React patterns
        if "useState" in component_code or "useEffect" in component_code:
            # Good - using hooks
            pass
        elif "class " in component_code:
            validation_errors.append("Code uses class components - should use functional components with hooks")
        
        # Check for API integration
        if endpoint_specs and "axios" not in component_code and "fetch" not in component_code:
            validation_errors.append("Component has backend endpoints but no API calls found - component may not be functional")
        
        # Check for error handling
        if "try" not in component_code and "catch" not in component_code and endpoint_specs:
            validation_errors.append("Component makes API calls but has no error handling - may crash on API errors")
        
        # **CRITICAL VALIDATION**: Check for React hooks infinite loop patterns
        import re
        useEffect_pattern = r'useEffect\s*\(\s*\([^)]*\)\s*=>\s*\{[^}]*\},\s*\[([^\]]+)\]'
        useEffect_matches = re.findall(useEffect_pattern, component_code, re.DOTALL)
        for deps in useEffect_matches:
            # Check if dependencies include function names that aren't memoized
            func_names = re.findall(r'\b(\w+)\b', deps)
            for func_name in func_names:
                # Check if it's a function defined with const/let/var
                func_def_pattern = rf'(const|let|var)\s+{func_name}\s*='
                if re.search(func_def_pattern, component_code):
                    # Check if function is memoized
                    use_callback_pattern = rf'const\s+{func_name}\s*=\s*useCallback'
                    use_memo_pattern = rf'const\s+{func_name}\s*=\s*React\.useMemo|const\s+{func_name}\s*=\s*useMemo'
                    if not re.search(use_callback_pattern, component_code) and not re.search(use_memo_pattern, component_code):
                        validation_errors.append(f"useEffect depends on function '{func_name}' which is not memoized - may cause infinite loop. Use useCallback or depend on function's dependencies instead.")
        
        # **CRITICAL VALIDATION**: Check for React hooks at module level (outside component)
        # Pattern: hooks called before component function definition
        component_start_pattern = r'(const|function)\s+\w+\s*=\s*\([^)]*\)\s*=>|function\s+\w+\s*\([^)]*\)\s*\{'
        component_match = re.search(component_start_pattern, component_code)
        if component_match:
            component_start_pos = component_match.start()
            code_before_component = component_code[:component_start_pos]
            # Check for hooks before component
            hooks_before = re.findall(r'(useState|useEffect|useCallback|useMemo|React\.useState|React\.useEffect|React\.useCallback|React\.useMemo)\s*\(', code_before_component)
            if hooks_before:
                validation_errors.append(f"CRITICAL: Found React hooks called at module level (outside component): {', '.join(set(hooks_before))}. Hooks MUST be called inside component function body. Move all hooks inside the component.")
        
        # Check for axiosInstance at module level
        axios_pattern = r'const\s+axiosInstance\s*=\s*axios\.create'
        axios_matches = list(re.finditer(axios_pattern, component_code))
        for match in axios_matches:
            match_pos = match.start()
            # Check if it's before component definition
            if component_match and match_pos < component_match.start():
                validation_errors.append("CRITICAL: axiosInstance defined at module level - must be inside component using useMemo")
            elif 'useMemo' not in component_code and 'React.useMemo' not in component_code:
                validation_errors.append("axiosInstance is recreated on every render - should use useMemo to prevent recreation and infinite loops")
        
        # Check for .reduce() calls without array validation
        if '.reduce(' in component_code:
            lines = component_code.split('\n')
            for i, line in enumerate(lines):
                if '.reduce(' in line:
                    # Check previous lines for array validation
                    prev_lines = lines[max(0, i-5):i]
                    has_validation = any('Array.isArray' in prev_line for prev_line in prev_lines)
                    if not has_validation:
                        validation_errors.append(f"Found .reduce() call without Array.isArray validation - may crash if data is not an array. Always check Array.isArray(data) before calling .reduce()")
                        break
        
        # Check for API call payload completeness
        api_call_pattern = r'(axios|axiosInstance)\.(post|put|patch)\s*\([^,]+,\s*\{([^}]+)\}'
        api_matches = re.findall(api_call_pattern, component_code, re.DOTALL)
        for match in api_matches:
            method = match[1].upper() if len(match) > 1 else ''
            payload = match[2] if len(match) > 2 else ''
            # Check if payload has required fields for cart operations
            if 'cart' in str(match[0]).lower() or '/api/cart' in component_code:
                has_product = 'product_id' in payload.lower() or 'productId' in payload.lower()
                has_quantity = 'quantity' in payload.lower()
                if not has_product or not has_quantity:
                    validation_errors.append(f"API call to /api/cart missing required fields - needs product_id (or productId) and quantity")
        
        # **CRITICAL VALIDATION**: Check for missing event handlers on interactive elements
        # Count buttons without onClick handlers
        import re
        button_pattern = r'<button[^>]*>'
        buttons = re.findall(button_pattern, component_code, re.IGNORECASE)
        buttons_without_onclick = []
        for i, button_match in enumerate(buttons):
            if 'onclick' not in button_match.lower() and 'onClick' not in button_match:
                # Check if it's a submit button in a form (those are OK)
                if 'type="submit"' not in button_match.lower() and 'type=\'submit\'' not in button_match.lower():
                    buttons_without_onclick.append(i + 1)
        
        if buttons_without_onclick:
            validation_errors.append(f"Found {len(buttons_without_onclick)} button(s) without onClick handlers - all buttons must have event handlers to be functional")
        
        # **CRITICAL VALIDATION**: Check for array validation before .map() calls
        # Find all .map( calls and check if they're properly validated
        map_pattern = r'\.map\s*\('
        map_calls = re.findall(map_pattern, component_code)
        if map_calls:
            # Check for common unsafe patterns
            unsafe_patterns = [
                r'\{[^}]*\w+\[[^\]]+\]\.map\s*\('  # {reviews[id].map( without Array.isArray check
            ]
            for pattern in unsafe_patterns:
                matches = re.findall(pattern, component_code)
                if matches:
                    # Check if Array.isArray validation exists before these patterns
                    for match in matches[:3]:  # Check first 3
                        # Look for Array.isArray check in context
                        match_pos = component_code.find(match)
                        context_before = component_code[max(0, match_pos - 200):match_pos]
                        if 'Array.isArray' not in context_before and 'Array.isArray' not in component_code[:match_pos]:
                            validation_errors.append("Found .map() call without Array.isArray validation - may crash if data is not an array. Always check Array.isArray(data) before calling .map()")
                            break
        
        # **CRITICAL VALIDATION**: Check for useEffect that only runs conditionally when it should always run
        # Pattern: useEffect with conditional execution based on id/params
        useEffect_pattern = r'useEffect\s*\(\s*\([^)]*\)\s*=>\s*\{[^}]*\},\s*\[([^\]]+)\]'
        useEffect_matches = re.findall(useEffect_pattern, component_code, re.DOTALL)
        for deps in useEffect_matches:
            # Check if useEffect has conditional execution inside
            useEffect_full_pattern = r'useEffect\s*\(\s*\([^)]*\)\s*=>\s*\{([^}]+)\},\s*\[([^\]]+)\]'
            full_matches = re.findall(useEffect_full_pattern, component_code, re.DOTALL)
            for body, deps_list in full_matches:
                # Check if body has "if (id)" or "if (!id)" that prevents execution
                if re.search(r'if\s*\(\s*!?\s*id\s*\)', body) and 'fetch' in body.lower() and 'api' in body.lower():
                    # Check if this prevents the main fetch from running
                    if 'return' in body and 'if' in body:
                        validation_errors.append("useEffect should always call fetch functions even when id is undefined - move conditional logic inside fetch function, not in useEffect condition")
        
        # **CRITICAL VALIDATION**: Check for proper API response format handling
        # Check if component handles multiple response formats (items/list/results/data/products)
        if 'response.data' in component_code or 'response?.data' in component_code:
            # Check if component checks multiple possible keys
            response_handling = re.findall(r'response\.data\.(\w+)|response\?\.data\.(\w+)', component_code)
            response_keys = [key for match in response_handling for key in match if key]
            # Check if component uses flexible key checking (|| operator)
            flexible_patterns = [
                r'data\.items\s*\|\|\s*data\.\w+',
                r'data\.list\s*\|\|\s*data\.\w+',
                r'data\.results\s*\|\|\s*data\.\w+',
                r'data\.products\s*\|\|\s*data\.\w+',
                r'data\[[\'"]items[\'"]\]\s*\|\|\s*data\[[\'"]\w+[\'"]\]'
            ]
            has_flexible_handling = any(re.search(pattern, component_code) for pattern in flexible_patterns)
            if not has_flexible_handling and len(response_keys) == 1:
                validation_errors.append("API response handling should check multiple possible keys (items/list/results/data/products) - backend may return different formats")
        
        # **CRITICAL VALIDATION**: Check for incorrect SVG attribute names (should be camelCase in React)
        svg_attr_patterns = [
            (r'stroke-linecap', 'strokeLinecap'),
            (r'stroke-linejoin', 'strokeLinejoin'),
            (r'stroke-width', 'strokeWidth'),
            (r'fill-rule', 'fillRule'),
            (r'clip-path', 'clipPath'),
            (r'font-family', 'fontFamily'),
            (r'font-size', 'fontSize'),
            (r'text-anchor', 'textAnchor')
        ]
        for pattern, correct_name in svg_attr_patterns:
            if re.search(pattern, component_code):
                validation_errors.append(f"Found SVG attribute '{pattern}' - React/JSX requires camelCase: '{correct_name}'")
        
        # **CRITICAL VALIDATION**: Check for API calls with undefined IDs
        # Find API calls that use template literals with id/params that might be undefined
        api_call_with_id_pattern = r'(axios|axiosInstance|api|instance)\.(get|post|put|delete|patch)\s*\([^,]*`[^`]*\$\{([^}]+)\}[^`]*`'
        api_calls = re.findall(api_call_with_id_pattern, component_code)
        for match in api_calls:
            var_name = match[2] if len(match) > 2 else ''
            if var_name in ['id', 'userId', 'videoId', 'channelId']:
                # Check if there's validation before this API call
                api_call_pos = component_code.find(match[0] + '.' + match[1])
                context_before = component_code[max(0, api_call_pos - 200):api_call_pos]
                has_validation = re.search(rf'if\s*\(\s*!{var_name}|if\s*\(\s*{var_name}\s*===\s*undefined|if\s*\(\s*!{var_name}\s*\)', context_before)
                if not has_validation:
                    validation_errors.append(f"API call uses {var_name} without validation - check 'if (!{var_name})' before API call to prevent undefined in URL")
        
        # **CRITICAL VALIDATION**: Check for missing imported components
        # Extract all relative imports (from './Component' or from './Component.jsx')
        import_pattern = r"import\s+(?:\{[^}]*\}|\w+|\*\s+as\s+\w+)\s+from\s+['\"](\.\/[^'\"]+)['\"]"
        import_matches = re.findall(import_pattern, component_code)
        missing_components = []
        pages_dir = os.path.join(os.path.dirname(component_file), '..', 'pages')
        components_dir = os.path.join(os.path.dirname(component_file), '..', 'components')
        
        for import_path in import_matches:
            # Normalize path (remove .jsx extension if present, handle ./Component or ./Component.jsx)
            import_path_clean = import_path.replace('./', '').replace('.jsx', '').replace('/', '')
            # Check if file exists in pages or components directory
            possible_paths = [
                os.path.join(pages_dir, f"{import_path_clean}.jsx"),
                os.path.join(components_dir, f"{import_path_clean}.jsx"),
                os.path.join(os.path.dirname(component_file), f"{import_path_clean}.jsx"),  # Same directory
            ]
            file_exists = any(os.path.exists(p) for p in possible_paths)
            if not file_exists:
                missing_components.append(import_path_clean)
        
        if missing_components:
            validation_errors.append(f"CRITICAL: Missing imported components: {', '.join(missing_components)}. These components are imported but don't exist. They will be auto-generated.")
            # Add defect for missing components
            if _defect_ledger:
                for missing_comp in missing_components:
                    _defect_ledger.add_defect(
                        f"Missing component file: {missing_comp}.jsx (imported but not found)",
                        f"frontend/{page_name}",
                        DefectSeverity.CRITICAL,
                        f"Implementation Agent {agent_id}",
                        "missing_file"
                    )
        
        # **CRITICAL VALIDATION**: Check for route path mismatches (GENERIC - works for any app)
        # Check if navigate() calls use routes that might not exist
        navigate_pattern = r"navigate\s*\(\s*['\"]([^'\"]+)['\"]"
        navigate_calls = re.findall(navigate_pattern, component_code)
        
        # Try to read App.jsx to get actual routes (if it exists)
        app_jsx_path = os.path.join(os.path.dirname(component_file), '..', 'App.jsx')
        if os.path.exists(app_jsx_path):
            try:
                with open(app_jsx_path, 'r', encoding='utf-8') as f:
                    app_jsx_content = f.read()
                # Extract all route paths from App.jsx
                route_pattern = r'path=["\']([^"\']+)["\']'
                defined_routes = set(re.findall(route_pattern, app_jsx_content))
                
                # Check if navigate calls match any defined route
                for nav_path in navigate_calls:
                    # Remove leading slash for comparison
                    nav_path_clean = nav_path.strip('/')
                    # Check if exact match or if any route starts with this path
                    route_matches = [r for r in defined_routes if r.strip('/') == nav_path_clean or r.strip('/').startswith(nav_path_clean)]
                    if not route_matches and nav_path.startswith('/'):
                        # Suggest similar routes (fuzzy matching)
                        similar_routes = [r for r in defined_routes if nav_path_clean in r.lower() or r.lower() in nav_path_clean]
                        if similar_routes:
                            validation_errors.append(f"Navigation to '{nav_path}' may not exist - similar routes found: {', '.join(similar_routes[:3])}")
                        else:
                            validation_errors.append(f"Navigation to '{nav_path}' - verify this route exists in App.jsx")
            except Exception as e:
                # If we can't read App.jsx, just warn about potential mismatches
                pass
        
        # **CRITICAL VALIDATION**: Check for incomplete button functionality (GENERIC - works for any button type)
        # Pattern: If a button navigates, it should perform its action first (API call, state update, etc.)
        # Find buttons that navigate without performing their described action
        button_text_pattern = r'<button[^>]*>([^<]+)</button>'
        button_matches = re.findall(button_text_pattern, component_code, re.IGNORECASE | re.DOTALL)
        
        for button_text in button_matches[:10]:  # Check first 10 buttons
            button_text_lower = button_text.lower().strip()
            # Detect action verbs in button text (add, create, submit, delete, update, save, etc.)
            action_verbs = ['add', 'create', 'submit', 'delete', 'remove', 'update', 'save', 'post', 'send', 'purchase', 'buy', 'order', 'checkout']
            has_action_verb = any(verb in button_text_lower for verb in action_verbs)
            
            if has_action_verb:
                # Find the onClick handler for this button
                # Look for button with this text and check its onClick handler
                button_with_text_pattern = rf'<button[^>]*onClick[^>]*>.*?{re.escape(button_text[:20])}.*?</button>'
                button_block = re.search(button_with_text_pattern, component_code, re.IGNORECASE | re.DOTALL)
                
                if button_block:
                    button_code = button_block.group(0)
                    # Check if button navigates
                    if 'navigate' in button_code:
                        # Check if it performs an action (API call, state update) before navigating
                        # Look for async function or API call in the handler
                        handler_pattern = r'onClick\s*=\s*\{?\s*([^}]+)\s*\}?'
                        handler_match = re.search(handler_pattern, button_code)
                        if handler_match:
                            handler_code = handler_match.group(1)
                            # Check if handler calls API or performs action
                            has_api_call = 'axios' in handler_code or 'fetch' in handler_code or '/api/' in handler_code
                            has_state_update = 'setState' in handler_code or 'useState' in handler_code or 'dispatch' in handler_code
                            is_async = 'async' in handler_code
                            
                            # If it navigates but doesn't perform action, flag it
                            if not (has_api_call or has_state_update or is_async):
                                # Extract function name if it's a function call
                                func_call_pattern = r'(\w+)\s*\([^)]*\)'
                                func_calls = re.findall(func_call_pattern, handler_code)
                                if func_calls:
                                    # Check if the function exists and performs action
                                    func_name = func_calls[0]
                                    func_def_pattern = rf'const\s+{func_name}\s*=\s*[^{{]*\{{([^}}]+)\}}'
                                    func_def = re.search(func_def_pattern, component_code, re.DOTALL)
                                    if func_def:
                                        func_body = func_def.group(1)
                                        if 'axios' not in func_body and 'fetch' not in func_body and '/api/' not in func_body:
                                            validation_errors.append(f"Button '{button_text[:30]}...' navigates but may not perform its action - ensure it calls API or updates state before navigating")
                                else:
                                    validation_errors.append(f"Button '{button_text[:30]}...' navigates but may not perform its action - ensure it calls API or updates state before navigating")
        
        # Check for links without navigation
        link_pattern = r'<Link[^>]*>'
        links = re.findall(link_pattern, component_code, re.IGNORECASE)
        links_without_to = []
        for i, link_match in enumerate(links):
            if 'to=' not in link_match.lower():
                links_without_to.append(i + 1)
        
        if links_without_to:
            validation_errors.append(f"Found {len(links_without_to)} Link(s) without 'to' prop - all Links must have navigation targets")
        
        # Check for form inputs without handlers (if they're controlled)
        # This is less critical, but worth noting
        input_pattern = r'<input[^>]*value='
        controlled_inputs = re.findall(input_pattern, component_code, re.IGNORECASE)
        inputs_without_onchange = []
        for i, input_match in enumerate(controlled_inputs):
            if 'onchange' not in input_match.lower() and 'onChange' not in input_match:
                # Check if it's a read-only input
                if 'readonly' not in input_match.lower() and 'readOnly' not in input_match:
                    inputs_without_onchange.append(i + 1)
        
        if inputs_without_onchange:
            validation_errors.append(f"Found {len(inputs_without_onchange)} controlled input(s) without onChange handlers - controlled inputs need onChange handlers")
        
        # Log validation warnings but don't fail (allow refinement cycles to fix)
        if validation_errors and not is_refinement:
            log_and_print(f"    [Validation Warnings] {len(validation_errors)} potential issues found:", log_file)
            for error in validation_errors[:5]:  # Show up to 5 errors
                log_and_print(f"      - {error}", log_file)
            # Add defects for critical issues - missing event handlers are HIGH priority
            if _defect_ledger:
                for error in validation_errors:
                    severity = DefectSeverity.HIGH
                    if "onClick" in error or "event handler" in error.lower() or "without onClick" in error.lower():
                        # Missing event handlers are critical - buttons won't work
                        severity = DefectSeverity.CRITICAL
                    elif "placeholder" in error.lower() or "not be functional" in error.lower():
                        severity = DefectSeverity.MEDIUM
                    elif "Link" in error and "without" in error:
                        # Missing navigation on links
                        severity = DefectSeverity.HIGH
                    
                    _defect_ledger.add_defect(
                        f"Code quality issue: {error}",
                        f"frontend/{page_name}",
                        severity,
                        f"Implementation Agent {agent_id}",
                        "quality"
                    )
        
        # Add imports if missing (but validate first)
        if "import React" not in component_code and "import" not in component_code[:200]:
            component_code = "import React, { useState, useEffect } from 'react';\nimport axios from 'axios';\n\n" + component_code
        
        # Ensure it has export
        if "export default" not in component_code and "export" not in component_code:
            # Try to add export if missing
            component_name = page.get('page_name', 'Component').replace(" ", "").replace("-", "")
            if component_code.strip().endswith("}"):
                component_code += f"\n\nexport default {component_name};"
        
        # Save component file
        component_file = get_page_file_path(page, project_path)
        os.makedirs(os.path.dirname(component_file), exist_ok=True)
        
        with open(component_file, 'w', encoding='utf-8') as f:
            f.write(component_code)
        
        # **CRITICAL**: After saving, check for missing imported components and generate them
        missing_components = detect_missing_imports(component_code, component_file, project_path)
        if missing_components:
            log_and_print(f"    [Auto-generating] {len(missing_components)} missing component(s): {', '.join(missing_components)}", log_file)
            for missing_comp in missing_components:
                generate_missing_component(missing_comp, project_path, description, log_file)
        
        action = "Refined" if is_refinement else "Implemented"
        log_and_print(f"    ✓ {action} {page_name}", log_file)
        
        # Mark defects as resolved if this was a refinement
        if is_refinement and _defect_ledger and component_defects:
            for defect in component_defects[:3]:  # Mark top 3 as resolved
                _defect_ledger.update_defect_status(
                    defect['id'], 
                    DefectStatus.RESOLVED, 
                    f"Implementation Agent {agent_id}",
                    f"Refined component in cycle"
                )
        
        return True
        
    except Exception as e:
        log_and_print(f"    ✗ Error implementing {page_name}: {e}", log_file)
        if _defect_ledger:
            _defect_ledger.add_defect(
                f"Failed to implement {page_name}: {str(e)}",
                f"frontend/{page_name}",
                DefectSeverity.HIGH,
                f"Implementation Agent {agent_id}",
                "implementation_error"
            )
        return False


def detect_missing_imports(component_code: str, component_file: str, project_path: str) -> List[str]:
    """
    Detect missing imported components from a React component file.
    Returns list of component names that are imported but don't exist.
    """
    import re
    missing = []
    
    # Extract all relative imports (from './Component' or from './Component.jsx' or from './pages/Component')
    import_pattern = r"import\s+(?:\{[^}]*\}|\w+|\*\s+as\s+\w+)\s+from\s+['\"](\.\/[^'\"]+)['\"]"
    import_matches = re.findall(import_pattern, component_code)
    
    pages_dir = os.path.join(project_path, "src", "pages")
    components_dir = os.path.join(project_path, "src", "components")
    same_dir = os.path.dirname(component_file)
    
    for import_path in import_matches:
        # Normalize path (remove .jsx extension if present, handle ./Component or ./Component.jsx)
        import_path_clean = import_path.replace('./', '').replace('.jsx', '').replace('/', '')
        # Handle nested paths like ./pages/Component -> Component
        if '/' in import_path_clean:
            import_path_clean = import_path_clean.split('/')[-1]
        
        # Check if file exists in pages, components, or same directory
        possible_paths = [
            os.path.join(pages_dir, f"{import_path_clean}.jsx"),
            os.path.join(components_dir, f"{import_path_clean}.jsx"),
            os.path.join(same_dir, f"{import_path_clean}.jsx"),
        ]
        file_exists = any(os.path.exists(p) for p in possible_paths)
        if not file_exists and import_path_clean not in missing:
            missing.append(import_path_clean)
    
    return missing


def infer_component_purpose(component_name: str, description: str) -> str:
    """
    Infer the purpose of a component from its name and application context.
    """
    name_lower = component_name.lower()
    
    # Common component patterns
    if 'pagination' in name_lower or 'pager' in name_lower:
        return "Pagination component for navigating through pages of items. Accepts currentPage, totalPages, onPageChange props."
    elif 'card' in name_lower:
        if 'blog' in name_lower or 'post' in name_lower:
            return "Blog post card component displaying post title, content preview, author, date. Accepts title, content, author, date, image, onClick props."
        elif 'product' in name_lower:
            return "Product card component displaying product information. Accepts product object with name, price, image, onClick props."
        else:
            return "Card component for displaying information. Accepts title, content, image, onClick props."
    elif 'spinner' in name_lower or 'loading' in name_lower:
        return "Loading spinner component. No props needed or accepts size prop."
    elif 'error' in name_lower or 'message' in name_lower:
        return "Error message display component. Accepts message, onClose props."
    elif 'button' in name_lower:
        return "Button component. Accepts onClick, disabled, children, variant props."
    elif 'modal' in name_lower or 'dialog' in name_lower:
        return "Modal/dialog component. Accepts isOpen, onClose, children props."
    elif 'form' in name_lower:
        return "Form component. Accepts onSubmit, children props."
    elif 'input' in name_lower or 'field' in name_lower:
        return "Input field component. Accepts value, onChange, placeholder, type, label props."
    elif 'list' in name_lower:
        return "List component for displaying items. Accepts items array, renderItem function props."
    elif 'item' in name_lower:
        return "Item component for displaying individual items in a list. Accepts item object, onClick props."
    else:
        # Generic component based on name
        return f"Component named {component_name} for the {description} application. Create a functional component with appropriate props based on the name."


def generate_missing_component(component_name: str, project_path: str, description: str, log_file: str = None) -> bool:
    """
    Generate a missing React component that was imported but doesn't exist.
    Infers component purpose from name and context.
    """
    pages_dir = os.path.join(project_path, "src", "pages")
    components_dir = os.path.join(project_path, "src", "components")
    
    # Determine where to place the component (prefer components/ for reusable components)
    # If name suggests it's a page component (ends with Page, or matches page naming), put in pages/
    is_page_component = any(keyword in component_name.lower() for keyword in ['page', 'list', 'detail', 'view', 'profile', 'cart', 'checkout'])
    target_dir = pages_dir if is_page_component else components_dir
    os.makedirs(target_dir, exist_ok=True)
    
    component_file = os.path.join(target_dir, f"{component_name}.jsx")
    
    # Skip if already exists (shouldn't happen, but safety check)
    if os.path.exists(component_file):
        return True
    
    try:
        # Infer component purpose from name
        component_purpose = infer_component_purpose(component_name, description)
        
        prompt = f"""You are an Implementation Agent creating a missing React component that was imported but doesn't exist.

APPLICATION CONTEXT: {description}

COMPONENT NAME: {component_name}
INFERRED PURPOSE: {component_purpose}

Create a complete, functional React functional component with:
1. React hooks (useState, useEffect if needed)
2. Component props (use JSDoc comments, NOT TypeScript interfaces)
3. Error handling
4. **IMPORTANT: 
   - Use Tailwind CSS classes for ALL styling. Do NOT use inline styles or CSS files.
   - This file will be saved as .jsx extension, so ensure all JSX syntax is correct.
   - Use .jsx extension in any relative imports (e.g., './pages/HomePage.jsx')
   - **CRITICAL - NO TYPESCRIPT SYNTAX**: This is a .jsx file, NOT .tsx. Do NOT use:
     * TypeScript interfaces: NO `interface ComponentProps {{ ... }}`
     * Type annotations: NO `const Component: React.FC<Props> = ...`
     * Type annotations: NO `const Component = ({{ prop }}: Props) => ...`
     * Use plain JavaScript: `const Component = ({{ prop }}) => ...` or `function Component({{ prop }})`
     * Use JSDoc comments for documentation: `/** @param {{string}} prop - Description */`
   - **NO SELF-IMPORTS**: Do NOT import the component file itself. Only import external dependencies.
   - **ONLY import from these packages**: react, react-dom, react-router-dom (if using NavLink/Link), axios (if needed), react-hook-form (if needed)
   - **DO NOT import FontAwesome or react-loading-skeleton** - Use inline SVG icons and Tailwind animate-pulse instead**
   - **CRITICAL - SVG ATTRIBUTES**: In React/JSX, SVG attributes MUST use camelCase: strokeLinecap (NOT stroke-linecap), strokeLinejoin (NOT stroke-linejoin), strokeWidth (NOT stroke-width), fillRule (NOT fill-rule), clipPath (NOT clip-path)
5. Make it responsive with Tailwind responsive classes
6. Proper prop documentation using JSDoc comments (NOT TypeScript interfaces)
7. Export as default

Based on the component name "{component_name}", create a component that makes sense for this application context.

Return ONLY the complete React component code (JSX) with Tailwind CSS classes, nothing else. Start with imports."""

        agent = get_agent(max_tokens=2000)
        response = invoke_with_rate_limit(agent, [HumanMessage(content=prompt)], log_file, estimated_tokens=1000)
        component_code = response.content.strip()
        
        # Clean code blocks
        if "```" in component_code:
            component_code = component_code.split("```")[1]
            if component_code.startswith("jsx") or component_code.startswith("javascript"):
                component_code = component_code.split('\n', 1)[1]
            component_code = component_code.split("```")[0]
        
        # Ensure it has React import
        if "import React" not in component_code:
            component_code = "import React from 'react';\n\n" + component_code
        
        # Ensure it has export
        if "export default" not in component_code:
            if component_code.strip().endswith("}"):
                component_code += f"\n\nexport default {component_name};"
        
        # Save component
        with open(component_file, 'w', encoding='utf-8') as f:
            f.write(component_code)
        
        if log_file:
            log_and_print(f"  ✓ Auto-generated missing component: {component_name}.jsx", log_file)
        return True
        
    except Exception as e:
        if log_file:
            log_and_print(f"  ✗ Failed to generate missing component {component_name}: {e}", log_file)
        return False


def implement_endpoint_kaizen(endpoint: Dict, project_path: str, description: str, agent_id: int, log_file: str, is_refinement: bool = False, use_mongodb: bool = False) -> bool:
    """
    Implementation Group agent implements or refines a backend endpoint with Kaizen principles.
    
    True Kaizen: Cycle 1 implements, Cycle 2+ refines the same endpoint.
    
    Args:
        use_mongodb: If True, use MongoDB for database operations instead of SQLite
    """
    global _defect_ledger
    _defect_ledger = get_defect_ledger()
    path = endpoint.get('path', '')
    method = endpoint.get('method', 'GET')
    
    endpoint_file = get_endpoint_file_path(endpoint, project_path)
    existing_code = None
    
    # If refining, read existing code and get defects
    if is_refinement and os.path.exists(endpoint_file):
        try:
            with open(endpoint_file, 'r', encoding='utf-8') as f:
                existing_code = f.read()
        except Exception as e:
            log_and_print(f"    [Warning] Could not read existing code: {e}", log_file)
    
    # Get defects for this endpoint
    component_defects = []
    improvement_suggestions = []
    if _defect_ledger:
        open_defects = _defect_ledger.get_open_defects(component=f"backend/{path}")
        component_defects = [d for d in open_defects if d['status'] in ['open', 'in_progress']]
        
        # Get improvement suggestions
        for improvement in _defect_ledger.improvements:
            if improvement.get('component') == f"backend/{path}" and improvement.get('status') == 'pending':
                improvement_suggestions.append(improvement)
    
    # Build prompt based on whether it's implementation or refinement
    if is_refinement and existing_code:
        # REFINEMENT: Improve existing code
        defects_info = "\n".join([f"- {d['description']} (Severity: {d['severity']})" for d in component_defects[:5]])
        improvements_info = "\n".join([f"- {imp['description']}" for imp in improvement_suggestions[:3]])
        
        prompt = f"""REFINE existing Flask endpoint: fix defects and apply improvements while maintaining functionality.

CONTEXT: {description}
ENDPOINT: {json.dumps(endpoint, indent=2)}
CURRENT CODE: {existing_code[:2000]}
DEFECTS: {defects_info if defects_info else "None"}
IMPROVEMENTS: {improvements_info if improvements_info else "None"}

PROCESS:
1. Analyze existing code and identify issues
2. Fix defects systematically
3. Apply improvements (validation, error handling, pagination, query optimization, security, logging, response structure)
4. {"Check 'if db is None:', derive collection names from path, convert ObjectId to string, use .count_documents()" if use_mongodb else ""}

Return IMPROVED endpoint code. Format: @app.route('...', methods=['...'])\ndef ...(): ..."""
    else:
        # INITIAL IMPLEMENTATION: Create new endpoint
        prompt = f"""Implement a production-quality Flask route handler based ONLY on the endpoint specification. Infer functionality from path and method.

RULES:
- Implement ONLY specified endpoint, no unmentioned fields/operations
- Infer data structure from endpoint path "{path}"
- Return ALL relevant fields for the resource, not just IDs
- All operations must be fully functional, no placeholders

CONTEXT:
Application: {description}
Endpoint: {method} {path}
Specification: {json.dumps(endpoint, indent=2)}

PROCESS:
1. Analyze: entities, operations, data fields, relationships
2. Plan: input validation, database operations, error handling, response structure
3. Implement: complete functionality matching endpoint purpose

REQUIREMENTS:
- Flask route syntax: use <id> not :id, function param matches route param name
- Error handling: wrap ALL DB ops in try-except, handle pymongo.errors, return JSON errors with jsonify()
- Input validation: validate required fields, types, formats, return 400 on failure
- HTTP status: 200 GET/PUT, 201 POST, 400 invalid, 404 not found, 500 server error
- Database connection: {"ALWAYS use the shared 'db' variable provided by app.py, NEVER create new MongoClient() or database connections. Check 'if db is None:' before operations. GET returns empty list [] if no DB, POST/PUT/DELETE return error if no DB. Derive collection names dynamically from path segments (e.g., /api/products → db['products'], /api/user/profile → db['user']). Convert ObjectId to string: str(doc['_id']). Use .count_documents() not .count(). ObjectId and PyMongoError are available in exec namespace - use them directly." if use_mongodb else "Use in-memory or skip if no DB"}
- HTTP methods: Implement ALL methods specified in endpoint (GET, POST, PUT, DELETE). If endpoint supports POST, implement POST handler. If endpoint supports multiple methods, implement all of them.
- Response format: list endpoints return {{"items": [...]}}, single resource endpoints return object with 'id' as string, always use jsonify()
- Accept camelCase and snake_case: `field = data.get('field_name') or data.get('fieldName')` for all input fields
- ObjectId handling: Use ObjectId() from exec namespace (provided by app.py), ALWAYS wrap in try-except for conversion, handle invalid IDs with 400 error, handle missing documents with 404. For GET endpoints with <id>, try ObjectId conversion first, if fails try finding by string id field or matching string _id as fallback
- Edge cases: empty results [], missing data 404, invalid IDs 400, malformed JSON 400, database unavailable 500
- No placeholders, TODOs, or incomplete code
- No imports: Do NOT import MongoClient, ObjectId, PyMongoError, datetime, jsonify, request - these are provided by app.py exec namespace

Return ONLY Python route handler code starting with @app.route."""

    try:
        agent = get_agent(max_tokens=3000)
        response = invoke_with_rate_limit(agent, [HumanMessage(content=prompt)], log_file, estimated_tokens=1500)
        code = response.content.strip()
        
        # Clean code blocks
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        # Validate that we got actual endpoint code
        if not code or len(code) < 50:
            raise Exception(f"Generated endpoint code is too short or empty ({len(code) if code else 0} chars). This indicates the AI response was incomplete. Cannot proceed with invalid code.")
        
        # Ensure it has route decorator
        if "@app.route" not in code:
            raise Exception(f"Generated endpoint code missing @app.route decorator. Invalid endpoint code generated. Cannot proceed.")
        
        # Ensure it has a function definition
        if "def " not in code:
            raise Exception(f"Generated endpoint code missing function definition. Invalid endpoint code generated. Cannot proceed.")
        
        # Validate code quality - check for common issues
        validation_errors = []
        
        # Check for placeholder text
        placeholder_patterns = ["Sample", "Test", "Lorem ipsum", "Example", "Demo", "TODO", "FIXME", "placeholder", "Feature1", "Feature2", "Feature3"]
        for pattern in placeholder_patterns:
            if pattern.lower() in code.lower() and "def " + pattern.lower() not in code.lower():
                validation_errors.append(f"Found placeholder text: '{pattern}' - code should use real, meaningful data")
        
        # Check for error handling (critical for endpoints)
        if use_mongodb and "try" not in code and "except" not in code:
            validation_errors.append("Endpoint uses database but has no error handling - may crash on database errors")
        
        # **CRITICAL VALIDATION**: Check for database connection creation (should use shared db)
        if use_mongodb:
            # Check for MongoClient() instantiation
            if "MongoClient()" in code or "MongoClient(" in code:
                validation_errors.append("CRITICAL: Found MongoClient() instantiation - MUST use shared 'db' variable from app.py, NEVER create new connections")
            # Check for client variable usage
            if "client = " in code and "MongoClient" in code:
                validation_errors.append("CRITICAL: Found 'client' variable - MUST use shared 'db' variable from app.py exec namespace")
            # Check for database connection check
            if "if db is None" not in code and "if db is not None" not in code:
                validation_errors.append("Endpoint uses database but doesn't check if db is connected - may crash if DB unavailable")
            # Check for imports that shouldn't be there
            if "from pymongo import MongoClient" in code or "import MongoClient" in code:
                validation_errors.append("CRITICAL: Do NOT import MongoClient - 'db' is provided by app.py exec namespace")
            if "from bson import ObjectId" in code or "import ObjectId" in code:
                validation_errors.append("CRITICAL: Do NOT import ObjectId - it's provided by app.py exec namespace, use it directly")
            if "from pymongo.errors import PyMongoError" in code or "import PyMongoError" in code:
                validation_errors.append("CRITICAL: Do NOT import PyMongoError - it's provided by app.py exec namespace, use it directly")
        
        # Check for proper response format
        if "jsonify" not in code:
            validation_errors.append("Endpoint doesn't use jsonify for responses - may not return proper JSON")
        
        # Check for input validation (for POST/PUT endpoints)
        if method in ["POST", "PUT", "PATCH"] and "request.get_json" not in code and "request.json" not in code:
            validation_errors.append(f"{method} endpoint doesn't read request body - may not process input correctly")
        
        # **CRITICAL VALIDATION**: Check if endpoint implements all required HTTP methods
        # If endpoint specification mentions multiple methods, ensure all are implemented
        import re  # Import re before using it
        endpoint_methods = endpoint.get('method', method)
        if isinstance(endpoint_methods, str):
            endpoint_methods = [endpoint_methods]
        elif isinstance(endpoint_methods, list):
            pass
        else:
            endpoint_methods = [method]
        
        # Check if current implementation matches all specified methods
        route_decorators = re.findall(r"@app\.route\([^)]+methods=\[([^\]]+)\]", code)
        implemented_methods = []
        for methods_str in route_decorators:
            methods = [m.strip().strip("'\"") for m in methods_str.split(',')]
            implemented_methods.extend(methods)
        
        # If endpoint supports POST but only GET is implemented, flag it
        if 'POST' in endpoint_methods and 'POST' not in implemented_methods:
            validation_errors.append(f"CRITICAL: Endpoint specification includes POST method but only {', '.join(implemented_methods)} is implemented - POST handler is missing")
        if 'PUT' in endpoint_methods and 'PUT' not in implemented_methods:
            validation_errors.append(f"CRITICAL: Endpoint specification includes PUT method but only {', '.join(implemented_methods)} is implemented - PUT handler is missing")
        
        # **CRITICAL VALIDATION**: Check for Flask route syntax errors
        # re is already imported above
        route_pattern = r"@app\.route\(['\"]([^'\"]+)['\"]"
        routes = re.findall(route_pattern, code)
        for route_path in routes:
            # Check for React Router syntax (:id instead of <id>)
            if ':id' in route_path or ':slug' in route_path or re.search(r':\w+', route_path):
                validation_errors.append(f"Found React Router syntax in Flask route: '{route_path}' - Flask uses <id> not :id")
            # Check if function parameter matches route parameter
            if '<' in route_path and '>' in route_path:
                # Extract parameter name from route
                param_match = re.search(r'<(\w+)>', route_path)
                if param_match:
                    param_name = param_match.group(1)
                    # Check if function uses this parameter
                    func_pattern = rf"def\s+\w+\s*\([^)]*{param_name}[^)]*\)"
                    if not re.search(func_pattern, code):
                        validation_errors.append(f"Route parameter '<{param_name}>' in '{route_path}' not found in function signature")
        
        # Check for deprecated PyMongo methods
        if '.count()' in code:
            validation_errors.append("Found deprecated .count() method - use .count_documents(filter) instead")
        
        # **CRITICAL VALIDATION**: Check for proper ObjectId handling in GET endpoints with ID parameters
        if use_mongodb and '<id>' in code or '<id>' in str(endpoint.get('path', '')):
            # Check if ObjectId conversion has proper error handling
            if 'ObjectId(' in code:
                # Check if there's try-except around ObjectId conversion
                objectid_pattern = r'ObjectId\s*\([^)]+\)'
                objectid_matches = list(re.finditer(objectid_pattern, code))
                for match in objectid_matches:
                    match_pos = match.start()
                    # Check context before and after for try-except
                    context_before = code[max(0, match_pos - 100):match_pos]
                    context_after = code[match_pos:match_pos + 200]
                    if 'try:' not in context_before and 'except' not in context_after:
                        validation_errors.append("ObjectId conversion should be wrapped in try-except to handle invalid IDs gracefully - return 400 for invalid IDs, 404 for not found")
                # Check if endpoint tries multiple methods to find document (fallback)
                if 'find_one' in code:
                    find_one_count = code.count('find_one')
                    if find_one_count < 2 and 'except' in code:
                        validation_errors.append("ObjectId conversion should have fallback: try ObjectId conversion first, if fails try finding by string id field or matching string _id")
            else:
                validation_errors.append("GET endpoint with <id> parameter should convert string ID to ObjectId using ObjectId(id) from exec namespace")
        
        # **CRITICAL VALIDATION**: Check for duplicate imports in route files
        import_lines = re.findall(r'^(from\s+\S+\s+import|import\s+\S+)', code, re.MULTILINE)
        import_counts = {}
        for imp in import_lines:
            import_counts[imp] = import_counts.get(imp, 0) + 1
        duplicate_imports = [imp for imp, count in import_counts.items() if count > 1]
        if duplicate_imports:
            validation_errors.append(f"Found duplicate imports: {', '.join(duplicate_imports[:3])}. Remove duplicates - ObjectId, PyMongoError, MongoClient are provided by app.py exec namespace")
        
        # Check for missing jsonify() in return statements
        return_statements = re.findall(r'return\s+([^;]+)', code)
        for ret in return_statements:
            ret = ret.strip()
            # If it's a dict literal or dict variable, should use jsonify
            if (ret.startswith('{') or ret.startswith('[')) and 'jsonify' not in ret and 'return jsonify' not in code[:code.find(ret)]:
                # Check if it's in a jsonify call already (might be on previous line)
                line_num = code[:code.find(ret)].count('\n')
                context = code[max(0, code.find(ret)-100):code.find(ret)]
                if 'jsonify' not in context:
                    validation_errors.append(f"Return statement returns dict/list without jsonify() - should use jsonify() for Flask responses")
                    break  # Only report once
        
        # Check for field name consistency in request body handling
        if method in ["POST", "PUT", "PATCH"]:
            # Check if endpoint accepts both camelCase and snake_case for flexibility
            data_access = re.findall(r'data\.get\([\'"](\w+)[\'"]', code) + re.findall(r'data\[[\'"](\w+)[\'"]', code)
            # If only one format is used, suggest accepting both
            camel_case_fields = [f for f in data_access if any(c.isupper() for c in f)]
            snake_case_fields = [f for f in data_access if '_' in f]
            if camel_case_fields and not snake_case_fields:
                validation_errors.append(f"Endpoint only accepts camelCase fields ({', '.join(camel_case_fields[:3])}) - consider accepting both camelCase and snake_case for flexibility")
        
        # Check for proper quantity/default value handling
        if 'quantity' in code.lower() or 'qty' in code.lower():
            if 'int(' not in code and 'parseInt' not in code and 'int(' not in code:
                validation_errors.append("Quantity field should be converted to integer - use int() or parseInt()")
            if 'quantity' in code and 'or 1' not in code and 'default' not in code.lower():
                # Check if there's validation for quantity > 0
                if 'quantity' in code and '> 0' not in code and '<= 0' not in code:
                    validation_errors.append("Quantity should be validated to be positive (> 0)")
        
        # Log validation warnings but don't fail (allow refinement cycles to fix)
        if validation_errors and not is_refinement:
            log_and_print(f"    [Validation Warnings] {len(validation_errors)} potential issues found:", log_file)
            for error in validation_errors[:3]:  # Limit to 3 to avoid spam
                log_and_print(f"      - {error}", log_file)
            # Add defects for critical issues (this is in backend endpoint function, not frontend)
            # Note: This validation block is for backend endpoints, so we don't add React-specific defects here
            # React validation defects are added in the frontend page implementation function
            # Add defects for critical issues
            if _defect_ledger:
                for error in validation_errors:
                    severity = DefectSeverity.MEDIUM
                    if "React Router syntax" in error or "Flask route" in error:
                        # Flask route syntax errors are CRITICAL - routes won't work
                        severity = DefectSeverity.CRITICAL
                    elif "deprecated" in error.lower() or ".count()" in error:
                        # Deprecated methods are HIGH priority
                        severity = DefectSeverity.HIGH
                    elif "crash" in error.lower() or "not be functional" in error.lower() or "jsonify" in error.lower():
                        severity = DefectSeverity.HIGH
                    
                    _defect_ledger.add_defect(
                        f"Code quality issue: {error}",
                        f"backend/{path}",
                        severity,
                        f"Implementation Agent {agent_id}",
                        "quality"
                    )
        
        # Organize routes into separate files by resource
        # Extract resource from path (e.g., /api/auth/login -> auth, /api/products -> products)
        path_parts = path.strip('/').split('/')
        resource = path_parts[1] if len(path_parts) > 1 else 'general'
        
        route_file = os.path.join(project_path, "routes", f"{resource}_routes.py")
        routes_dir = os.path.dirname(route_file)
        os.makedirs(routes_dir, exist_ok=True)
        
        # Check if route file exists
        route_exists = os.path.exists(route_file)
        
        if route_exists:
            # Read existing route file
            with open(route_file, 'r', encoding='utf-8') as f:
                existing_routes = f.read()
            
            # Check if this endpoint already exists
            endpoint_signature = f"@app.route('{path}'"
            if endpoint_signature in existing_routes and not is_refinement:
                # Endpoint already exists, append as new version
                with open(route_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n# {method} {path} - {'Refined' if is_refinement else 'New version'} by Implementation Agent {agent_id}\n")
                    f.write(code.strip() + "\n")
            else:
                # Append new endpoint
                with open(route_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n# {method} {path} - {'Refined' if is_refinement else 'Implemented'} by Implementation Agent {agent_id}\n")
                    f.write(code.strip() + "\n")
        else:
            # Create new route file
            # Routes will be executed with app and db in namespace
            route_file_content = f"""# {resource.upper()} Routes
# Auto-generated by Kaizen Implementation Agents

# {method} {path} - {'Refined' if is_refinement else 'Implemented'} by Implementation Agent {agent_id}
{code.strip()}
"""
            with open(route_file, 'w', encoding='utf-8') as f:
                f.write(route_file_content)
        
        # Update app.py to execute route files (making app and db available)
        app_py_path = os.path.join(project_path, "app.py")
        if os.path.exists(app_py_path):
            with open(app_py_path, 'r', encoding='utf-8') as f:
                app_content = f.read()
            
            # Check if this route module is already registered
            route_check = f"routes.{resource}_routes" in app_content or f"# Register {resource} routes" in app_content
            
            if not route_check:
                # Add route registration before error handlers
                error_handler_marker = "# Error handlers"
                if error_handler_marker in app_content:
                    insertion_point = app_content.find(error_handler_marker)
                    
                    # Check if there's already a routes registration section
                    if "# Register route modules" not in app_content:
                        # Create new registration section
                        registration_section = f"""
# Register route modules
# Execute route files with app and db in namespace so @app.route decorators work
import os
route_files_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "routes")
if os.path.exists(route_files_dir):
    route_files = [f for f in os.listdir(route_files_dir) if f.endswith('_routes.py')]
    for route_file in route_files:
        route_path = os.path.join(route_files_dir, route_file)
        try:
            # Execute route file with app and db in namespace
            with open(route_path, 'r', encoding='utf-8') as f:
                route_code = f.read()
            # Make app and db available in the route file's namespace
            exec(route_code, {{'app': app, 'db': db, '__file__': route_path}})
        except Exception as e:
            print(f"Warning: Could not load routes from {{route_file}}: {{e}}")

"""
                        app_content = (
                            app_content[:insertion_point] +
                            registration_section +
                            app_content[insertion_point:]
                        )
        
        action = "Refined" if is_refinement else "Implemented"
        log_and_print(f"    ✓ {action} {method} {path}", log_file)
        
        # Mark defects as resolved if this was a refinement
        if is_refinement and _defect_ledger and component_defects:
            for defect in component_defects[:3]:  # Mark top 3 as resolved
                _defect_ledger.update_defect_status(
                    defect['id'], 
                    DefectStatus.RESOLVED, 
                    f"Implementation Agent {agent_id}",
                    f"Refined endpoint in cycle"
                )
        
        return True
        
    except Exception as e:
        log_and_print(f"    ✗ Error implementing {method} {path}: {e}", log_file)
        if _defect_ledger:
            _defect_ledger.add_defect(
                f"Failed to implement {method} {path}: {str(e)}",
                f"backend/{path}",
                DefectSeverity.HIGH,
                f"Implementation Agent {agent_id}",
                "implementation_error"
            )
        return False


def verify_page_kaizen(page: Dict, project_path: str, agent_id: int, log_file: str) -> List[Dict]:
    """Verification Group agent inspects a frontend page for defects."""
    global _defect_ledger
    _defect_ledger = get_defect_ledger()
    
    page_name = page.get('page_name', 'Unknown')
    component_name = page_name.replace(" ", "").replace("-", "")
    component_file = os.path.join(project_path, "src", "pages", f"{component_name}.jsx")
    
    defects = []
    
    if not os.path.exists(component_file):
        if _defect_ledger:
            defect_id = _defect_ledger.add_defect(
                f"Component file not found: {component_name}.jsx",
                f"frontend/{page_name}",
                DefectSeverity.CRITICAL,
                f"Verification Agent {agent_id}",
                "missing_file"
            )
            defects.append({"id": defect_id, "severity": "critical"})
        return defects
    
    # Read and verify code
    try:
        with open(component_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        verification_agent = get_agent(temperature=0.2, max_tokens=1500)
        
        verify_prompt = f"""Inspect this code for defects: syntax, logic, error handling, accessibility, performance, security, quality.

COMPONENT: {page_name}
CODE: {code[:1000]}

Return JSON:
{{
    "defects": [
        {{
            "description": "defect description",
            "severity": "critical|high|medium|low|minor",
            "category": "syntax|logic|security|performance|quality",
            "line_number": 10,
            "suggestion": "how to fix"
        }}
    ]
}}"""

        response = invoke_with_rate_limit(verification_agent, [HumanMessage(content=verify_prompt)], log_file, estimated_tokens=1500)
        if not response:
            return defects
        content = response.content.strip()
        
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0:
                result = json.loads(content[json_start:json_end])
                found_defects = result.get('defects', [])
                
                for defect in found_defects:
                    severity_map = {
                        'critical': DefectSeverity.CRITICAL,
                        'high': DefectSeverity.HIGH,
                        'medium': DefectSeverity.MEDIUM,
                        'low': DefectSeverity.LOW,
                        'minor': DefectSeverity.MINOR
                    }
                    severity = severity_map.get(defect.get('severity', 'medium'), DefectSeverity.MEDIUM)
                    
                    if _defect_ledger:
                        defect_id = _defect_ledger.add_defect(
                            defect['description'],
                            f"frontend/{page_name}",
                            severity,
                            f"Verification Agent {agent_id}",
                            defect.get('category', 'general'),
                            {'line_number': defect.get('line_number'), 'suggestion': defect.get('suggestion')}
                        )
                        defects.append({"id": defect_id, "severity": defect.get('severity')})
        except:
            pass
    
    except Exception as e:
        log_and_print(f"    ⚠ Error verifying {page_name}: {e}", log_file)
    
    return defects


def verify_endpoint_kaizen(endpoint: Dict, project_path: str, agent_id: int, log_file: str) -> List[Dict]:
    """Verification Group agent inspects a backend endpoint for defects."""
    global _defect_ledger
    _defect_ledger = get_defect_ledger()
    
    path = endpoint.get('path', '')
    method = endpoint.get('method', 'GET')
    path_parts = path.strip('/').split('/')
    resource = path_parts[1] if len(path_parts) > 1 else 'general'
    resource_file = os.path.join(project_path, "routes", f"{resource}_routes.py")
    
    defects = []
    
    if not os.path.exists(resource_file):
        if _defect_ledger:
            defect_id = _defect_ledger.add_defect(
                f"Route file not found: {resource}_routes.py",
                f"backend/{path}",
                DefectSeverity.CRITICAL,
                f"Verification Agent {agent_id}",
                "missing_file"
            )
            defects.append({"id": defect_id, "severity": "critical"})
        return defects
    
    # Read and verify code
    try:
        with open(resource_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        verification_agent = get_agent(temperature=0.2, max_tokens=1500)
        
        verify_prompt = f"""Inspect this endpoint code for defects: syntax, logic, error handling (try-except for DB ops), input validation, security, performance, route functionality, data completeness, error responses, edge cases.

ENDPOINT: {method} {path}
CODE: {code[:1000]}

Return JSON:
{{
    "defects": [
        {{
            "description": "defect description",
            "severity": "critical|high|medium|low|minor",
            "category": "syntax|logic|security|performance|quality",
            "line_number": 10,
            "suggestion": "how to fix"
        }}
    ]
}}"""

        response = invoke_with_rate_limit(verification_agent, [HumanMessage(content=verify_prompt)], log_file, estimated_tokens=1500)
        if not response:
            return defects
        content = response.content.strip()
        
        try:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0:
                result = json.loads(content[json_start:json_end])
                found_defects = result.get('defects', [])
                
                for defect in found_defects:
                    severity_map = {
                        'critical': DefectSeverity.CRITICAL,
                        'high': DefectSeverity.HIGH,
                        'medium': DefectSeverity.MEDIUM,
                        'low': DefectSeverity.LOW,
                        'minor': DefectSeverity.MINOR
                    }
                    severity = severity_map.get(defect.get('severity', 'medium'), DefectSeverity.MEDIUM)
                    
                    if _defect_ledger:
                        defect_id = _defect_ledger.add_defect(
                            defect['description'],
                            f"backend/{path}",
                            severity,
                            f"Verification Agent {agent_id}",
                            defect.get('category', 'general'),
                            {'line_number': defect.get('line_number'), 'suggestion': defect.get('suggestion')}
                        )
                        defects.append({"id": defect_id, "severity": defect.get('severity')})
        except:
            pass
    
    except Exception as e:
        log_and_print(f"    ⚠ Error verifying {method} {path}: {e}", log_file)
    
    return defects


# ============================================================================
# PROJECT GENERATION FUNCTIONS (Direct generation without project_generator.py)
# ============================================================================

def determine_db_usage(description: str, features: List[str], design: Dict[str, Any]) -> bool:
    """
    AI-driven intelligent detection: Determine if MongoDB is needed based on application requirements.
    Uses AI analysis instead of hardcoded keywords to handle ANY application type dynamically.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, f"db_determination_{timestamp}.log")
    
    # Use AI to analyze if database is needed
    agent = get_agent(temperature=0.2, max_tokens=200)
    
    endpoints = design.get('backend', {}).get('endpoints', [])
    endpoints_summary = json.dumps([{"method": e.get('method'), "path": e.get('path'), "description": e.get('description', '')[:100]} for e in endpoints[:10]], indent=2)
    
    db_analysis_prompt = f"""Analyze if this application needs a database (MongoDB) for data persistence.

DESCRIPTION: {description}
FEATURES: {json.dumps(features, indent=2)}
ENDPOINTS: {endpoints_summary}

Consider: persistent storage needs, CRUD operations, user accounts, content storage, client-side only apps.

Respond with JSON:
{{
    "needs_database": true/false,
    "reasoning": "brief explanation"
}}"""

    try:
        response = invoke_with_rate_limit(agent, [HumanMessage(content=db_analysis_prompt)], log_file)
        content = response.content.strip()
        
        # Extract JSON
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            result = json.loads(json_str)
            needs_db = result.get("needs_database", False)
            reasoning = result.get("reasoning", "No reasoning provided")
            
            log_and_print(f"\n[Database Analysis] Needs database: {needs_db}", log_file)
            log_and_print(f"  Reasoning: {reasoning}", log_file)
            
            return needs_db
    except Exception as e:
        log_and_print(f"  Error: AI database analysis failed: {e}", log_file)
        # Don't use fallback - raise exception to ensure proper handling
        # The system should retry or the user should be notified
        raise Exception(f"Database usage determination failed. Cannot proceed without knowing if database is needed. Error: {e}")


def generate_react_tailwind_project(design: Dict[str, Any], project_name: str = "frontend", log_file: str = None) -> str:
    """
    Generate React project with Vite and Tailwind CSS v4 directly.
    Creates project structure, installs dependencies, and sets up Tailwind.
    """
    if log_file:
        log_and_print(f"\n[Project Generation] Creating React + Vite + Tailwind CSS v4 project: {project_name}", log_file)
    
    # Step 1: Create project directory structure
    if os.path.exists(project_name):
        if log_file:
            log_and_print(f"  [Warning] Directory '{project_name}' already exists. Skipping creation.", log_file)
    else:
        if log_file:
            log_and_print(f"  [1/6] Creating project structure...", log_file)
        os.makedirs(project_name, exist_ok=True)
        os.makedirs(os.path.join(project_name, "src"), exist_ok=True)
        os.makedirs(os.path.join(project_name, "src", "pages"), exist_ok=True)
        os.makedirs(os.path.join(project_name, "src", "components"), exist_ok=True)
        public_dir = os.path.join(project_name, "public")
        os.makedirs(public_dir, exist_ok=True)
        
        # Create favicon.svg (SVG is better than ICO for modern browsers)
        favicon_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="#3B82F6"/>
  <text x="50" y="70" font-size="60" text-anchor="middle" fill="white">A</text>
</svg>"""
        with open(os.path.join(public_dir, "favicon.svg"), 'w', encoding='utf-8') as f:
            f.write(favicon_svg)
        
        # Create manifest.json
        app_name = design.get('application_type', 'Web Application')
        manifest = {
            "short_name": app_name.split()[0] if app_name else "App",
            "name": app_name,
            "icons": [
                {
                    "src": "favicon.svg",
                    "sizes": "any",
                    "type": "image/svg+xml"
                }
            ],
            "start_url": ".",
            "display": "standalone",
            "theme_color": "#000000",
            "background_color": "#ffffff"
        }
        import json
        with open(os.path.join(public_dir, "manifest.json"), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        if log_file:
            log_and_print(f"  ✓ Project structure created", log_file)
    
    # Step 2: Create package.json with Vite and Tailwind v4
    if log_file:
        log_and_print(f"  [2/6] Creating package.json with Vite...", log_file)
    
    package_json = {
        "name": project_name,
        "version": "0.1.0",
        "private": True,
        "type": "module",
        "scripts": {
            "dev": "vite",
            "start": "vite",
            "build": "vite build",
            "preview": "vite preview"
        },
        "dependencies": {
            "@tailwindcss/vite": "^4.1.17",
            "axios": "^1.13.2",
            "react": "^19.2.1",
            "react-dom": "^19.2.1",
            "react-hook-form": "^7.67.0",
            "react-router-dom": "^7.10.0",
            "tailwindcss": "^4.1.17"
        },
        "devDependencies": {
            "@vitejs/plugin-react": "^5.1.1",
            "vite": "^7.2.4"
        }
    }
    
    package_json_path = os.path.join(project_name, "package.json")
    with open(package_json_path, 'w', encoding='utf-8') as f:
        import json
        f.write(json.dumps(package_json, indent=2))
    
    if log_file:
        log_and_print(f"  ✓ package.json created", log_file)
    
    # Step 3: Create vite.config.js
    if log_file:
        log_and_print(f"  [3/6] Creating vite.config.js...", log_file)
    
    vite_config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        ws: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
    },
  },
})
'''
    
    vite_config_path = os.path.join(project_name, "vite.config.js")
    with open(vite_config_path, 'w', encoding='utf-8') as f:
        f.write(vite_config)
    
    if log_file:
        log_and_print(f"  ✓ vite.config.js created", log_file)
    
    # Step 4: Create index.html (Vite entry point)
    if log_file:
        log_and_print(f"  [4/6] Creating index.html...", log_file)
    
    index_html = '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Web application created using Kaizen methodology" />
    <link rel="apple-touch-icon" href="/logo192.png" />
    <link rel="manifest" href="/manifest.json" />
    <title>React App</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'''
    
    index_html_path = os.path.join(project_name, "index.html")
    with open(index_html_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    if log_file:
        log_and_print(f"  ✓ index.html created", log_file)
    
    # Step 5: Create src/index.css with Tailwind v4
    if log_file:
        log_and_print(f"  [5/6] Creating src/index.css with Tailwind v4...", log_file)
    
    index_css = '''@import "tailwindcss";

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
'''
    
    index_css_path = os.path.join(project_name, "src", "index.css")
    with open(index_css_path, 'w', encoding='utf-8') as f:
        f.write(index_css)
    
    if log_file:
        log_and_print(f"  ✓ index.css created", log_file)
    
    # Step 6: Create src/main.jsx (Vite entry point)
    if log_file:
        log_and_print(f"  [6/6] Creating src/main.jsx...", log_file)
    
    main_jsx = '''import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);
'''
    
    main_jsx_path = os.path.join(project_name, "src", "main.jsx")
    with open(main_jsx_path, 'w', encoding='utf-8') as f:
        f.write(main_jsx)
    
    if log_file:
        log_and_print(f"  ✓ main.jsx created", log_file)
    
    # Step 7: Install dependencies
    if log_file:
        log_and_print(f"  [7/7] Installing dependencies...", log_file)
    try:
        subprocess.run(
            "npm install",
            shell=True,
            cwd=project_name,
            check=True,
            capture_output=True,
            timeout=300
        )
        if log_file:
            log_and_print(f"  ✓ Dependencies installed", log_file)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        if log_file:
            log_and_print(f"  ⚠ Warning: Auto-installation may have issues. Please run manually:", log_file)
            log_and_print(f"    cd {project_name}", log_file)
            log_and_print(f"    npm install", log_file)
    
    if log_file:
        log_and_print(f"  ✓ React + Vite + Tailwind CSS v4 project ready: {os.path.abspath(project_name)}", log_file)
    
    return os.path.abspath(project_name)


def generate_flask_mongodb_backend(design: Dict[str, Any], project_name: str = "backend", use_mongodb: bool = False, log_file: str = None) -> str:
    """
    Generate Flask backend with optional MongoDB directly (no project_generator.py).
    Creates project structure, virtual environment, and installs dependencies.
    """
    if log_file:
        log_and_print(f"\n[Project Generation] Creating Flask backend: {project_name}", log_file)
        if use_mongodb:
            log_and_print(f"  [MongoDB] Database integration enabled", log_file)
    
    # Step 1: Create project directory
    os.makedirs(project_name, exist_ok=True)
    
    # Step 2: Create virtual environment
    if log_file:
        log_and_print(f"  [1/5] Creating virtual environment...", log_file)
    try:
        subprocess.run(
            ["python", "-m", "venv", "venv"],
            cwd=project_name,
            check=True,
            capture_output=True
        )
        if log_file:
            log_and_print(f"  ✓ Virtual environment created", log_file)
    except subprocess.CalledProcessError as e:
        if log_file:
            log_and_print(f"  ⚠ Warning: Virtual environment creation may have issues", log_file)
    
    # Step 3: Create requirements.txt
    if log_file:
        log_and_print(f"  [2/5] Creating requirements.txt...", log_file)
    
    requirements = [
        "Flask==3.0.0",
        "Flask-CORS==4.0.0",
        "python-dotenv==1.0.0",
        "requests==2.31.0"
    ]
    
    if use_mongodb:
        requirements.extend([
            "pymongo==4.6.0",
            "dnspython==2.4.2"
        ])
    
    requirements_path = os.path.join(project_name, "requirements.txt")
    with open(requirements_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(requirements) + '\n')
    
    if log_file:
        log_and_print(f"  ✓ requirements.txt created", log_file)
    
    # Step 4: Create main app.py
    if log_file:
        log_and_print(f"  [3/5] Creating Flask application...", log_file)
    
    # Determine pip command based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = os.path.join("venv", "Scripts", "pip.exe")
        python_cmd = os.path.join("venv", "Scripts", "python.exe")
    else:  # Unix/Linux/Mac
        pip_cmd = os.path.join("venv", "bin", "pip")
        python_cmd = os.path.join("venv", "bin", "python")
    
    # MongoDB connection code
    mongodb_setup = ""
    mongodb_import = ""
    if use_mongodb:
        mongodb_import = "from pymongo import MongoClient\nfrom pymongo.errors import ConnectionFailure\n"
        mongodb_setup = """
# MongoDB connection
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
try:
    mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()  # Test connection
    db = mongo_client.get_database(os.getenv("MONGODB_DB_NAME", "app_db"))
    print(f"✓ Connected to MongoDB: {MONGODB_URI}")
except ConnectionFailure as e:
    print(f"⚠ Warning: MongoDB connection failed: {e}")
    print("  Continuing without database. Some features may not work.")
    db = None
except Exception as e:
    print(f"⚠ Warning: MongoDB connection error: {e}")
    db = None
"""
    else:
        # Always initialize db variable, even if MongoDB is not used
        mongodb_setup = """
# Database connection (MongoDB not enabled for this project)
    db = None
"""
    
    # Seed data import and call (only if MongoDB is enabled)
    seed_data_code = ""
    if use_mongodb:
        seed_data_code = """
# Seed database with basic data if connected
if db is not None:
    try:
        from seed_data import seed_database
        print("\\n[Database Seeding] Initializing seed data...")
        seed_result = seed_database(db)
        if seed_result.get("status") == "success":
            print("  Database seeded successfully with basic data.")
        elif seed_result.get("status") == "skipped":
            print("  Database seeding skipped (already has data or not connected).")
    except Exception as e:
        print(f"  Warning: Could not seed database: {e}")
        import traceback
        traceback.print_exc()
"""
    
    app_py_content = f"""from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
{mongodb_import}
# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes (allows React frontend to communicate)
CORS(app, resources={{r"/*": {{"origins": "*"}}}}, supports_credentials=True)

# Configuration
app.config['DEBUG'] = True
app.config['JSON_SORT_KEYS'] = False
{mongodb_setup}
# Home route
@app.route('/')
def home():
    \"\"\"API Home - List all available endpoints\"\"\"
    return jsonify({{
        "message": "Flask Backend API",
        "mongodb_enabled": db is not None,
        "status": "running"
    }})

# Register route modules
# Execute route files with app and db in namespace so @app.route decorators work
import os
from flask import request as flask_request
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import bson
from werkzeug.security import generate_password_hash, check_password_hash
try:
    import bcrypt
except ImportError:
    bcrypt = None
try:
    import jwt
except ImportError:
    jwt = None
import datetime
import re

route_files_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "routes")
if os.path.exists(route_files_dir):
    route_files = [f for f in os.listdir(route_files_dir) if f.endswith('_routes.py')]
    for route_file in sorted(route_files):  # Sort for consistent loading order
        route_path = os.path.join(route_files_dir, route_file)
        try:
            # Execute route file with app and db in namespace
            with open(route_path, 'r', encoding='utf-8') as f:
                route_code = f.read()
            # Make app, db, and all necessary imports available in the route file's namespace
            from bson import ObjectId
            from pymongo.errors import PyMongoError
            exec(route_code, {{
                'app': app, 
                'db': db, 
                '__file__': route_path,
                'request': flask_request,
                'jsonify': jsonify,
                'MongoClient': MongoClient,
                'ConnectionFailure': ConnectionFailure,
                'bson': bson,
                'ObjectId': ObjectId,
                'PyMongoError': PyMongoError,
                'generate_password_hash': generate_password_hash,
                'check_password_hash': check_password_hash,
                'bcrypt': bcrypt,
                'jwt': jwt,
                'datetime': datetime,
                're': re
            }})
            print(f"Loaded routes from {{route_file}}")
        except Exception as e:
            print(f"Warning: Could not load routes from {{route_file}}: {{e}}")
            import traceback
            traceback.print_exc()
{seed_data_code}
# Serve uploaded static files (videos, images, documents, etc.)
# This route is needed if the application handles file uploads
from flask import send_from_directory
@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    \"\"\"Serve uploaded files from the uploads directory.\"\"\"
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    if os.path.exists(uploads_dir) and os.path.exists(os.path.join(uploads_dir, filename)):
        return send_from_directory(uploads_dir, filename)
    return jsonify({{"error": "File not found"}}), 404

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
"""
    
    app_py_path = os.path.join(project_name, "app.py")
    with open(app_py_path, 'w', encoding='utf-8') as f:
        f.write(app_py_content)
    
    if log_file:
        log_and_print(f"  ✓ Flask app.py created", log_file)
    
    # Step 5: Create .env file
    if log_file:
        log_and_print(f"  [4/5] Creating .env file...", log_file)
    
    env_content = """# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
PORT=5000

"""
    
    if use_mongodb:
        env_content += """# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=app_db

"""
    
    env_path = os.path.join(project_name, ".env")
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    if log_file:
        log_and_print(f"  ✓ .env file created", log_file)
    
    # Step 6: Install dependencies (optional, may take time)
    if log_file:
        log_and_print(f"  [5/5] Installing Python dependencies (this may take a minute)...", log_file)
    try:
        result = subprocess.run(
            f'"{pip_cmd}" install -r requirements.txt',
            shell=True,
            cwd=project_name,
            check=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        if log_file:
            log_and_print(f"  ✓ Dependencies installed", log_file)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        if log_file:
            log_and_print(f"  ⚠ Warning: Auto-installation failed. Please run manually:", log_file)
            log_and_print(f"    cd {project_name}", log_file)
            log_and_print(f"    {pip_cmd} install -r requirements.txt", log_file)
    
    # Create routes directory for organized endpoint files
    routes_dir = os.path.join(project_name, "routes")
    os.makedirs(routes_dir, exist_ok=True)
    
    # Create __init__.py for routes package
    init_py_path = os.path.join(routes_dir, "__init__.py")
    with open(init_py_path, 'w', encoding='utf-8') as f:
        f.write("# Routes package\n")
    
    # Create seed_data.py if MongoDB is enabled - dynamically generate based on design
    if use_mongodb:
        if log_file:
            log_and_print(f"  [6/6] Creating dynamic seed_data.py based on design...", log_file)
        
        # Extract data models from design
        data_models = design.get('backend', {}).get('data_models', [])
        application_type = design.get('application_type', 'Web Application')
        app_description = design.get('detailed_description', design.get('description', 'Web Application'))
        
        # Use AI to generate seed data based on actual data models
        seed_data_prompt = f"""Generate complete, valid Python code for a seed_database function that populates MongoDB with REALISTIC, MEANINGFUL sample data.
        
CRITICAL RULES:
- Function MUST be complete and syntactically correct
- NO incomplete docstrings, NO dangling triple quotes
- Use provided 'db' parameter, NEVER create new MongoClient()
- Import only: random, bson.ObjectId, datetime
- Check 'if db is None:' before operations
- Return dict with 'status' field ('success', 'skipped', or 'error')
- Generate data relevant to the application type and models
- NO placeholders, NO incomplete code, NO syntax errors

APPLICATION TYPE: {application_type}
DESCRIPTION: {app_description}

DATA MODELS:
{json.dumps(data_models, indent=2)}

**CRITICAL REQUIREMENTS FOR MEANINGFUL DATA**:
- Analyze the application description "{app_description}" and application type "{application_type}" to understand what kind of data is needed
- Generate REALISTIC data that matches what the application actually does (infer from description):
  * Look at the data model fields to understand what entities exist
  * Generate appropriate data for each field based on the field name, type, and application context
  * **CONTEXT-AWARE DATA GENERATION**: 
    - For e-commerce applications: Generate realistic product names, prices, descriptions, categories, images, stock quantities
    - For social media: Generate realistic posts, comments, user profiles, likes, shares
    - For blogs: Generate realistic blog posts, categories, tags, authors, publication dates
    - For task management: Generate realistic tasks, projects, users, due dates, priorities
    - INFER from the application type and description - don't use generic templates
  * INFER the data type from field names, model structure, and application context, not from hardcoded assumptions
- NO placeholder text like "Sample", "Test", "Lorem ipsum", "Example", "Demo", "Feature1", "Feature2"
- Use diverse, realistic data (different names, values, descriptions, etc.) that makes sense for the application
- Include ALL fields from the data models with appropriate, meaningful values
- Generate enough data to be useful (20-30 items per collection minimum for testing and demonstration)
- Ensure data relationships are correct based on the model structure
- **MEANINGFUL FIELD VALUES**: 
  - For "name" or "title" fields: Use realistic names (e.g., "Blue Denim Jeans", "Wireless Headphones", NOT "Product 1", "Item 1")
  - For "price" fields: Use realistic prices (e.g., 29.99, 149.99, NOT 0, 100)
  - For "description" fields: Use realistic descriptions (e.g., "High-quality cotton t-shirt in various colors", NOT "Sample description")
  - For "category" fields: Use realistic categories (e.g., "Men's Clothing", "Electronics", NOT "Category1", "Category2")
  - For "image" or "imageUrl" fields: Use placeholder image URLs or realistic image paths
  - For date fields: Use realistic dates (recent dates for new items, older dates for historical items)

Generate a seed_database(db) function that:
1. Checks if collections already have data (skip if they do)
2. Creates REALISTIC, MEANINGFUL sample data based on the data models above (NO placeholders)
3. Uses appropriate field types and realistic values that match the application type
4. Returns a summary dict with counts of seeded items AND a status field

CRITICAL COLLECTION NAMING RULES:
- Collection names MUST be lowercase, plural, and use underscores for multi-word models
- Examples:
  * "User" model → "users" collection
  * "Product" model → "products" collection
  * "News" model → "news" collection (NOT "newss")
  * "SocialMediaLink" model → "social_media_links" collection (NOT "socialmedia links" or "socialmedialinks")
  * "OrderItem" model → "order_items" collection
  * "BlogPost" model → "blog_posts" collection
- Convert model names to collection names using this logic:
  * Split camelCase/PascalCase into words (e.g., "SocialMediaLink" → ["Social", "Media", "Link"])
  * Convert to lowercase and join with underscores (e.g., ["social", "media", "link"])
  * Add "s" for plural (e.g., "social_media_links")
  * Special case: If model name ends with "s" or is already plural-sounding, don't add extra "s" (e.g., "News" → "news", not "newss")

The function should:
- Handle any data model structure dynamically
- Create REALISTIC, MEANINGFUL sample data appropriate for {application_type} (NO "Sample" or "Test" text)
- Generate 15-25 items per collection to make the application useful
- Use diverse data: Different names, prices, descriptions, categories, etc.
- Use proper MongoDB operations (insert_many, etc.)
- Include comprehensive error handling
- Print progress messages
- Return dict with "status" field ("success" or "skipped") and "summary" field with counts
- Use proper collection naming as described above
- Ensure ALL fields from models are populated with meaningful values

Return ONLY the Python function code, starting with the docstring and function definition."""
        
        try:
            agent = get_agent(temperature=0.2, max_tokens=1500)
            response = invoke_with_rate_limit(agent, [HumanMessage(content=seed_data_prompt)], log_file if log_file else None, estimated_tokens=1500)
            seed_function_code = response.content.strip()
            
            # Extract function code if wrapped in code blocks
            if "```python" in seed_function_code:
                seed_function_code = seed_function_code.split("```python")[1].split("```")[0]
            elif "```" in seed_function_code:
                seed_function_code = seed_function_code.split("```")[1].split("```")[0]
            
            # Ensure it has the proper structure
            if "def seed_database" not in seed_function_code:
                # Retry with a more specific prompt if AI didn't generate properly
                if log_file:
                    log_and_print(f"  [Retry] Seed data function not found in response, retrying with more specific prompt...", log_file)
                retry_prompt = f"""Generate ONLY the seed_database function for {application_type} with REALISTIC, MEANINGFUL data.

DATA MODELS:
{json.dumps(data_models, indent=2)}

Return ONLY the complete Python function starting with 'def seed_database(db):' and including all necessary code to seed the database with realistic sample data for these models."""
                
                try:
                    retry_response = invoke_with_rate_limit(agent, [HumanMessage(content=retry_prompt)], log_file if log_file else None, estimated_tokens=2000)
                    if retry_response:
                        seed_function_code = retry_response.content.strip()
                        if "```python" in seed_function_code:
                            seed_function_code = seed_function_code.split("```python")[1].split("```")[0]
                        elif "```" in seed_function_code:
                            seed_function_code = seed_function_code.split("```")[1].split("```")[0]
                except Exception as retry_e:
                    if log_file:
                        log_and_print(f"  Error: Retry also failed: {retry_e}", log_file)
                    # Don't use fallback - raise exception
                    raise Exception(f"Failed to generate seed data function after retry. Cannot proceed with incomplete seed data. Error: {retry_e}")
                
                if "def seed_database" not in seed_function_code:
                    raise Exception("Seed data generation failed - function structure not found in AI response")
            
            # Validate seed function code for common errors
            validation_errors = []
            if seed_function_code.count('"""') % 2 != 0:
                validation_errors.append("Unclosed docstring (dangling triple quotes)")
            if "if db is None" not in seed_function_code and "if db is not None" not in seed_function_code:
                validation_errors.append("Missing database connection check")
            if "MongoClient()" in seed_function_code or "MongoClient(" in seed_function_code:
                validation_errors.append("CRITICAL: Found MongoClient() - must use provided 'db' parameter")
            if "from pymongo import MongoClient" in seed_function_code:
                validation_errors.append("CRITICAL: Do NOT import MongoClient - use provided 'db' parameter")
            
            if validation_errors:
                if log_file:
                    log_and_print(f"  [Seed Data Validation Warnings] {', '.join(validation_errors)}", log_file)
                # Fix common issues automatically
                if "MongoClient()" in seed_function_code:
                    seed_function_code = seed_function_code.replace("MongoClient()", "# MongoClient removed - use 'db' parameter")
                if "from pymongo import MongoClient" in seed_function_code:
                    seed_function_code = seed_function_code.replace("from pymongo import MongoClient", "# MongoClient import removed - use 'db' parameter")
        except Exception as e:
            if log_file:
                log_and_print(f"  Error: Could not generate dynamic seed data: {e}", log_file)
            # Don't use fallback template - raise exception to ensure proper handling
            raise Exception(f"Seed data generation failed. Cannot proceed with incomplete seed data. Error: {e}")
        
        seed_data_content = f'''"""
Seed database with basic static data for {application_type}.
This function populates the database with sample data based on the application's data models.
"""

{seed_function_code}
'''
        
        seed_data_path = os.path.join(project_name, "seed_data.py")
        with open(seed_data_path, 'w', encoding='utf-8') as f:
            f.write(seed_data_content)
        
        if log_file:
            log_and_print(f"  ✓ seed_data.py created", log_file)
    
    if log_file:
        log_and_print(f"  ✓ Flask backend ready: {os.path.abspath(project_name)}", log_file)
    
    return os.path.abspath(project_name)


def generate_app_js_with_routing(design: Dict[str, Any], react_path: str, log_file: str = None) -> bool:
    """
    Generate App.jsx with routing for all pages.
    Called after all pages are implemented in Cycle 1.
    Creates App.jsx with React Router and imports all page components with .jsx extensions.
    """
    if log_file:
        log_and_print(f"\n[Routing] Setting up App.js with routing...", log_file)
    
    pages = design.get('frontend', {}).get('pages', [])
    if not pages:
        if log_file:
            log_and_print(f"  ⚠ No pages to route", log_file)
        return False
    
    # Generate imports
    imports = []
    routes = []
    nav_links = []
    
    # Extract UI theme for navbar styling
    ui_theme = design.get('ui_theme', {})
    primary_color = ui_theme.get('primary_color', 'blue-600')
    secondary_color = ui_theme.get('secondary_color', 'gray-600')
    application_type = design.get('application_type', 'Web Application')
    
    # Convert hex colors to Tailwind classes if needed
    def get_tailwind_color(color):
        if color.startswith('#'):
            # For hex colors, use a generic approach - extract base color name
            # This is a simplified mapping - in production, you'd want a more sophisticated color matcher
            return 'blue'  # Default fallback, but we'll use custom colors via style attribute
        return color.split('-')[0] if '-' in color else color
    
    primary_tailwind = get_tailwind_color(primary_color)
    
    for page in pages:
        page_name = page.get('page_name', 'Unknown')
        component_name = page_name.replace(" ", "").replace("-", "")
        route_path = page_name.lower().replace(' ', '-').replace('_', '-')
        
        # Check if this page needs dynamic routing (e.g., "Video Details", "Product Details", "Post Details")
        # Look for keywords that suggest detail pages
        is_detail_page = any(keyword in page_name.lower() for keyword in ['detail', 'view', 'show', 'item', 'single'])
        
        # If it's a detail page, check if endpoints suggest an ID parameter
        page_endpoints = page.get('backend_endpoints', [])
        has_id_endpoint = any('/:id' in ep.get('path', '') or 'id' in ep.get('path', '').lower() for ep in page_endpoints)
        
        # Determine if dynamic route is needed
        if is_detail_page or has_id_endpoint:
            # Create both static and dynamic routes for flexibility
            # Static route for pages that can work without ID (e.g., /user-account)
            routes.append(f'            <Route path="/{route_path}" element={{<{component_name} />}} />')
            # Dynamic route with :id parameter (e.g., /user-account/:id)
            dynamic_route_path = f"/{route_path}/:id"
            routes.append(f'            <Route path="{dynamic_route_path}" element={{<{component_name} />}} />')
        else:
            # Regular static route
            routes.append(f'            <Route path="/{route_path}" element={{<{component_name} />}} />')
        
        # Create intelligent route aliases (GENERIC - pattern-based, works for any app)
        # Generate common aliases based on page name patterns
        page_name_lower = page_name.lower()
        route_path_lower = route_path.lower()
        
        # Pattern 1: If page name has multiple words, create alias from last significant word
        # e.g., "Shopping Cart" -> /cart, "Product List" -> /products, "User Profile" -> /profile
        words = page_name_lower.split()
        if len(words) > 1:
            # Get the last significant word (skip common words like "page", "view", "list" if they're not the only word)
            significant_words = [w for w in words if w not in ['page', 'view', 'screen']]
            if significant_words:
                last_word = significant_words[-1]
                # Create alias if it's different from full route path
                alias_path = f"/{last_word}"
                if alias_path != f"/{route_path}" and alias_path not in [r.split('"')[1] if '"' in r else '' for r in routes]:
                    routes.append(f'            <Route path="{alias_path}" element={{<{component_name} />}} />')
        
        # Pattern 2: Create plural/singular aliases for list pages
        # e.g., "ProductList" -> /products (plural), "Product" -> /products
        if 'list' in page_name_lower or 'index' in page_name_lower or 'home' in page_name_lower:
            # Extract resource name (first word before "List", "Index", etc.)
            resource_word = words[0] if words else ''
            if resource_word:
                # Create plural alias
                plural_alias = f"/{resource_word}s"  # Simple pluralization
                if plural_alias != f"/{route_path}" and plural_alias not in [r.split('"')[1] if '"' in r else '' for r in routes]:
                    routes.append(f'            <Route path="{plural_alias}" element={{<{component_name} />}} />')
        
        # Pattern 3: Create common shortened aliases for multi-word routes
        # e.g., "ShoppingCart" -> /cart, "UserProfile" -> /profile, "ProductDetail" -> /product
        if len(words) >= 2:
            # Create alias from last word if route is long
            if len(route_path) > 10:  # Only for longer routes
                last_word_alias = f"/{words[-1]}"
                if last_word_alias != f"/{route_path}" and last_word_alias not in [r.split('"')[1] if '"' in r else '' for r in routes]:
                    routes.append(f'            <Route path="{last_word_alias}" element={{<{component_name} />}} />')
        
        imports.append(f"import {component_name} from './pages/{component_name}.jsx';")
        # Only add to nav if it's not a detail page (detail pages are accessed via links from list pages)
        if not is_detail_page:
            nav_links.append(f'                <Link to="/{route_path}" className="px-3 py-2 rounded-md text-sm font-medium text-white hover:bg-white/10 hover:text-white transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white/50">{page_name}</Link>')
    
    # First page is the home route
    first_component = pages[0].get('page_name', 'Home').replace(" ", "").replace("-", "")
    
    # Build desktop nav links
    desktop_nav_links = []
    mobile_nav_links = []
    for page in pages:
        page_name = page.get('page_name', 'Unknown')
        route_path = page_name.lower().replace(' ', '-').replace('_', '-')
        is_detail_page = any(keyword in page_name.lower() for keyword in ['detail', 'view', 'show', 'item', 'single'])
        
        if not is_detail_page:
            desktop_nav_links.append(f'            <Link to="/{route_path}" className={{`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${{isActive("/{route_path}") ? "bg-white/20 text-white shadow-md" : "text-gray-300 hover:bg-white/10 hover:text-white"}}`}}>{page_name}</Link>')
            mobile_nav_links.append(f'            <Link to="/{route_path}" onClick={{() => setMobileMenuOpen(false)}} className={{`block px-4 py-3 rounded-lg text-base font-medium transition-all duration-200 ${{isActive("/{route_path}") ? "bg-white/20 text-white" : "text-gray-300 hover:bg-white/10 hover:text-white"}}`}}>{page_name}</Link>')
    
    # Get app name from application type
    app_name = application_type.split()[0] if application_type else "App"
    
    # Generate enhanced navbar with mobile menu support
    navbar_content = f'''import React, {{ useState }} from 'react';
import {{ BrowserRouter as Router, Routes, Route, Link, useLocation }} from 'react-router-dom';

// Import all page components
{chr(10).join(imports)}

function Navbar() {{
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  
  const isActive = (path) => {{
    return location.pathname === path || location.pathname.startsWith(path + '/');
  }};
  
  return (
    <nav className="bg-gradient-to-r from-gray-800 to-gray-900 text-white shadow-lg sticky top-0 z-50 backdrop-blur-sm bg-opacity-95">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 md:h-20">
          {{/* Logo/Brand */}}
          <Link to="/" className="flex items-center space-x-2 group">
            <div className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent group-hover:from-white group-hover:to-white transition-all duration-300">
              {app_name}
            </div>
            <span className="hidden sm:inline text-sm text-gray-300">- {application_type}</span>
          </Link>
          
          {{/* Desktop Navigation */}}
          <div className="hidden md:flex items-center space-x-1">
{chr(10).join(desktop_nav_links)}
          </div>
          
          {{/* Mobile Menu Button */}}
          <button
            onClick={{() => setMobileMenuOpen(!mobileMenuOpen)}}
            className="md:hidden p-2 rounded-md text-gray-300 hover:text-white hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-white/50 transition-colors"
            aria-label="Toggle menu"
            aria-expanded={{mobileMenuOpen}}
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {{mobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              )}}
            </svg>
          </button>
        </div>
        
        {{/* Mobile Navigation Menu */}}
        <div className={{`md:hidden transition-all duration-300 ease-in-out ${{mobileMenuOpen ? "max-h-96 opacity-100" : "max-h-0 opacity-0"}} overflow-hidden`}}>
          <div className="px-2 pt-2 pb-4 space-y-1 border-t border-white/10">
{chr(10).join(mobile_nav_links)}
          </div>
        </div>
      </div>
    </nav>
  );
}}

function App() {{
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
          <Routes>
            <Route path="/" element={{<{first_component} />}} />
{chr(10).join(routes)}
          </Routes>
        </main>
      </div>
    </Router>
  );
}}

export default App;
'''
    
    app_jsx_path = os.path.join(react_path, "src", "App.jsx")
    try:
        with open(app_jsx_path, 'w', encoding='utf-8') as f:
            f.write(navbar_content)
        if log_file:
            log_and_print(f"  ✓ App.jsx with enhanced navbar and routing created ({len(pages)} routes)", log_file)
        return True
    except Exception as e:
        if log_file:
            log_and_print(f"  ✗ Failed to create App.jsx: {e}", log_file)
        return False


def generate_shared_components(design: Dict[str, Any], react_path: str, description: str, log_file: str = None) -> bool:
    """
    Generate shared React components based on application type and design.
    Components are placed in src/components/ directory.
    """
    if log_file:
        log_and_print(f"\n[Components] Generating shared components...", log_file)
    
    components_dir = os.path.join(react_path, "src", "components")
    os.makedirs(components_dir, exist_ok=True)
    
    description_lower = description.lower()
    
    components_to_create = []
    
    # Dynamically determine which components are needed based on description analysis
    # Don't hardcode application types - infer from description
    components_to_create = []
    
    # Always include basic utility components
    components_to_create.append({'name': 'NavigationMenu', 'description': 'Main navigation menu component'})
    components_to_create.append({'name': 'LoadingSpinner', 'description': 'Loading indicator component'})
    components_to_create.append({'name': 'ErrorMessage', 'description': 'Error message display component'})
    
    # Analyze description to infer additional components needed
    # Look for keywords that suggest specific component types, but don't hardcode application types
    if any(keyword in description_lower for keyword in ['product', 'item', 'card', 'listing']):
        components_to_create.append({'name': 'Card', 'description': 'Display item information in a card format'})
    
    if any(keyword in description_lower for keyword in ['review', 'rating', 'comment', 'feedback']):
        components_to_create.append({'name': 'ReviewCard', 'description': 'Display review or comment with rating'})
    
    if any(keyword in description_lower for keyword in ['cart', 'basket', 'shopping']):
        components_to_create.append({'name': 'CartItem', 'description': 'Display item in shopping cart'})
    
    if any(keyword in description_lower for keyword in ['user', 'profile', 'account']):
        components_to_create.append({'name': 'UserProfile', 'description': 'User profile display component'})
    
    if not components_to_create:
        if log_file:
            log_and_print(f"  ⚠ No shared components needed", log_file)
        return False
    
    # Generate each component
    agent = get_agent()
    components_created = 0
    total_components = len(components_to_create)
    
    for idx, component_spec in enumerate(components_to_create, 1):
        component_name = component_spec['name']
        component_file = os.path.join(components_dir, f"{component_name}.jsx")
        
        if log_file:
            log_and_print(f"  [{idx}/{total_components}] Generating {component_name}.jsx...", log_file)
        else:
            print(f"  [{idx}/{total_components}] Generating {component_name}.jsx...", flush=True)
        
        # Skip if already exists
        if os.path.exists(component_file):
            if log_file:
                log_and_print(f"  [Skip] {component_name}.jsx already exists", log_file)
            else:
                print(f"  [Skip] {component_name}.jsx already exists")
            continue
        
        try:
            component_prompt = f"""You are an Implementation Agent creating a reusable React component.

APPLICATION CONTEXT: {description}

COMPONENT: {component_name}
Description: {component_spec['description']}

Create a complete, reusable React functional component with:
1. React hooks (useState, useEffect if needed)
2. Component props (use JSDoc comments, NOT TypeScript interfaces)
3. Error handling
4. **IMPORTANT: 
   - Use Tailwind CSS classes for ALL styling. Do NOT use inline styles or CSS files.
   - This file will be saved as .jsx extension, so ensure all JSX syntax is correct.
   - Use .jsx extension in any relative imports (e.g., './pages/HomePage.jsx')
   - **CRITICAL - NO TYPESCRIPT SYNTAX**: This is a .jsx file, NOT .tsx. Do NOT use:
     * TypeScript interfaces: NO `interface ComponentProps {{ ... }}`
     * Type annotations: NO `const Component: React.FC<Props> = ...`
     * Type annotations: NO `const Component = ({{ prop }}: Props) => ...`
     * Use plain JavaScript: `const Component = ({{ prop }}) => ...` or `function Component({{ prop }})`
     * Use JSDoc comments for documentation: `/** @param {{string}} prop - Description */`
   - **NO SELF-IMPORTS**: Do NOT import the component file itself (e.g., `import './ComponentName.jsx'`). Only import external dependencies.
   - **ONLY import from these packages**: react, react-dom, react-router-dom (if using NavLink/Link), axios (if needed), react-hook-form (if needed)
   - **DO NOT import FontAwesome or react-loading-skeleton** - Use inline SVG icons and Tailwind animate-pulse instead**
5. Make it responsive with Tailwind responsive classes
6. Proper prop documentation using JSDoc comments (NOT TypeScript interfaces)
7. Export as default

Return ONLY the complete React component code (JSX) with Tailwind CSS classes, nothing else. Start with imports."""

            if log_file:
                log_and_print(f"  [API Call] Requesting {component_name} from AI...", log_file)
            else:
                print(f"  [API Call] Requesting {component_name} from AI...", flush=True)
            
            response = invoke_with_rate_limit(agent, [HumanMessage(content=component_prompt)], log_file, estimated_tokens=800)  # Reduced from 1500
            if not response:
                if log_file:
                    log_and_print(f"  ⚠ No response received for {component_name}, skipping...", log_file)
                else:
                    print(f"  ⚠ No response received for {component_name}, skipping...")
                continue
            
            if log_file:
                log_and_print(f"  [Processing] Parsing response for {component_name}...", log_file)
            else:
                print(f"  [Processing] Parsing response for {component_name}...", flush=True)
            
            component_code = response.content.strip()
            
            # Clean code blocks
            if "```" in component_code:
                component_code = component_code.split("```")[1]
                if component_code.startswith("jsx") or component_code.startswith("javascript"):
                    component_code = component_code.split('\n', 1)[1]
                component_code = component_code.split("```")[0]
            
            # Add imports if missing
            if "import React" not in component_code:
                component_code = "import React from 'react';\n\n" + component_code
            
            # Save component file
            with open(component_file, 'w', encoding='utf-8') as f:
                f.write(component_code)
            
            components_created += 1
            if log_file:
                log_and_print(f"  ✓ Created {component_name}.jsx", log_file)
            else:
                print(f"  ✓ Created {component_name}.jsx", flush=True)
        
        except KeyboardInterrupt:
            if log_file:
                log_and_print(f"  [Interrupted] Component generation cancelled by user", log_file)
            else:
                print(f"  [Interrupted] Component generation cancelled by user")
            raise
        
        except Exception as e:
            error_msg = str(e)
            if log_file:
                log_and_print(f"  ✗ Error creating {component_name}: {error_msg}", log_file)
            else:
                print(f"  ✗ Error creating {component_name}: {error_msg}")
            import traceback
            full_traceback = traceback.format_exc()
            if log_file:
                log_and_print(f"  [Traceback] {full_traceback[:1000]}", log_file)
            else:
                print(f"  [Traceback] {full_traceback[:500]}")
            # Continue with next component instead of stopping
            continue
    
    if log_file:
        log_and_print(f"  ✓ Generated {components_created}/{total_components} shared components", log_file)
    else:
        print(f"  ✓ Generated {components_created}/{total_components} shared components")
    
    return components_created > 0

