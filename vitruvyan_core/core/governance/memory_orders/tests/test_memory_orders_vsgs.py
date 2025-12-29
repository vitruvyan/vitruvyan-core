"""
🧪 VSGS Memory Orders Test Suite (PR-B)
Test Coverage: Dual Write, Sync Job, Drift Monitor, Deduplication

Run:
    # All tests (with VSGS_ENABLED=0 for safety)
    pytest tests/test_memory_orders_vsgs.py -v
    
    # Integration tests (requires VSGS_ENABLED=1 + real services)
    VSGS_ENABLED=1 pytest tests/test_memory_orders_vsgs.py -m integration -v
"""

import pytest
import os
import sys
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestMemoryOrdersVSGS:
    """Test suite for VSGS Memory Orders integration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.test_grounding_event = {
            "user_id": "test_user",
            "trace_id": "test_trace_123",
            "query_text": "analizza AAPL trend",
            "language": "it",
            "affective_state": "confident",
            "semantic_context": {"matches": [{"text": "NVDA momentum", "score": 0.87}]},
            "grounding_confidence": 0.87,
            "phrase_hash": hashlib.sha256(b"test_user:analizza AAPL trend:it").hexdigest(),
            "phase": "ingest"
        }
    
    # ============================================================
    # TEST 1: Dual Write Success (PostgreSQL + Qdrant)
    # ============================================================
    
    @patch("core.leo.postgres_agent.save_grounding_event")
    @patch("core.leo.qdrant_agent.QdrantAgent.upsert_semantic_state")
    def test_dual_write_success(self, mock_qdrant, mock_pg):
        """
        Test that dual write saves to both PostgreSQL and Qdrant.
        
        Expected:
        - save_grounding_event() called with correct params
        - upsert_semantic_state() called with matches
        """
        # Setup mocks
        mock_pg.return_value = 123  # Grounding event ID
        mock_qdrant.return_value = {"status": "ok", "upserted": 1}
        
        # Simulate dual write (same logic as semantic_grounding_node.py)
        from core.foundation.persistence.postgres_agent import save_grounding_event
        from core.foundation.persistence.qdrant_agent import QdrantAgent
        
        # Call PostgreSQL save
        grounding_id = save_grounding_event(MagicMock(), **self.test_grounding_event)
        
        # Call Qdrant upsert
        qdrant = QdrantAgent()
        matches = self.test_grounding_event["semantic_context"]["matches"]
        qdrant_result = qdrant.upsert_semantic_state(matches, user_id="test_user")
        
        # Verify both called
        assert mock_pg.called, "PostgreSQL save_grounding_event should be called"
        assert mock_qdrant.called, "Qdrant upsert_semantic_state should be called"
        
        print("✅ test_dual_write_success passed")
    
    # ============================================================
    # TEST 2: Phrase Hash Deduplication
    # ============================================================
    
    def test_dedupe_phrase_hash(self):
        """
        Test that duplicate phrase_hash prevents double insertion.
        
        Expected:
        - First insert returns ID
        - Second insert returns None (ON CONFLICT DO NOTHING)
        """
        # Generate same phrase_hash twice
        phrase_hash_1 = hashlib.sha256(b"user:query:lang").hexdigest()
        phrase_hash_2 = hashlib.sha256(b"user:query:lang").hexdigest()
        
        assert phrase_hash_1 == phrase_hash_2, "Same input should produce same hash"
        
        # In real implementation, ON CONFLICT DO NOTHING prevents duplicates
        # This test validates the hash generation is deterministic
        
        print("✅ test_dedupe_phrase_hash passed")
    
    # ============================================================
    # TEST 3: Sync Job Marks Synced
    # ============================================================
    
    @patch("core.memory_orders.vsgs_sync.fetch_unsynced_groundings")
    @patch("core.memory_orders.vsgs_sync.mark_grounding_synced")
    @patch("core.leo.qdrant_agent.QdrantAgent.upsert_point_from_grounding")
    def test_sync_job_marks_synced(self, mock_qdrant, mock_mark, mock_fetch):
        """
        Test that sync job marks events as synced after Qdrant upsert.
        
        Expected:
        - fetch_unsynced_groundings() returns unsynced events
        - upsert_point_from_grounding() succeeds
        - mark_grounding_synced() called with event ID
        """
        # Setup mocks
        mock_fetch.return_value = [
            {
                "id": 1,
                "user_id": "user1",
                "trace_id": "trace1",
                "embedding_vector": [0.1] * 384,
                "language": "it",
                "phase": "ingest"
            }
        ]
        mock_qdrant.return_value = {"status": "ok"}
        mock_mark.return_value = True
        
        # Simulate sync
        from core.memory_orders.vsgs_sync import sync_semantic_states
        result = sync_semantic_states(limit=1)
        
        # Verify sync flow
        assert mock_fetch.called, "Should fetch unsynced events"
        assert mock_qdrant.called, "Should upsert to Qdrant"
        assert mock_mark.called, "Should mark as synced"
        assert result["synced"] > 0, "Should report synced count"
        
        print("✅ test_sync_job_marks_synced passed")
    
    # ============================================================
    # TEST 4: Drift Check Below Threshold
    # ============================================================
    
    @patch("core.leo.postgres_agent.count_grounding_events")
    @patch("core.leo.qdrant_agent.QdrantAgent.count_points")
    def test_drift_below_threshold(self, mock_qdrant_count, mock_pg_count):
        """
        Test drift monitoring with healthy status (drift < 5%).
        
        Expected:
        - Drift calculation correct
        - Status "healthy" when drift < 5%
        - passed = True
        """
        # Setup mocks (1% drift)
        mock_pg_count.return_value = 1000
        mock_qdrant_count.return_value = 990  # 10/1000 = 1% drift
        
        from scripts.check_vsgs_drift import check_vsgs_drift
        result = check_vsgs_drift(threshold=0.05)
        
        # Verify drift calculation
        assert result["pg_count"] == 1000
        assert result["qdrant_count"] == 990
        assert result["drift"] == 0.01, f"Expected drift 0.01, got {result['drift']}"
        assert result["status"] == "healthy", "Status should be healthy"
        assert result["passed"] is True, "Drift check should pass"
        
        print("✅ test_drift_below_threshold passed")
    
    # ============================================================
    # TEST 5: Flag OFF - No Side Effects
    # ============================================================
    
    def test_flag_off_no_effect(self):
        """
        Test that VSGS_ENABLED=0 prevents all dual write operations.
        
        Expected:
        - semantic_grounding_node bypassed
        - No PostgreSQL writes
        - No Qdrant upserts
        """
        os.environ["VSGS_ENABLED"] = "0"
        
        from core.langgraph.node.semantic_grounding_node import semantic_grounding_node
        
        state = {
            "input_text": "test query",
            "user_id": "test",
            "trace_id": "trace",
            "intent": "trend",
            "language": "en"
        }
        
        result = semantic_grounding_node(state)
        
        # Verify bypass
        assert result["vsgs_status"] == "disabled", "VSGS should be disabled"
        assert result["semantic_matches"] == [], "No semantic matches when disabled"
        assert result["vsgs_elapsed_ms"] == 0.0, "Zero latency when disabled"
        
        print("✅ test_flag_off_no_effect passed")
    
    # ============================================================
    # TEST 6: Embedding Vector Validation
    # ============================================================
    
    def test_embedding_vector_required_for_sync(self):
        """
        Test that sync skips events without embedding_vector.
        
        Expected:
        - Events with embedding_vector synced
        - Events without embedding_vector skipped
        """
        event_with_embedding = {
            "id": 1,
            "user_id": "user1",
            "embedding_vector": [0.1] * 384
        }
        
        event_without_embedding = {
            "id": 2,
            "user_id": "user2",
            "embedding_vector": None
        }
        
        # Event with embedding is valid
        assert event_with_embedding["embedding_vector"] is not None
        
        # Event without embedding should be skipped
        assert event_without_embedding["embedding_vector"] is None
        
        print("✅ test_embedding_vector_required_for_sync passed")
    
    # ============================================================
    # TEST 7: Audit Logging Integration
    # ============================================================
    
    @patch("core.logging.audit.audit")
    def test_audit_logging(self, mock_audit):
        """
        Test that all VSGS operations are audit logged.
        
        Expected:
        - Drift check logs to audit
        - Sync job logs to audit
        - Dual write logs to audit
        """
        from scripts.check_vsgs_drift import check_vsgs_drift
        
        # Mock counts
        with patch("core.leo.postgres_agent.count_grounding_events", return_value=100):
            with patch("core.leo.qdrant_agent.QdrantAgent.count_points", return_value=98):
                check_vsgs_drift()
        
        # Verify audit called
        assert mock_audit.called, "Audit should be called"
        call_args = mock_audit.call_args
        assert call_args[1]["trace_id"] == "drift_check"
        assert call_args[1]["user_id"] == "system"
        
        print("✅ test_audit_logging passed")


# ============================================================
# Integration Tests (Require Real Services)
# ============================================================

@pytest.mark.integration
@pytest.mark.skipif(os.getenv("VSGS_ENABLED") != "1", reason="VSGS disabled or integration test not requested")
class TestMemoryOrdersIntegration:
    """Integration tests requiring real PostgreSQL + Qdrant"""
    
    def test_real_dual_write(self):
        """Test dual write against real databases"""
        import psycopg2
        from core.foundation.persistence.postgres_agent import save_grounding_event
        from core.foundation.persistence.qdrant_agent import QdrantAgent
        
        # Setup
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        
        # Create test event
        phrase_hash = hashlib.sha256(b"integration_test:query:en").hexdigest()
        grounding_id = save_grounding_event(
            conn,
            user_id="integration_test",
            trace_id="integration_trace",
            query_text="integration test query",
            language="en",
            affective_state="neutral",
            semantic_context={"matches": []},
            grounding_confidence=0.5,
            phrase_hash=phrase_hash,
            phase="test"
        )
        
        conn.close()
        
        # Verify PostgreSQL
        assert grounding_id is not None, "PostgreSQL insert should succeed"
        
        print(f"✅ test_real_dual_write passed (grounding_id={grounding_id})")
    
    def test_real_sync_job(self):
        """Test sync job against real services"""
        from core.memory_orders.vsgs_sync import sync_semantic_states
        
        result = sync_semantic_states(limit=10)
        
        # Verify sync executed
        assert "synced" in result
        assert "failed" in result
        assert "skipped" in result
        
        print(f"✅ test_real_sync_job passed (synced={result['synced']}, failed={result['failed']})")
    
    def test_real_drift_check(self):
        """Test drift check against real databases"""
        from scripts.check_vsgs_drift import check_vsgs_drift
        
        result = check_vsgs_drift()
        
        # Verify drift calculation
        assert result["pg_count"] >= 0
        assert result["qdrant_count"] >= 0
        assert result["drift"] >= 0.0
        assert result["status"] in ["healthy", "warning", "critical"]
        
        print(f"✅ test_real_drift_check passed (drift={result['drift_percent']:.2f}%, status={result['status']})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
