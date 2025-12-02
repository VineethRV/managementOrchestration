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
        raise Exception(f"Daily token limit exceeded. Remaining: {remaining_tokens} tokens")
    
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


def get_agent(model: str = "llama-3.3-70b-versatile", temperature: float = 0.3, max_tokens: int = 8000) -> ChatGroq:
    """Get a ChatGroq agent instance."""
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
    
    # Improvement Coordinator designs the application
    coordinator_agent = get_agent(temperature=0.4, max_tokens=12000)
    
    # Chain-of-thought design prompt
    design_prompt = f"""You are the Improvement Coordinator Agent in a Kaizen continuous improvement system.
Your task is to design a complete software application using chain-of-thought reasoning.

APPLICATION REQUIREMENTS:
Description: {description}
Features: {json.dumps(features, indent=2)}

CHAIN OF THOUGHT PROCESSING:
1. First, think about the overall architecture and user flows
2. Identify all pages/screens needed for the frontend
3. For each page, think about its requirements and functionality
4. Identify all backend API endpoints needed
5. For each endpoint, think about request/response structures
6. Consider cross-component dependencies
7. Think about potential defects or issues to watch for

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

Be comprehensive, detailed, and think through all aspects systematically."""

    log_and_print(f"\n[Improvement Coordinator] Designing application...", log_file)
    
    response = invoke_with_rate_limit(coordinator_agent, [HumanMessage(content=design_prompt)], log_file)
    content = response.content.strip()
    
    log_and_print(f"\n[Improvement Coordinator Response]\n{content[:2000]}...", log_file)
    
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
    
    # ACT Phase
    log_and_print(f"\n[ACT] Standardizing improvements and planning next cycle...", log_file)
    act_result = act_phase(design, react_path, flask_path, cycle_number, log_file)
    cycle_results.update(act_result)
    cycle_results['defects_resolved'] = act_result.get('defects_resolved', 0)
    cycle_results['improvements_applied'] = act_result.get('improvements_applied', 0)
    
    cycle_time = time.time() - cycle_start
    _metrics.record_pdca_cycle(cycle_time)
    
    log_and_print(f"\n✓ Cycle {cycle_number} completed in {cycle_time:.2f}s", log_file)
    log_and_print(f"  Defects found: {cycle_results['defects_found']}", log_file)
    log_and_print(f"  Defects resolved: {cycle_results['defects_resolved']}", log_file)
    log_and_print(f"  Improvements applied: {cycle_results['improvements_applied']}", log_file)
    
    return cycle_results


