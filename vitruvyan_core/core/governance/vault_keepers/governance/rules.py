"""
Vault Keepers — Governance Rules

Pure business rules for vault operations.
No I/O, no infrastructure, fully testable.

Rules cover:
  - Retention policies
  - Integrity thresholds
  - Backup scheduling
  - Archive priorities
"""

from typing import Dict, Any
from datetime import datetime, timedelta


class VaultRules:
    """
    Sacred rules governing vault operations.
    All methods are pure functions: same input → same output.
    """
    
    # Retention policies (days)
    RETENTION_SNAPSHOTS = 30
    RETENTION_ARCHIVES_DEFAULT = 90
    RETENTION_ARCHIVES_CRITICAL = 365
    RETENTION_AUDIT_RECORDS = 730  # 2 years for compliance
    
    # Integrity thresholds
    COHERENCE_RATIO_MIN = 0.95  # 95% coherence required for "sacred" status
    COHERENCE_RATIO_WARN = 0.85  # 85% triggers warning
    
    # Backup scheduling
    BACKUP_FULL_INTERVAL_HOURS = 24
    BACKUP_INCREMENTAL_INTERVAL_HOURS = 6
    
    @staticmethod
    def should_retain_snapshot(snapshot_age_days: int, snapshot_type: str = "regular") -> bool:
        """
        Determine if a snapshot should be retained.
        
        Args:
            snapshot_age_days: Age of snapshot in days
            snapshot_type: "regular" | "critical"
            
        Returns:
            True if snapshot should be kept
        """
        if snapshot_type == "critical":
            return snapshot_age_days <= VaultRules.RETENTION_SNAPSHOTS * 2
        return snapshot_age_days <= VaultRules.RETENTION_SNAPSHOTS
    
    @staticmethod
    def should_retain_archive(archive_age_days: int, content_type: str = "generic") -> bool:
        """
        Determine if an archive should be retained.
        
        Args:
            archive_age_days: Age of archive in days
            content_type: Type of archived content
            
        Returns:
            True if archive should be kept
        """
        if content_type in ["critical", "compliance", "audit"]:
            return archive_age_days <= VaultRules.RETENTION_ARCHIVES_CRITICAL
        return archive_age_days <= VaultRules.RETENTION_ARCHIVES_DEFAULT
    
    @staticmethod
    def evaluate_coherence_status(coherence_ratio: float) -> str:
        """
        Evaluate coherence status from ratio.
        
        Args:
            coherence_ratio: Ratio of coherent records (0.0 to 1.0)
            
        Returns:
            "coherent" | "drift_detected" | "critical"
        """
        if coherence_ratio >= VaultRules.COHERENCE_RATIO_MIN:
            return "coherent"
        elif coherence_ratio >= VaultRules.COHERENCE_RATIO_WARN:
            return "drift_detected"
        else:
            return "critical"
    
    @staticmethod
    def calculate_backup_priority(last_backup_hours: float, data_volatility: float = 0.5) -> str:
        """
        Calculate backup priority based on time and volatility.
        
        Args:
            last_backup_hours: Hours since last backup
            data_volatility: Rate of data change (0.0 = static, 1.0 = high churn)
            
        Returns:
            "low" | "normal" | "high" | "critical"
        """
        # Adjust threshold by volatility
        threshold_high = VaultRules.BACKUP_INCREMENTAL_INTERVAL_HOURS * (1 - data_volatility * 0.5)
        threshold_critical = VaultRules.BACKUP_FULL_INTERVAL_HOURS * (1 - data_volatility * 0.5)
        
        if last_backup_hours >= threshold_critical:
            return "critical"
        elif last_backup_hours >= threshold_high:
            return "high"
        elif last_backup_hours >= VaultRules.BACKUP_INCREMENTAL_INTERVAL_HOURS / 2:
            return "normal"
        else:
            return "low"
    
    @staticmethod
    def requires_integrity_check_before_backup(priority: str) -> bool:
        """
        Determine if integrity check is required before backup.
        
        Args:
            priority: Backup priority level
            
        Returns:
            True if integrity check is required first
        """
        return priority in ["high", "critical"]
    
    @staticmethod
    def calculate_retention_date(content_type: str) -> str:
        """
        Calculate retention expiry date for content.
        
        Args:
            content_type: Type of content being archived
            
        Returns:
            ISO timestamp for retention expiry
        """
        if content_type in ["critical", "compliance", "audit"]:
            days = VaultRules.RETENTION_ARCHIVES_CRITICAL
        else:
            days = VaultRules.RETENTION_ARCHIVES_DEFAULT
        
        expiry = datetime.utcnow() + timedelta(days=days)
        return expiry.isoformat()
    
    @staticmethod
    def validate_snapshot_metadata(metadata: Dict[str, Any]) -> tuple:
        """
        Validate snapshot metadata for completeness.
        
        Args:
            metadata: Snapshot metadata dict
            
        Returns:
            (is_valid: bool, missing_fields: list)
        """
        required_fields = ["mode", "scope", "correlation_id"]
        missing = [f for f in required_fields if f not in metadata]
        return (len(missing) == 0, missing)
