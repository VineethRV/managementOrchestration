"""
Defect Ledger: Shared defect tracking system for Kaizen methodology.
Tracks defects, improvements, and waste elimination throughout PDCA cycles.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class DefectSeverity(Enum):
    """Severity levels for defects."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINOR = "minor"


class DefectStatus(Enum):
    """Status of defect resolution."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    CLOSED = "closed"


class DefectLedger:
    """
    Central defect ledger for tracking issues, improvements, and waste elimination.
    Supports transparency and continuous learning across all agent groups.
    """
    
    def __init__(self, ledger_path: str = None):
        """
        Initialize the defect ledger.
        
        Args:
            ledger_path: Path to save/load ledger JSON file
        """
        self.ledger_path = ledger_path or os.path.join("logs", f"defect_ledger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        
        self.defects: List[Dict[str, Any]] = []
        self.improvements: List[Dict[str, Any]] = []
        self.waste_eliminations: List[Dict[str, Any]] = []
        self.defect_counter = 0
        
        # Load existing ledger if it exists
        self._load_ledger()
    
    def _load_ledger(self):
        """Load existing ledger from file if it exists."""
        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.defects = data.get('defects', [])
                    self.improvements = data.get('improvements', [])
                    self.waste_eliminations = data.get('waste_eliminations', [])
                    self.defect_counter = data.get('defect_counter', len(self.defects))
            except Exception as e:
                print(f"[WARNING] Failed to load defect ledger: {e}")
    
    def _save_ledger(self):
        """Save ledger to file."""
        try:
            data = {
                'defects': self.defects,
                'improvements': self.improvements,
                'waste_eliminations': self.waste_eliminations,
                'defect_counter': self.defect_counter,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.ledger_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[WARNING] Failed to save defect ledger: {e}")
    
    def add_defect(
        self,
        description: str,
        component: str,
        severity: DefectSeverity,
        detected_by: str,
        category: str = "general",
        metadata: Dict[str, Any] = None
    ) -> int:
        """
        Add a new defect to the ledger.
        
        Args:
            description: Description of the defect
            component: Component where defect was found (e.g., "frontend/HomePage", "backend/api/users")
            severity: Severity level
            detected_by: Agent/group that detected the defect
            category: Category of defect (e.g., "syntax", "logic", "performance", "security")
            metadata: Additional metadata about the defect
        
        Returns:
            Defect ID
        """
        self.defect_counter += 1
        defect = {
            'id': self.defect_counter,
            'description': description,
            'component': component,
            'severity': severity.value,
            'status': DefectStatus.OPEN.value,
            'detected_by': detected_by,
            'detected_at': datetime.now().isoformat(),
            'category': category,
            'metadata': metadata or {},
            'resolved_by': None,
            'resolved_at': None,
            'verification_notes': []
        }
        
        self.defects.append(defect)
        self._save_ledger()
        
        return self.defect_counter
    
    def update_defect_status(
        self,
        defect_id: int,
        status: DefectStatus,
        resolved_by: str = None,
        verification_notes: str = None
    ) -> bool:
        """
        Update the status of a defect.
        
        Args:
            defect_id: ID of the defect
            status: New status
            resolved_by: Agent/group that resolved it
            verification_notes: Notes from verification
        
        Returns:
            True if defect was found and updated
        """
        for defect in self.defects:
            if defect['id'] == defect_id:
                defect['status'] = status.value
                if status == DefectStatus.RESOLVED or status == DefectStatus.VERIFIED:
                    defect['resolved_by'] = resolved_by
                    defect['resolved_at'] = datetime.now().isoformat()
                if verification_notes:
                    defect['verification_notes'].append({
                        'note': verification_notes,
                        'added_at': datetime.now().isoformat(),
                        'added_by': resolved_by or 'system'
                    })
                self._save_ledger()
                return True
        return False
    
    def add_improvement(
        self,
        description: str,
        component: str,
        suggested_by: str,
        impact: str = "medium",
        metadata: Dict[str, Any] = None
    ) -> int:
        """
        Add an improvement suggestion.
        
        Args:
            description: Description of the improvement
            component: Component to be improved
            suggested_by: Agent/group that suggested it
            impact: Expected impact level (low, medium, high)
            metadata: Additional metadata
        
        Returns:
            Improvement ID
        """
        improvement = {
            'id': len(self.improvements) + 1,
            'description': description,
            'component': component,
            'suggested_by': suggested_by,
            'suggested_at': datetime.now().isoformat(),
            'impact': impact,
            'status': 'pending',
            'metadata': metadata or {}
        }
        
        self.improvements.append(improvement)
        self._save_ledger()
        
        return improvement['id']
    
    def add_waste_elimination(
        self,
        waste_type: str,
        description: str,
        eliminated_by: str,
        savings: str = None
    ) -> int:
        """
        Record waste elimination (muda).
        
        Args:
            waste_type: Type of waste (e.g., "redundant_processing", "excess_complexity", "inconsistent_standards")
            description: Description of eliminated waste
            eliminated_by: Agent/group that eliminated it
            savings: Description of time/complexity savings
        
        Returns:
            Waste elimination ID
        """
        elimination = {
            'id': len(self.waste_eliminations) + 1,
            'waste_type': waste_type,
            'description': description,
            'eliminated_by': eliminated_by,
            'eliminated_at': datetime.now().isoformat(),
            'savings': savings
        }
        
        self.waste_eliminations.append(elimination)
        self._save_ledger()
        
        return elimination['id']
    
    def get_open_defects(self, component: str = None, severity: DefectSeverity = None) -> List[Dict[str, Any]]:
        """
        Get all open defects, optionally filtered by component or severity.
        
        Args:
            component: Filter by component (optional)
            severity: Filter by severity (optional)
        
        Returns:
            List of open defects
        """
        open_defects = [
            d for d in self.defects
            if d['status'] in [DefectStatus.OPEN.value, DefectStatus.IN_PROGRESS.value]
        ]
        
        if component:
            open_defects = [d for d in open_defects if component in d['component']]
        
        if severity:
            open_defects = [d for d in open_defects if d['severity'] == severity.value]
        
        return open_defects
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about defects, improvements, and waste elimination.
        
        Returns:
            Dictionary with statistics
        """
        total_defects = len(self.defects)
        open_defects = len(self.get_open_defects())
        resolved_defects = len([d for d in self.defects if d['status'] == DefectStatus.RESOLVED.value])
        verified_defects = len([d for d in self.defects if d['status'] == DefectStatus.VERIFIED.value])
        
        severity_counts = {}
        for severity in DefectSeverity:
            severity_counts[severity.value] = len([
                d for d in self.defects if d['severity'] == severity.value
            ])
        
        return {
            'total_defects': total_defects,
            'open_defects': open_defects,
            'resolved_defects': resolved_defects,
            'verified_defects': verified_defects,
            'resolution_rate': (resolved_defects + verified_defects) / total_defects if total_defects > 0 else 0,
            'severity_breakdown': severity_counts,
            'total_improvements': len(self.improvements),
            'total_waste_eliminations': len(self.waste_eliminations)
        }
    
    def export_report(self, report_path: str = None) -> str:
        """
        Export a comprehensive defect report.
        
        Args:
            report_path: Path to save report (optional)
        
        Returns:
            Report content as string
        """
        stats = self.get_statistics()
        
        report = f"""
DEFECT LEDGER REPORT
{'='*70}
Generated: {datetime.now().isoformat()}
Ledger Path: {self.ledger_path}

STATISTICS
{'-'*70}
Total Defects: {stats['total_defects']}
Open Defects: {stats['open_defects']}
Resolved Defects: {stats['resolved_defects']}
Verified Defects: {stats['verified_defects']}
Resolution Rate: {stats['resolution_rate']:.2%}

Severity Breakdown:
  Critical: {stats['severity_breakdown']['critical']}
  High: {stats['severity_breakdown']['high']}
  Medium: {stats['severity_breakdown']['medium']}
  Low: {stats['severity_breakdown']['low']}
  Minor: {stats['severity_breakdown']['minor']}

Total Improvements: {stats['total_improvements']}
Total Waste Eliminations: {stats['total_waste_eliminations']}

OPEN DEFECTS
{'-'*70}
"""
        
        open_defects = self.get_open_defects()
        if open_defects:
            for defect in open_defects:
                report += f"""
ID: {defect['id']}
Component: {defect['component']}
Severity: {defect['severity']}
Status: {defect['status']}
Detected By: {defect['detected_by']}
Description: {defect['description']}
Category: {defect['category']}
---
"""
        else:
            report += "No open defects.\n"
        
        if report_path:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report