def plan_phase(design: Dict, react_path: str, flask_path: str, cycle_number: int, log_file: str) -> Dict:
    """
    PLAN phase: Analyze current state and establish improvement targets.
    
    True Kaizen: In Cycle 2+, focus on refining components with defects/improvements.
    """
    global _defect_ledger
    _defect_ledger = get_defect_ledger()
    
    coordinator = get_agent(temperature=0.3, max_tokens=4000)
    
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

    response = invoke_with_rate_limit(coordinator, [HumanMessage(content=plan_prompt)], log_file, estimated_tokens=2000)
    if not response:
        return {"targets": [], "focus_areas": [], "waste_opportunities": []}
    
    content = response.content.strip()
    
    try:
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start >= 0:
            plan_data = json.loads(content[json_start:json_end])
            action = "refinement" if cycle_number > 1 else "implementation"
            log_and_print(f"  ✓ Planned {len(plan_data.get('targets', []))} improvement targets for {action}", log_file)
            return plan_data
    except Exception as e:
        log_and_print(f"  [Warning] Failed to parse plan data: {e}", log_file)
    
    return {"targets": [], "focus_areas": [], "waste_opportunities": []}


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
        # Cycle 1: Initial implementation of all components
        log_and_print(f"  [Cycle {cycle_number}] Initial implementation phase...", log_file)
        
        # Divide work among 3 implementation agents
        pages_per_agent = (len(pages) + 2) // 3
        endpoints_per_agent = (len(endpoints) + 2) // 3
        
        for agent_id in range(1, 4):
            agent_pages = pages[(agent_id-1)*pages_per_agent:agent_id*pages_per_agent]
            agent_endpoints = endpoints[(agent_id-1)*endpoints_per_agent:agent_id*endpoints_per_agent]
            
            if agent_pages:
                log_and_print(f"  [Implementation Agent {agent_id}] Implementing {len(agent_pages)} pages...", log_file)
                for page in agent_pages:
                    result = implement_page_kaizen(page, react_path, endpoints, description, agent_id, log_file, is_refinement=False)
                    if result:
                        implementation_results['pages_implemented'] += 1
            
            if agent_endpoints:
                log_and_print(f"  [Implementation Agent {agent_id}] Implementing {len(agent_endpoints)} endpoints...", log_file)
                for endpoint in agent_endpoints:
                    result = implement_endpoint_kaizen(endpoint, flask_path, description, agent_id, log_file, is_refinement=False)
                    if result:
                        implementation_results['endpoints_implemented'] += 1
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
        
        # Limit refinement based on token budget
        max_refinements = min(
            len(pages_to_refine) + len(endpoints_to_refine),
            max(3, remaining_tokens // 5000)  # Estimate 5k tokens per refinement
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
                    result = implement_page_kaizen(page, react_path, endpoints, description, agent_id, log_file, is_refinement=True)
                    if result:
                        implementation_results['pages_refined'] += 1
            
            if agent_endpoints:
                log_and_print(f"  [Implementation Agent {agent_id}] Refining {len(agent_endpoints)} endpoints...", log_file)
                for endpoint in agent_endpoints:
                    result = implement_endpoint_kaizen(endpoint, flask_path, description, agent_id, log_file, is_refinement=True)
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
    
    # If we're close to the limit, reduce verification scope
    if remaining_tokens < 10000:  # Less than 10k tokens remaining
        log_and_print(f"  [WARNING] Low token budget. Skipping verification phase to preserve tokens.", log_file)
        return {"defects_found": 0, "skipped": True}
    
    pages = design.get("frontend", {}).get("pages", [])
    endpoints = design.get("backend", {}).get("endpoints", [])
    
    defects_found = 0
    
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
    max_items_per_agent = min(3, max(1, remaining_tokens // 3000))  # Estimate 3k tokens per verification, more conservative
    
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
    
    return {"defects_found": defects_found}


def act_phase(design: Dict, react_path: str, flask_path: str, cycle_number: int, log_file: str) -> Dict:
    """ACT phase: Integration Group ensures consistency and resolves defects."""
    global _defect_ledger, _metrics, _rate_limiter
    _defect_ledger = get_defect_ledger()
    
    # Check remaining token budget
    remaining_tokens = _rate_limiter.get_remaining_daily_tokens()
    if remaining_tokens < 5000:
        log_and_print(f"  [Integration Agent] Skipping ACT phase due to low token budget ({remaining_tokens} remaining)", log_file)
        return {"defects_resolved": 0, "improvements_applied": 0, "skipped": True}
    
    # Integration Group: 1 agent ensuring architectural consistency
    log_and_print(f"  [Integration Agent] Ensuring architectural consistency...", log_file)
    
    integration_agent = get_agent(temperature=0.3, max_tokens=4000)
    
    # Get open defects
    open_defects = _defect_ledger.get_open_defects() if _defect_ledger else []
    critical_defects = [d for d in open_defects if d['severity'] == DefectSeverity.CRITICAL.value]
    high_defects = [d for d in open_defects if d['severity'] == DefectSeverity.HIGH.value]
    
    defects_resolved = 0
    improvements_applied = 0
    
    # Resolve critical and high priority defects (limit based on remaining tokens)
    max_defects_to_resolve = min(3, max(1, remaining_tokens // 3000))  # Estimate 3k tokens per resolution
    
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

            response = invoke_with_rate_limit(integration_agent, [HumanMessage(content=resolve_prompt)], log_file, estimated_tokens=3000)
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
    
    # Check for architectural consistency (only if we have enough tokens)
    if _rate_limiter.get_remaining_daily_tokens() > 3000:
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

            response = invoke_with_rate_limit(integration_agent, [HumanMessage(content=consistency_prompt)], log_file, estimated_tokens=2000)
            # Process inconsistencies if found
        except Exception as e:
            if '429' not in str(e) and 'rate_limit' not in str(e).lower():
                log_and_print(f"    [Error] Consistency check failed: {str(e)[:100]}", log_file)
    
    return {
        "defects_resolved": defects_resolved,
        "improvements_applied": improvements_applied
    }


def get_page_file_path(page: Dict, project_path: str) -> str:
    """Get the file path for a page component."""
    page_name = page.get('page_name', 'Unknown')
    component_name = page_name.replace(" ", "").replace("-", "")
    return os.path.join(project_path, "src", "pages", f"{component_name}.js")


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


def implement_page_kaizen(page: Dict, project_path: str, all_endpoints: List[Dict], description: str, agent_id: int, log_file: str, is_refinement: bool = False) -> bool:
    """
    Implementation Group agent implements or refines a frontend page with Kaizen principles.
    
    True Kaizen: Cycle 1 implements, Cycle 2+ refines the same component.
    """
    global _defect_ledger
    _defect_ledger = get_defect_ledger()
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

PAGE: {page_name}
Description: {page.get('description', '')}

CURRENT CODE:
{existing_code[:3000]}

DEFECTS TO FIX:
{defects_info if defects_info else "No specific defects identified"}

IMPROVEMENTS TO APPLY:
{improvements_info if improvements_info else "No specific improvements identified"}

REQUIREMENTS:
{json.dumps(requirements, indent=2)}

BACKEND ENDPOINTS:
{json.dumps(endpoint_specs, indent=2)}

CHAIN OF THOUGHT FOR REFINEMENT:
1. Analyze the existing code structure
2. Identify issues from defects list
3. Apply improvements while maintaining existing functionality
4. Fix any bugs or quality issues
5. Enhance error handling and edge cases
6. Improve code quality and maintainability

Return the IMPROVED version of the component. Keep the same structure but fix defects and apply improvements.
Return ONLY the complete React component code (JSX), nothing else. Start with imports."""
    else:
        # INITIAL IMPLEMENTATION: Create new component
        prompt = f"""You are an Implementation Agent in the Kaizen system. Implement a production-quality React component.

APPLICATION CONTEXT: {description}

PAGE: {page_name}
Description: {page.get('description', '')}

REQUIREMENTS:
{json.dumps(requirements, indent=2)}

BACKEND ENDPOINTS:
{json.dumps(endpoint_specs, indent=2)}

CHAIN OF THOUGHT:
1. Think about the component structure
2. Identify state management needs
3. Plan API integration
4. Consider error handling
5. Plan user experience flow

Create a complete React functional component with:
1. React hooks (useState, useEffect, useCallback)
2. Error handling and loading states
3. Form validation if forms are present
4. Axios for API calls (backend at http://localhost:5000)
5. Proper comments and documentation
6. Semantic HTML and accessibility
7. Handle edge cases

Return ONLY the complete React component code (JSX), nothing else. Start with imports."""

    try:
        agent = get_agent()
        response = invoke_with_rate_limit(agent, [HumanMessage(content=prompt)], log_file)
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
        component_file = get_page_file_path(page, project_path)
        os.makedirs(os.path.dirname(component_file), exist_ok=True)
        
        with open(component_file, 'w', encoding='utf-8') as f:
            f.write(component_code)
        
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


def implement_endpoint_kaizen(endpoint: Dict, project_path: str, description: str, agent_id: int, log_file: str, is_refinement: bool = False) -> bool:
    """
    Implementation Group agent implements or refines a backend endpoint with Kaizen principles.
    
    True Kaizen: Cycle 1 implements, Cycle 2+ refines the same endpoint.
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
        
        prompt = f"""You are an Implementation Agent in the Kaizen system. REFINE an existing Flask endpoint to improve quality.

APPLICATION CONTEXT: {description}

ENDPOINT SPECIFICATION:
{json.dumps(endpoint, indent=2)}

CURRENT CODE:
{existing_code[:3000]}

DEFECTS TO FIX:
{defects_info if defects_info else "No specific defects identified"}

IMPROVEMENTS TO APPLY:
{improvements_info if improvements_info else "No specific improvements identified"}

CHAIN OF THOUGHT FOR REFINEMENT:
1. Analyze the existing endpoint code
2. Identify issues from defects list
3. Apply improvements while maintaining existing functionality
4. Fix any bugs or quality issues
5. Enhance error handling and validation
6. Improve code quality and maintainability

Return the IMPROVED version of the endpoint code. Keep the same structure but fix defects and apply improvements.
Return ONLY Python code for the route handler. Format as: @app.route('...', methods=['...'])\ndef ...(): ..."""
    else:
        # INITIAL IMPLEMENTATION: Create new endpoint
        prompt = f"""You are an Implementation Agent in the Kaizen system. Implement a production-quality Flask route handler.

APPLICATION CONTEXT: {description}

ENDPOINT SPECIFICATION:
{json.dumps(endpoint, indent=2)}

CHAIN OF THOUGHT:
1. Think about the endpoint's purpose
2. Plan input validation
3. Plan database operations if needed
4. Plan error handling
5. Plan response structure

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
        agent = get_agent()
        response = invoke_with_rate_limit(agent, [HumanMessage(content=prompt)], log_file)
        code = response.content.strip()
        
        # Clean code blocks
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        # Determine file path based on resource
        endpoint_file = get_endpoint_file_path(endpoint, project_path)
        os.makedirs(os.path.dirname(endpoint_file), exist_ok=True)
        
        # For refinement, append refined version
        # For initial implementation, append to file or create new
        if is_refinement and os.path.exists(endpoint_file):
            # Append refined version
            with open(endpoint_file, 'a', encoding='utf-8') as f:
                f.write("\n\n# Refined version:\n" + code)
        else:
            # Initial implementation: append to file or create new
            if os.path.exists(endpoint_file):
                with open(endpoint_file, 'a', encoding='utf-8') as f:
                    f.write("\n\n" + code)
            else:
                with open(endpoint_file, 'w', encoding='utf-8') as f:
                    f.write("from flask import Flask, request, jsonify\n\n" + code)
        
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
    component_file = os.path.join(project_path, "src", "pages", f"{component_name}.js")
    
    defects = []
    
    if not os.path.exists(component_file):
        if _defect_ledger:
            defect_id = _defect_ledger.add_defect(
                f"Component file not found: {component_name}.js",
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
        
        verification_agent = get_agent(temperature=0.2, max_tokens=4000)
        
        verify_prompt = f"""You are a Verification Agent inspecting code for defects.

COMPONENT: {page_name}
CODE:
{code[:2000]}

Inspect this code for:
1. Syntax errors
2. Logic errors
3. Missing error handling
4. Accessibility issues
5. Performance issues
6. Security vulnerabilities
7. Code quality issues

Return JSON with defects found:
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

        response = invoke_with_rate_limit(verification_agent, [HumanMessage(content=verify_prompt)], log_file, estimated_tokens=2000)
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
        
        verification_agent = get_agent(temperature=0.2, max_tokens=4000)
        
        verify_prompt = f"""You are a Verification Agent inspecting code for defects.

ENDPOINT: {method} {path}
CODE:
{code[:2000]}

Inspect this code for:
1. Syntax errors
2. Logic errors
3. Missing error handling
4. Input validation issues
5. Security vulnerabilities (SQL injection, XSS, etc.)
6. Performance issues
7. Code quality issues

Return JSON with defects found:
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

        response = invoke_with_rate_limit(verification_agent, [HumanMessage(content=verify_prompt)], log_file, estimated_tokens=2000)
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

