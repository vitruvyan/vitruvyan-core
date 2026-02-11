"""
Vault Keepers — Signal Archive Domain Objects

Immutable domain objects for long-term signal timeseries storage.
Integrates with Babel Gardens v2.1 SignalSchema.

Sacred Order: Truth (Memory & Archival)
Layer: Foundational (LIVELLO 1)
"""
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class SignalDataPoint:
    """
    Immutable single data point in a signal timeseries.
    
    Attributes:
        timestamp: ISO 8601 timestamp of signal extraction
        value: Signal value (numeric)
        confidence: Confidence score [0,1]
        extraction_method: How signal was extracted ("model:finbert", "heuristic:volatility_calc")
        source_text_hash: SHA256 of source text (for traceability, optional)
        metadata: Additional context (tuple of key-value pairs)
    
    Example:
        SignalDataPoint(
            timestamp="2026-02-11T14:00:00Z",
            value=0.65,
            confidence=0.88,
            extraction_method="model:finbert",
            source_text_hash="abc123...",
            metadata=(("entity_id", "AAPL"), ("vertical", "finance"))
        )
    """
    timestamp: str
    value: float
    confidence: float
    extraction_method: str
    source_text_hash: Optional[str] = None
    metadata: Tuple[Tuple[str, str], ...] = ()  # Frozen: tuple of (key, value) pairs

    def __post_init__(self):
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be [0,1], got {self.confidence}")


