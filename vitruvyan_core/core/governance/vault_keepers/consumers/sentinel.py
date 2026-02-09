"""
Vault Keepers — Sentinel Consumer

The Sentinel validates data integrity and detects corruption.
Pure logic: given database health data, determines integrity status.

Sacred Order: Truth (Memory & Archival)
Layer: Foundational (consumers)
"""

from typing import Any, Dict
from datetime import datetime

from ..consumers.base import VaultRole
from ..domain.vault_objects import IntegrityReport


class Sentinel(VaultRole):
    """
    The Sentinel: Data Integrity Validator
    
    Judges the health of PostgreSQL, Qdrant, and cross-system coherence.
    Does NOT perform database queries — receives health data from service layer.
    
    Input (dict):
        {
            "postgresql": {"status": "healthy|degraded|corrupted", "tables": {...}},
            "qdrant": {"status": "healthy|degraded|corrupted", "collections": {...}},
            "coherence": {"status": "coherent|drift_detected|critical", "ratio": float},
            "correlation_id": str (optional)
        }
    
    Output:
        IntegrityReport with overall judgment and findings
    """
    
    @property
    def role_name(self) -> str:
        return "sentinel"
    
    @property
    def description(self) -> str:
        return "Validates data integrity and detects corruption"
    
    def can_handle(self, event: Any) -> bool:
        """Handles integrity check events"""
        if isinstance(event, dict):
            return "postgresql" in event and "qdrant" in event
        return False
    
    def process(self, event: Dict[str, Any]) -> IntegrityReport:
        """
        Pure integrity validation logic.
        
        Args:
            event: Health data from databases
            
        Returns:
            IntegrityReport with judgment
        """
        pg_data = event.get("postgresql", {})
        qdrant_data = event.get("qdrant", {})
        coherence_data = event.get("coherence", {})
        correlation_id = event.get("correlation_id", "unknown")
        
        # Extract statuses (normalize "error" to "corrupted")
        pg_status = pg_data.get("status", "unreachable")
        if pg_status == "error":
            pg_status = "corrupted"
        
        qdrant_status = qdrant_data.get("status", "unreachable")
        if qdrant_status == "error":
            qdrant_status = "corrupted"
        
        coherence_status = coherence_data.get("status", "critical")
        if coherence_status == "error":
            coherence_status = "critical"
        
        # Determine overall status
        overall_status = self._judge_overall_integrity(pg_status, qdrant_status, coherence_status)
        
        # Collect findings
        findings = self._collect_findings(pg_data, qdrant_data, coherence_data)
        
        # Generate blessing
        warden_blessing = self._generate_blessing(overall_status)
        
        # Create report
        report_id = f"integrity_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        return IntegrityReport(
            report_id=report_id,
            timestamp=datetime.utcnow().isoformat(),
            postgresql_status=pg_status,
            qdrant_status=qdrant_status,
            coherence_status=coherence_status,
            overall_status=overall_status,
            findings=tuple(findings),
            warden_blessing=warden_blessing
        )
    
    def _judge_overall_integrity(self, pg_status: str, qdrant_status: str, coherence_status: str) -> str:
        """
        Determine overall integrity status from component statuses.
        
        Returns:
            "sacred" | "blessed_with_concerns" | "corruption_detected"
        """
        # Critical: any system corrupted or unreachable
        if any(s in ["corrupted", "unreachable"] for s in [pg_status, qdrant_status]):
            return "corruption_detected"
        
        if coherence_status == "critical":
            return "corruption_detected"
        
        # All healthy and coherent
        if all(s == "healthy" for s in [pg_status, qdrant_status]) and coherence_status == "coherent":
            return "sacred"
        
        # Degraded or drift detected
        return "blessed_with_concerns"
    
    def _collect_findings(self, pg_data: Dict, qdrant_data: Dict, coherence_data: Dict) -> list:
        """Collect specific findings from health data"""
        findings = []
        
        # PostgreSQL findings
        if pg_data.get("status") == "degraded":
            tables = pg_data.get("tables", {})
            error_tables = [t for t, info in tables.items() if info.get("status") == "error"]
            if error_tables:
                findings.append(f"PostgreSQL: {len(error_tables)} tables with errors: {', '.join(error_tables)}")
        elif pg_data.get("status") == "corrupted":
            findings.append("PostgreSQL: Database connectivity issues detected")
        
        # Qdrant findings
        if qdrant_data.get("status") == "degraded":
            findings.append("Qdrant: Vector database degraded performance")
        elif qdrant_data.get("status") == "corrupted":
            findings.append("Qdrant: Vector database unreachable")
        
        # Coherence findings
        if coherence_data.get("status") == "drift_detected":
            ratio = coherence_data.get("coherence_ratio", 0)
            findings.append(f"Coherence: Data drift detected (ratio: {ratio:.2%})")
        elif coherence_data.get("status") == "critical":
            findings.append("Coherence: Critical data inconsistency between systems")
        
        return findings
    
    def _generate_blessing(self, overall_status: str) -> str:
        """Generate Sentinel's blessing based on status"""
        blessings = {
            "sacred": "integrity_verified",
            "blessed_with_concerns": "integrity_acceptable_with_warnings",
            "corruption_detected": "integrity_violation_detected"
        }
        return blessings.get(overall_status, "integrity_unknown")
