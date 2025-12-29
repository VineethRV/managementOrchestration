"""
Kaizen Methodology: Main Entry Point
Continuous improvement multi-agent system with PDCA cycles.

Usage:
    python main.py

This will:
1. Gather requirements
2. Design application (Improvement Coordinator)
3. Generate project scaffolding
4. Run PDCA cycles for continuous improvement
5. Track metrics and defects
"""

import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file in the Kaizen folder
# Get the directory where main.py is located
kaizen_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(kaizen_dir, ".env")

# Load .env file if it exists
api_key_loaded = False
api_key = None

if os.path.exists(env_path):
    # First, try to manually parse the .env file to handle any formatting issues
    try:
        with open(env_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    # Set environment variable directly
                    if key == "GROQ_API_KEY":
                        os.environ[key] = value
                        api_key = value
                        api_key_loaded = True
                        masked_key = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                        print(f"✓ Loaded GROQ_API_KEY from .env file: {masked_key}")
                        break
    except Exception as e:
        print(f"⚠ Error reading .env file manually: {e}")
    
    # Also try load_dotenv as backup
    if not api_key_loaded:
        load_dotenv(env_path, override=True)
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            api_key_loaded = True
            masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
            print(f"✓ Loaded GROQ_API_KEY via load_dotenv: {masked_key}")
else:
    # Try loading from current directory (fallback)
    load_dotenv(override=True)
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        api_key_loaded = True
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"✓ Loaded GROQ_API_KEY from current directory: {masked_key}")

# Verify API key is set before importing kaizen_orchestrator
if not api_key_loaded or not os.getenv("GROQ_API_KEY"):
    print("\n❌ Error: GROQ_API_KEY not found in environment variables.")
    print(f"   Please create or fix the .env file at: {env_path}")
    print("   With the following content (NO quotes, NO spaces around =):")
    print("   GROQ_API_KEY=your_api_key_here")
    sys.exit(1)

from kaizen_orchestrator import (
    gather_requirements_interactive,
    design_application_kaizen,
    run_pdca_cycle,
    _metrics,
    log_and_print,
    set_defect_ledger,
    get_defect_ledger,
    determine_db_usage,
    generate_react_tailwind_project,
    generate_flask_mongodb_backend
)
from defect_ledger import DefectLedger
from rate_limiter import RateLimiter


