"""
Vault Keepers — Signal Archivist Consumer

Extension of Archivist for signal timeseries archival.
Pure logic: converts signal extraction results to archivable timeseries.

Sacred Order: Truth (Memory & Archival)
Layer: Foundational (consumers)
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import hashlib

from ..consumers.base import VaultRole
from ..domain.signal_archive import SignalDataPoint, SignalTimeseries


class SignalArchivist(VaultRole):
    """
    The Signal Archivist: Signal Timeseries Planner
    
    Creates archival plans for Babel Gardens signal extractions.
    Does NOT perform actual archival — creates SignalTimeseries for service layer to store.
    
    Input (dict):
        {
            "operation": "archive_signal_timeseries",
            "entity_id": str,                # Domain-agnostic (ticker, IP, vessel IMO, patient ID, etc.)
            "signal_results": List[dict],    # List of signal extraction results from Babel Gardens
            "vertical": str,                 # "finance", "cybersecurity", "healthcare", etc.
            "schema_version": str,           # Babel Gardens version (e.g., "2.1")
            "retention_days": int,           # How long to keep data (default: 365)
            "correlation_id": str
        }
    
    signal_results format (from Babel Gardens):
        [
            {
                "signal_name": "sentiment_valence",
                "value": 0.65,
                "confidence": 0.88,
                "extraction_trace": {
                    "method": "model:finbert",
                    "timestamp": "2026-02-11T14:00:00Z",
                    "model_version": "finbert-0.4"
                },
                "source_text": "Apple announced record earnings..."  # Optional
            },
            ...
        ]
    
    Output:
        SignalTimeseries with data points ready for archival
    
    Design Principles:
        - Domain-agnostic: Works with ANY vertical (finance, cyber, healthcare, sports, etc.)
        - Traceable: Each data point includes extraction method + source text hash
        - Compressible: Efficient storage format for long-term retention
    """
    
    @property
    def role_name(self) -> str:
        return "signal_archivist"
    
    @property
    def description(self) -> str:
        return "Plans signal timeseries archival for Babel Gardens extractions"
    
    def can_handle(self, event: Any) -> bool:
        """Handles signal timeseries archival events"""
        if isinstance(event, dict):
            operation = event.get("operation", "")
            return operation == "archive_signal_timeseries"
        return False
    
    def process(self, event: Dict[str, Any]) -> SignalTimeseries:
        """
        Pure signal archival planning logic.
        
        Args:
            event: Signal timeseries archival request (from Babel Gardens)
            
        Returns:
            SignalTimeseries ready for storage
            
        Raises:
            ValueError: If input validation fails
        """
        # Validate input
        entity_id = event.get("entity_id")
        if not entity_id:
            raise ValueError("entity_id is required")
        
        signal_results = event.get("signal_results", [])
        if not signal_results:
            raise ValueError("signal_results cannot be empty")
        
        vertical = event.get("vertical", "unknown")
        schema_version = event.get("schema_version", "2.1")
        retention_days = event.get("retention_days", 365)
        
        # Extract signal name (all results should have same signal_name in this batch)
        first_result = signal_results[0]
        signal_name = first_result.get("signal_name")
        if not signal_name:
            raise ValueError("signal_name missing in signal_results")
        
        # Validate all results have same signal_name
        for result in signal_results:
            if result.get("signal_name") != signal_name:
                raise ValueError(f"Mixed signal names in batch: {signal_name} vs {result.get('signal_name')}")
        
        # Convert signal results to data points
        data_points = self._convert_to_data_points(signal_results)
        
        # Generate timeseries ID
        archive_timestamp = datetime.utcnow()
        timeseries_id = self._generate_timeseries_id(entity_id, signal_name, archive_timestamp)
        
        # Calculate retention
        retention_until = (archive_timestamp + timedelta(days=retention_days)).isoformat()
        
        # Create timeseries
        return SignalTimeseries(
            timeseries_id=timeseries_id,
            entity_id=entity_id,
            signal_name=signal_name,
            vertical=vertical,
            data_points=tuple(data_points),
            schema_version=schema_version,
            retention_until=retention_until,
            archive_timestamp=archive_timestamp.isoformat(),
            metadata=(
                ("correlation_id", event.get("correlation_id", "unknown")),
                ("data_points_count", str(len(data_points))),
            )
        )
    
    def _convert_to_data_points(self, signal_results: List[Dict[str, Any]]) -> List[SignalDataPoint]:
        """
        Convert Babel Gardens signal results to SignalDataPoint objects.
        
        Args:
            signal_results: List of dicts from Babel Gardens
            
        Returns:
            List of SignalDataPoint objects
        """
        data_points = []
        
        for result in signal_results:
            # Extract fields
            value = result.get("value")
            if value is None:
                continue  # Skip invalid results
            
            confidence = result.get("confidence", 0.0)
            extraction_trace = result.get("extraction_trace", {})
            extraction_method = extraction_trace.get("method", "unknown")
            timestamp = extraction_trace.get("timestamp", datetime.utcnow().isoformat())
            
            # Hash source text for traceability (optional)
            source_text = result.get("source_text")
            source_text_hash = None
            if source_text:
                source_text_hash = hashlib.sha256(source_text.encode()).hexdigest()[:16]  # First 16 chars
            
            # Build metadata tuple
            metadata_pairs = []
            if "model_version" in extraction_trace:
                metadata_pairs.append(("model_version", extraction_trace["model_version"]))
            if "entity_id" in result:
                metadata_pairs.append(("entity_id", result["entity_id"]))
            
            # Create data point
            data_point = SignalDataPoint(
                timestamp=timestamp,
                value=float(value),
                confidence=float(confidence),
                extraction_method=extraction_method,
                source_text_hash=source_text_hash,
                metadata=tuple(metadata_pairs)
            )
            data_points.append(data_point)
        
        # Sort by timestamp (chronological order)
        data_points.sort(key=lambda dp: dp.timestamp)
        
        return data_points
    
    def _generate_timeseries_id(self, entity_id: str, signal_name: str, timestamp: datetime) -> str:
        """
        Generate unique timeseries ID.
        
        Format: signal_ts_<entity>_<signal>_<timestamp>
        Example: signal_ts_AAPL_sentiment_valence_20260211_140000
        
        Args:
            entity_id: Entity identifier
            signal_name: Signal name
            timestamp: Archive timestamp
            
        Returns:
            Unique timeseries ID
        """
        # Sanitize entity_id (remove non-alphanumeric)
        entity_safe = "".join(c if c.isalnum() else "_" for c in entity_id)
        
        # Format timestamp
        ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        return f"signal_ts_{entity_safe}_{signal_name}_{ts_str}"


def archive_signal_timeseries(
    entity_id: str,
    signal_results: List[Dict[str, Any]],
    vertical: str,
    schema_version: str = "2.1",
    retention_days: int = 365,
    correlation_id: Optional[str] = None
) -> SignalTimeseries:
    """
    Convenience function for creating signal timeseries archives.
    
    Args:
        entity_id: Entity identifier (domain-agnostic)
        signal_results: List of Babel Gardens signal extraction results
        vertical: Vertical domain ("finance", "cybersecurity", "healthcare", etc.)
        schema_version: Babel Gardens schema version (default: "2.1")
        retention_days: Retention period in days (default: 365)
        correlation_id: Optional correlation ID
        
    Returns:
        SignalTimeseries ready for archival
        
    Example:
        # Archive sentiment signals for AAPL
        timeseries = archive_signal_timeseries(
            entity_id="AAPL",
            signal_results=[
                {"signal_name": "sentiment_valence", "value": 0.65, "confidence": 0.88, ...},
                {"signal_name": "sentiment_valence", "value": 0.72, "confidence": 0.91, ...},
            ],
            vertical="finance"
        )
    """
    archivist = SignalArchivist()
    
    event = {
        "operation": "archive_signal_timeseries",
        "entity_id": entity_id,
        "signal_results": signal_results,
        "vertical": vertical,
        "schema_version": schema_version,
        "retention_days": retention_days,
        "correlation_id": correlation_id or f"sig_archive_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    }
    
    return archivist.process(event)
