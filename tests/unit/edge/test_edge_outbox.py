import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api_edge_gateway.contracts import EdgeEnvelopeIn, EdgeEnvelopeStored
from services.api_edge_gateway.outbox import SQLiteOutbox


def test_sqlite_outbox_enqueue_and_mark_sent(tmp_path):
    db_path = tmp_path / "edge_outbox.db"
    outbox = SQLiteOutbox(str(db_path))

    envelope_in = EdgeEnvelopeIn(
        source_type="document",
        source_uri="/tmp/example.txt",
        metadata={"sampling_policy_ref": "SAMPPOL-DOC-DEFAULT-V1"},
        correlation_id="trace-test-1",
    )
    envelope = EdgeEnvelopeStored.from_input(envelope_in)

    row_id = outbox.enqueue(envelope)
    assert row_id > 0
    assert outbox.pending_count() == 1

    records = outbox.fetch_pending(limit=10)
    assert len(records) == 1
    assert records[0].envelope.envelope_id == envelope.envelope_id

    outbox.mark_attempt(row_id)
    outbox.mark_sent(row_id)
    assert outbox.pending_count() == 0
    assert outbox.sent_count() == 1