def main():
    """Main orchestrator for Kaizen continuous improvement methodology."""
    global _defect_ledger
    
    # Initialize logs directory
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_log = os.path.join(logs_dir, f"kaizen_main_{timestamp}.log")
    
    print("\n" + "="*70)
    print("KAIZEN METHODOLOGY: CONTINUOUS IMPROVEMENT SYSTEM")
    print("="*70)
    print("\nThis system uses PDCA cycles with three specialized agent groups:")
    print("  - Implementation Group: Produces and refines core logic")
    print("  - Verification Group: Performs inspections and identifies defects")
    print("  - Integration Group: Ensures architectural consistency")
    print("="*70)
    
    # Initialize defect ledger
    ledger_path = os.path.join(logs_dir, f"defect_ledger_{timestamp}.json")
    defect_ledger = DefectLedger(ledger_path)
    set_defect_ledger(defect_ledger)
    log_and_print(f"\n✓ Defect ledger initialized: {ledger_path}", main_log)
    
    # Phase 1: Requirements Gathering
    log_and_print("\n" + "="*70, main_log)
    log_and_print("PHASE 1: REQUIREMENTS GATHERING", main_log)
    log_and_print("="*70, main_log)
    
    requirements = gather_requirements_interactive()
    if not requirements.get("is_finalized"):
        log_and_print("\n⚠ Cannot proceed without finalized requirements.", main_log)
        return
    
    log_and_print(f"\n✓ Requirements finalized:", main_log)
    log_and_print(f"  Description: {requirements['detailed_description'][:100]}...", main_log)
    log_and_print(f"  Features: {len(requirements['features'])} features", main_log)
    
    # Phase 2: Application Design (Improvement Coordinator)
    log_and_print("\n" + "="*70, main_log)
    log_and_print("PHASE 2: APPLICATION DESIGN (Improvement Coordinator)", main_log)
    log_and_print("="*70, main_log)
    
    design = design_application_kaizen(
        requirements["detailed_description"],
        requirements["features"]
    )
    
    # Save design
    design_path = os.path.join(logs_dir, f"kaizen_design_{timestamp}.json")
    with open(design_path, 'w', encoding='utf-8') as f:
        json.dump(design, f, indent=2)
    log_and_print(f"\n✓ Design saved to: {design_path}", main_log)
    
    pages_count = len(design.get('frontend', {}).get('pages', []))
    endpoints_count = len(design.get('backend', {}).get('endpoints', []))
    log_and_print(f"  Frontend: {pages_count} pages", main_log)
    log_and_print(f"  Backend: {endpoints_count} endpoints", main_log)
    
    # Phase 3: Determine project paths (projects will be generated in Cycle 1)
    log_and_print("\n" + "="*70, main_log)
    log_and_print("PHASE 3: PROJECT SETUP", main_log)
    log_and_print("="*70, main_log)
    
    # Determine MongoDB usage
    use_mongodb = determine_db_usage(
        requirements["detailed_description"],
        requirements["features"],
        design
    )
    
    # Set project paths (will be created in Cycle 1 DO phase)
    react_path = os.path.abspath("frontend")
    flask_path = os.path.abspath("backend")
    
    log_and_print(f"\n✓ Project paths configured:", main_log)
    log_and_print(f"  React + Tailwind CSS: {react_path}", main_log)
    log_and_print(f"  Flask {'+ MongoDB' if use_mongodb else '(no database)'}: {flask_path}", main_log)
    log_and_print(f"\n  Note: Projects will be generated in Cycle 1 DO phase", main_log)
    
    # Phase 4: PDCA Cycles
    log_and_print("\n" + "="*70, main_log)
    log_and_print("PHASE 4: PDCA CYCLES (Continuous Improvement)", main_log)
    log_and_print("="*70, main_log)
    
    # Default to 1 PDCA cycle
    num_cycles = 1
    log_and_print(f"\nRunning {num_cycles} PDCA cycle...", main_log)
    
    cycle_results = []
    for cycle_num in range(1, num_cycles + 1):
        log_and_print(f"\n{'='*70}", main_log)
        log_and_print(f"Starting PDCA Cycle {cycle_num}/{num_cycles}", main_log)
        log_and_print(f"{'='*70}", main_log)
        
        result = run_pdca_cycle(
            design,
            react_path,
            flask_path,
            requirements["detailed_description"],
            cycle_num,
            main_log
        )
        cycle_results.append(result)
        
        # Show cycle summary
        log_and_print(f"\nCycle {cycle_num} Summary:", main_log)
        log_and_print(f"  Defects found: {result.get('defects_found', 0)}", main_log)
        log_and_print(f"  Defects resolved: {result.get('defects_resolved', 0)}", main_log)
        log_and_print(f"  Improvements applied: {result.get('improvements_applied', 0)}", main_log)
        
        # Check if we should continue
        if cycle_num < num_cycles:
            defect_ledger = get_defect_ledger()
            if defect_ledger:
                defect_stats = defect_ledger.get_statistics()
                if defect_stats.get('open_defects', 0) == 0:
                    log_and_print("\n✓ No open defects remaining. All cycles may not be necessary.", main_log)
                    continue_choice = input("\nContinue with remaining cycles? (yes/no): ").strip().lower()
                    if continue_choice not in ['yes', 'y']:
                        break
    
    # Final Summary
    log_and_print("\n" + "="*70, main_log)
    log_and_print("KAIZEN METHODOLOGY COMPLETE", main_log)
    log_and_print("="*70, main_log)
    
    # Defect ledger statistics
    defect_ledger = get_defect_ledger()
    if defect_ledger:
        defect_stats = defect_ledger.get_statistics()
    log_and_print(f"\nDEFECT LEDGER STATISTICS:", main_log)
    log_and_print(f"  Total defects: {defect_stats['total_defects']}", main_log)
    log_and_print(f"  Open defects: {defect_stats['open_defects']}", main_log)
    log_and_print(f"  Resolved defects: {defect_stats['resolved_defects']}", main_log)
    log_and_print(f"  Verified defects: {defect_stats['verified_defects']}", main_log)
    log_and_print(f"  Resolution rate: {defect_stats['resolution_rate']:.2%}", main_log)
    log_and_print(f"  Total improvements: {defect_stats['total_improvements']}", main_log)
    log_and_print(f"  Waste eliminations: {defect_stats['total_waste_eliminations']}", main_log)
    
    # Metrics
    metrics = _metrics.get_metrics()
    log_and_print(f"\nMETRICS:", main_log)
    log_and_print(f"  Total tokens: {metrics['total_tokens']:,}", main_log)
    log_and_print(f"  Total requests: {metrics['total_requests']}", main_log)
    log_and_print(f"  PDCA cycles completed: {metrics['pdca_cycles']}", main_log)
    log_and_print(f"  Average cycle time: {metrics['average_cycle_time_seconds']:.2f}s", main_log)
    log_and_print(f"  Total duration: {metrics['duration_seconds']:.2f}s", main_log)
    
    # Save metrics
    metrics_path = os.path.join(logs_dir, f"kaizen_metrics_{timestamp}.json")
    _metrics.save(metrics_path)
    log_and_print(f"\n✓ Metrics saved to: {metrics_path}", main_log)
    
    # Export defect report
    if defect_ledger:
        report_path = os.path.join(logs_dir, f"defect_report_{timestamp}.txt")
        defect_ledger.export_report(report_path)
        log_and_print(f"✓ Defect report saved to: {report_path}", main_log)
    
    # Save cycle results
    cycles_path = os.path.join(logs_dir, f"pdca_cycles_{timestamp}.json")
    with open(cycles_path, 'w', encoding='utf-8') as f:
        json.dump(cycle_results, f, indent=2)
    log_and_print(f"✓ Cycle results saved to: {cycles_path}", main_log)
    
    log_and_print("\n" + "="*70, main_log)
    log_and_print("All files saved to logs directory", main_log)
    log_and_print("="*70, main_log)


if __name__ == "__main__":
    main()