@dataclass(frozen=True)
class SignalTimeseries:
    """
    Immutable timeseries of signal values for a specific entity.
    
    Attributes:
        timeseries_id: Unique identifier (format: "signal_ts_<entity>_<signal>_<timestamp>")
        entity_id: Entity this signal pertains to (domain-agnostic: ticker, IP, vessel IMO, patient ID, etc.)
        signal_name: Signal being tracked (domain-agnostic: sentiment_valence, threat_severity, etc.)
        vertical: Vertical domain ("finance", "cybersecurity", "maritime", "healthcare", etc.)
        data_points: Tuple of SignalDataPoint (chronologically ordered)
        schema_version: Babel Gardens SignalSchema version used
        retention_until: ISO 8601 expiration date (when to purge old data)
        archive_timestamp: ISO 8601 when this archive was created
        metadata: Additional context (tuple of key-value pairs)
    
    Design Principles:
        - Domain-agnostic: Works with ANY vertical (finance, cyber, healthcare, sports, IoT, etc.)
        - Immutable: Data points cannot be modified after creation
        - Traceable: Each point links to extraction method + source text hash
        - Compressible: Tuple of small dataclasses for efficient storage
    
    Example (Finance):
        SignalTimeseries(
            timeseries_id="signal_ts_AAPL_sentiment_valence_20260211",
            entity_id="AAPL",
            signal_name="sentiment_valence",
            vertical="finance",
            data_points=(
                SignalDataPoint(timestamp="2026-02-11T10:00:00Z", value=0.65, confidence=0.88, ...),
                SignalDataPoint(timestamp="2026-02-11T12:00:00Z", value=0.72, confidence=0.91, ...),
            ),
            schema_version="2.1",
            retention_until="2027-02-11T00:00:00Z",
            archive_timestamp="2026-02-11T23:59:59Z"
        )
    
    Example (Cybersecurity):
        SignalTimeseries(
            entity_id="192.168.1.100",
            signal_name="threat_severity",
            vertical="cybersecurity",
            data_points=(
                SignalDataPoint(timestamp="2026-02-11T10:00:00Z", value=0.42, confidence=0.95, ...),
                SignalDataPoint(timestamp="2026-02-11T12:00:00Z", value=0.89, confidence=0.87, ...),
            ),
            ...
        )
    
    Example (Healthcare):
        SignalTimeseries(
            entity_id="patient_12345",
            signal_name="diagnostic_confidence",
            vertical="healthcare",
            data_points=(
                SignalDataPoint(timestamp="2026-02-11T08:00:00Z", value=0.73, confidence=0.92, ...),
                SignalDataPoint(timestamp="2026-02-11T14:00:00Z", value=0.81, confidence=0.94, ...),
            ),
            ...
        )
    """
    timeseries_id: str
    entity_id: str
    signal_name: str
    vertical: str
    data_points: Tuple[SignalDataPoint, ...]
    schema_version: str
    retention_until: str
    archive_timestamp: str
    metadata: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self):
        if not self.timeseries_id:
            raise ValueError("timeseries_id cannot be empty")
        if not self.entity_id:
            raise ValueError("entity_id cannot be empty")
        if not self.signal_name:
            raise ValueError("signal_name cannot be empty")
        if not self.vertical:
            raise ValueError("vertical cannot be empty")
        if not self.data_points:
            raise ValueError("data_points cannot be empty (must have at least 1 point)")
        
        # Validate all data points are SignalDataPoint instances
        for point in self.data_points:
            if not isinstance(point, SignalDataPoint):
                raise TypeError(f"All data_points must be SignalDataPoint, got {type(point)}")
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict for storage."""
        return {
            "timeseries_id": self.timeseries_id,
            "entity_id": self.entity_id,
            "signal_name": self.signal_name,
            "vertical": self.vertical,
            "data_points": [
                {
                    "timestamp": point.timestamp,
                    "value": point.value,
                    "confidence": point.confidence,
                    "extraction_method": point.extraction_method,
                    "source_text_hash": point.source_text_hash,
                    "metadata": dict(point.metadata) if point.metadata else {}
                }
                for point in self.data_points
            ],
            "schema_version": self.schema_version,
            "retention_until": self.retention_until,
            "archive_timestamp": self.archive_timestamp,
            "metadata": dict(self.metadata) if self.metadata else {}
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SignalTimeseries":
        """Reconstruct from stored dict."""
        data_points = tuple(
            SignalDataPoint(
                timestamp=point["timestamp"],
                value=point["value"],
                confidence=point["confidence"],
                extraction_method=point["extraction_method"],
                source_text_hash=point.get("source_text_hash"),
                metadata=tuple(point.get("metadata", {}).items())
            )
            for point in data["data_points"]
        )
        
        return cls(
            timeseries_id=data["timeseries_id"],
            entity_id=data["entity_id"],
            signal_name=data["signal_name"],
            vertical=data["vertical"],
            data_points=data_points,
            schema_version=data["schema_version"],
            retention_until=data["retention_until"],
            archive_timestamp=data["archive_timestamp"],
            metadata=tuple(data.get("metadata", {}).items())
        )


@dataclass(frozen=True)
class SignalArchiveQuery:
    """
    Immutable query specification for retrieving signal timeseries.
    
    Attributes:
        entity_id: Entity to query (required)
        signal_name: Signal name to filter by (optional - if None, returns all signals)
        vertical: Vertical domain to filter by (optional)
        start_time: ISO 8601 start of time range (optional - if None, from beginning)
        end_time: ISO 8601 end of time range (optional - if None, until now)
        min_confidence: Minimum confidence threshold [0,1] (optional)
        limit: Maximum number of timeseries to return (optional)
    
    Example:
        # Query all sentiment signals for AAPL in February 2026
        SignalArchiveQuery(
            entity_id="AAPL",
            signal_name="sentiment_valence",
            vertical="finance",
            start_time="2026-02-01T00:00:00Z",
            end_time="2026-02-28T23:59:59Z",
            min_confidence=0.8
        )
    """
    entity_id: str
    signal_name: Optional[str] = None
    vertical: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    min_confidence: Optional[float] = None
    limit: Optional[int] = None

    def __post_init__(self):
        if not self.entity_id:
            raise ValueError("entity_id is required")
        if self.min_confidence is not None and not (0.0 <= self.min_confidence <= 1.0):
            raise ValueError(f"min_confidence must be [0,1], got {self.min_confidence}")
        if self.limit is not None and self.limit < 1:
            raise ValueError(f"limit must be >= 1, got {self.limit}")
