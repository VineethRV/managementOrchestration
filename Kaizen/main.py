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
from kaizen_orchestrator import (
    gather_requirements_interactive,
    design_application_kaizen,
    run_pdca_cycle,
    _metrics,
    log_and_print,
    set_defect_ledger,
    get_defect_ledger
)
from defect_ledger import DefectLedger
from rate_limiter import RateLimiter

# Import project generator from Top down directory
topdown_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Top down")
sys.path.insert(0, topdown_path)
from project_generator import generate_projects


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
    
    # Ask if user wants to generate projects
    user_input = input("\n\nWould you like to generate React and Flask projects? (yes/no): ").strip().lower()
    if user_input not in ['yes', 'y']:
        log_and_print("\nProject generation skipped.", main_log)
        return
    
    # Phase 3: Generate Project Scaffolding
    log_and_print("\n" + "="*70, main_log)
    log_and_print("PHASE 3: PROJECT SCAFFOLDING GENERATION", main_log)
    log_and_print("="*70, main_log)
    
    project_paths = generate_projects(design)
    
    react_path = project_paths.get('react')
    flask_path = project_paths.get('flask')
    
    if not react_path or not flask_path:
        log_and_print("\n⚠ Failed to generate projects.", main_log)
        return
    
    log_and_print(f"\n✓ Projects generated:", main_log)
    log_and_print(f"  React: {react_path}", main_log)
    log_and_print(f"  Flask: {flask_path}", main_log)
    
    # Ask if user wants to run PDCA cycles
    user_input = input("\n\nWould you like to run PDCA cycles for continuous improvement? (yes/no): ").strip().lower()
    if user_input not in ['yes', 'y']:
        log_and_print("\nPDCA cycles skipped.", main_log)
        return
    
    # Phase 4: PDCA Cycles
    log_and_print("\n" + "="*70, main_log)
    log_and_print("PHASE 4: PDCA CYCLES (Continuous Improvement)", main_log)
    log_and_print("="*70, main_log)
    
    # Ask for number of cycles
    try:
        num_cycles = int(input("\nHow many PDCA cycles would you like to run? (default: 3): ").strip() or "3")
    except ValueError:
        num_cycles = 3
    
    log_and_print(f"\nRunning {num_cycles} PDCA cycles...", main_log)
    
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

