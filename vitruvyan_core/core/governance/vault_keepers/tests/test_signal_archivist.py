"""
Vault Keepers — Signal Archivist Tests

Unit tests for SignalArchivist consumer (LIVELLO 1 pure logic).
No I/O, no external dependencies.

Sacred Order: Truth (Memory & Archival)
Layer: Testing
"""

import pytest
from datetime import datetime

from vitruvyan_core.core.governance.vault_keepers.consumers.signal_archivist import (
    SignalArchivist,
    archive_signal_timeseries
)
from vitruvyan_core.core.governance.vault_keepers.domain.signal_archive import (
    SignalTimeseries,
    SignalDataPoint
)


class TestSignalArchivist:
    """Test SignalArchivist pure logic"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.archivist = SignalArchivist()
    
    def test_role_name(self):
        """Test role identification"""
        assert self.archivist.role_name == "signal_archivist"
        assert "signal timeseries" in self.archivist.description.lower()
    
    def test_can_handle_signal_timeseries(self):
        """Test event routing"""
        event = {"operation": "archive_signal_timeseries", "entity_id": "ENTITY_A"}
        assert self.archivist.can_handle(event) is True
    
    def test_cannot_handle_other_operations(self):
        """Test event routing rejection"""
        event = {"operation": "backup"}
        assert self.archivist.can_handle(event) is False
    
    def test_archive_finance_signals(self):
        """Test archiving finance signals (sentiment_valence)"""
        event = {
            "operation": "archive_signal_timeseries",
            "entity_id": "ENTITY_A",
            "signal_results": [
                {
                    "signal_name": "sentiment_valence",
                    "value": 0.65,
                    "confidence": 0.88,
                    "extraction_trace": {
                        "method": "model:finbert",
                        "timestamp": "2026-02-11T10:00:00Z",
                        "model_version": "finbert-0.4"
                    },
                    "source_text": "Apple announced record earnings..."
                },
                {
                    "signal_name": "sentiment_valence",
                    "value": 0.72,
                    "confidence": 0.91,
                    "extraction_trace": {
                        "method": "model:finbert",
                        "timestamp": "2026-02-11T12:00:00Z",
                        "model_version": "finbert-0.4"
                    },
                    "source_text": "Strong demand for iPhone 15..."
                }
            ],
            "vertical": "finance",
            "schema_version": "2.1",
            "retention_days": 365,
            "correlation_id": "test_finance_001"
        }
        
        timeseries = self.archivist.process(event)
        
        # Validate timeseries structure
        assert isinstance(timeseries, SignalTimeseries)
        assert timeseries.entity_id == "ENTITY_A"
        assert timeseries.signal_name == "sentiment_valence"
        assert timeseries.vertical == "finance"
        assert timeseries.schema_version == "2.1"
        assert len(timeseries.data_points) == 2
        
        # Validate data points
        point1 = timeseries.data_points[0]
        assert isinstance(point1, SignalDataPoint)
        assert point1.value == 0.65
        assert point1.confidence == 0.88
        assert point1.extraction_method == "model:finbert"
        assert point1.timestamp == "2026-02-11T10:00:00Z"
        assert point1.source_text_hash is not None  # SHA256 hash exists
        
        point2 = timeseries.data_points[1]
        assert point2.value == 0.72
        assert point2.confidence == 0.91
        assert point2.timestamp == "2026-02-11T12:00:00Z"
        
        # Validate chronological order
        assert point1.timestamp < point2.timestamp
    
    def test_archive_cybersecurity_signals(self):
        """Test archiving cybersecurity signals (threat_severity)"""
        event = {
            "operation": "archive_signal_timeseries",
            "entity_id": "192.168.1.100",
            "signal_results": [
                {
                    "signal_name": "threat_severity",
                    "value": 0.42,
                    "confidence": 0.95,
                    "extraction_trace": {
                        "method": "model:secbert",
                        "timestamp": "2026-02-11T10:00:00Z"
                    }
                },
                {
                    "signal_name": "threat_severity",
                    "value": 0.89,
                    "confidence": 0.87,
                    "extraction_trace": {
                        "method": "model:secbert",
                        "timestamp": "2026-02-11T12:00:00Z"
                    }
                }
            ],
            "vertical": "cybersecurity",
            "schema_version": "2.1"
        }
        
        timeseries = self.archivist.process(event)
        
        assert timeseries.entity_id == "192.168.1.100"
        assert timeseries.signal_name == "threat_severity"
        assert timeseries.vertical == "cybersecurity"
        assert len(timeseries.data_points) == 2
        
        # Validate threat escalation
        assert timeseries.data_points[0].value == 0.42  # Low threat
        assert timeseries.data_points[1].value == 0.89  # High threat
    
    def test_archive_healthcare_signals(self):
        """Test archiving healthcare signals (diagnostic_confidence)"""
        event = {
            "operation": "archive_signal_timeseries",
            "entity_id": "patient_12345",
            "signal_results": [
                {
                    "signal_name": "diagnostic_confidence",
                    "value": 0.73,
                    "confidence": 0.92,
                    "extraction_trace": {
                        "method": "model:bioclinicalbert",
                        "timestamp": "2026-02-11T08:00:00Z"
                    }
                },
                {
                    "signal_name": "diagnostic_confidence",
                    "value": 0.81,
                    "confidence": 0.94,
                    "extraction_trace": {
                        "method": "model:bioclinicalbert",
                        "timestamp": "2026-02-11T14:00:00Z"
                    }
                }
            ],
            "vertical": "healthcare",
            "schema_version": "2.1",
            "retention_days": 2555  # 7 years (HIPAA compliance)
        }
        
        timeseries = self.archivist.process(event)
        
        assert timeseries.entity_id == "patient_12345"
        assert timeseries.signal_name == "diagnostic_confidence"
        assert timeseries.vertical == "healthcare"
        assert len(timeseries.data_points) == 2
        
        # Validate diagnostic improvement
        assert timeseries.data_points[0].value == 0.73
        assert timeseries.data_points[1].value == 0.81
    
    def test_mixed_signal_names_rejected(self):
        """Test that mixed signal names in batch are rejected"""
        event = {
            "operation": "archive_signal_timeseries",
            "entity_id": "ENTITY_A",
            "signal_results": [
                {"signal_name": "sentiment_valence", "value": 0.65, "confidence": 0.88},
                {"signal_name": "market_fear_index", "value": 0.35, "confidence": 0.90}  # DIFFERENT signal
            ],
            "vertical": "finance"
        }
        
        with pytest.raises(ValueError, match="Mixed signal names"):
            self.archivist.process(event)
    
    def test_empty_signal_results_rejected(self):
        """Test that empty signal results are rejected"""
        event = {
            "operation": "archive_signal_timeseries",
            "entity_id": "ENTITY_A",
            "signal_results": [],
            "vertical": "finance"
        }
        
        with pytest.raises(ValueError, match="signal_results cannot be empty"):
            self.archivist.process(event)
    
    def test_missing_entity_id_rejected(self):
        """Test that missing entity_id is rejected"""
        event = {
            "operation": "archive_signal_timeseries",
            "signal_results": [{"signal_name": "sentiment_valence", "value": 0.65}],
            "vertical": "finance"
        }
        
        with pytest.raises(ValueError, match="entity_id is required"):
            self.archivist.process(event)
    
    def test_timeseries_id_generation(self):
        """Test unique timeseries ID generation"""
        event = {
            "operation": "archive_signal_timeseries",
            "entity_id": "ENTITY_A",
            "signal_results": [
                {"signal_name": "sentiment_valence", "value": 0.65, "confidence": 0.88}
            ],
            "vertical": "finance"
        }
        
        timeseries = self.archivist.process(event)
        
        # Validate ID format: signal_ts_<entity>_<signal>_<timestamp>
        assert timeseries.timeseries_id.startswith("signal_ts_ENTITY_A_sentiment_valence_")
        assert len(timeseries.timeseries_id) > 30  # Includes timestamp
    
    def test_serialization_roundtrip(self):
        """Test to_dict() and from_dict() roundtrip"""
        event = {
            "operation": "archive_signal_timeseries",
            "entity_id": "ENTITY_A",
            "signal_results": [
                {
                    "signal_name": "sentiment_valence",
                    "value": 0.65,
                    "confidence": 0.88,
                    "extraction_trace": {
                        "method": "model:finbert",
                        "timestamp": "2026-02-11T10:00:00Z"
                    }
                }
            ],
            "vertical": "finance"
        }
        
        original = self.archivist.process(event)
        
        # Serialize to dict
        data = original.to_dict()
        assert isinstance(data, dict)
        assert data["entity_id"] == "ENTITY_A"
        assert data["signal_name"] == "sentiment_valence"
        assert len(data["data_points"]) == 1
        
        # Deserialize back
        reconstructed = SignalTimeseries.from_dict(data)
        
        # Validate equivalence
        assert reconstructed.entity_id == original.entity_id
        assert reconstructed.signal_name == original.signal_name
        assert reconstructed.vertical == original.vertical
        assert len(reconstructed.data_points) == len(original.data_points)
        assert reconstructed.data_points[0].value == original.data_points[0].value


class TestConvenienceFunction:
    """Test archive_signal_timeseries() convenience function"""
    
    def test_convenience_function_finance(self):
        """Test convenience function with finance signals"""
        signal_results = [
            {
                "signal_name": "sentiment_valence",
                "value": 0.65,
                "confidence": 0.88,
                "extraction_trace": {
                    "method": "model:finbert",
                    "timestamp": "2026-02-11T10:00:00Z"
                }
            }
        ]
        
        timeseries = archive_signal_timeseries(
            entity_id="ENTITY_A",
            signal_results=signal_results,
            vertical="finance"
        )
        
        assert isinstance(timeseries, SignalTimeseries)
        assert timeseries.entity_id == "ENTITY_A"
        assert timeseries.signal_name == "sentiment_valence"
        assert timeseries.vertical == "finance"
        assert timeseries.schema_version == "2.1"  # Default
    
    def test_convenience_function_custom_retention(self):
        """Test convenience function with custom retention"""
        signal_results = [
            {"signal_name": "threat_severity", "value": 0.42, "confidence": 0.95}
        ]
        
        timeseries = archive_signal_timeseries(
            entity_id="192.168.1.100",
            signal_results=signal_results,
            vertical="cybersecurity",
            retention_days=90  # 3 months
        )
        
        assert timeseries.vertical == "cybersecurity"
        # Retention should be ~90 days from now (not exact due to timing)
        assert "2026-05" in timeseries.retention_until  # ~3 months later


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
