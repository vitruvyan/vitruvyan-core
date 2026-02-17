from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, Query

from .contracts import EdgeEnvelopeIn, EdgeEnvelopeStored
from .outbox import SQLiteOutbox
from .relay import CoreOculusPrimeRelay


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

APP_VERSION = "0.1.0"
OUTBOX_PATH = os.getenv("EDGE_OUTBOX_PATH", "/tmp/vitruvyan_edge_outbox.db")
CORE_OCULUS_PRIME_BASE_URL = os.getenv(
    "CORE_OCULUS_PRIME_BASE_URL",
    os.getenv("CORE_INTAKE_BASE_URL", "http://localhost:9050"),
)
HTTP_TIMEOUT_SEC = int(os.getenv("EDGE_HTTP_TIMEOUT_SEC", "10"))
REPLAY_BATCH_SIZE = int(os.getenv("EDGE_REPLAY_BATCH_SIZE", "50"))
CORE_EDGE_API_TOKEN = os.getenv("CORE_EDGE_API_TOKEN")

app = FastAPI(
    title="Vitruvyan Edge Gateway",
    description="Offline-first edge ingress gateway for Intake interoperability",
    version=APP_VERSION,
)

outbox = SQLiteOutbox(OUTBOX_PATH)
relay = CoreOculusPrimeRelay(
    base_url=CORE_OCULUS_PRIME_BASE_URL,
    timeout_sec=HTTP_TIMEOUT_SEC,
    token=CORE_EDGE_API_TOKEN,
)

_metrics: Dict[str, int] = {
    "accepted_total": 0,
    "relay_success_total": 0,
    "relay_failed_total": 0,
    "replay_runs_total": 0,
}
_last_replay_utc: str | None = None


def _attempt_relay(record_id: int, envelope: EdgeEnvelopeStored) -> Dict[str, Any]:
    outbox.mark_attempt(record_id)
    ok, details = relay.submit(envelope)
    if ok:
        outbox.mark_sent(record_id)
        _metrics["relay_success_total"] += 1
        return {"status": "sent", "details": details}

    outbox.mark_pending(record_id)
    _metrics["relay_failed_total"] += 1
    return {"status": "pending", "details": details}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "service": "vitruvyan_edge_gateway",
        "version": APP_VERSION,
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "core_reachable": relay.health(),
        "outbox_path": OUTBOX_PATH,
    }


@app.get("/status")
def status() -> Dict[str, Any]:
    return {
        "service": "vitruvyan_edge_gateway",
        "version": APP_VERSION,
        "core_oculus_prime_base_url": CORE_OCULUS_PRIME_BASE_URL,
        "core_intake_base_url": CORE_OCULUS_PRIME_BASE_URL,
        "pending_count": outbox.pending_count(),
        "sent_count": outbox.sent_count(),
        "last_replay_utc": _last_replay_utc,
        "metrics": _metrics,
    }


@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    return {
        "accepted_total": _metrics["accepted_total"],
        "relay_success_total": _metrics["relay_success_total"],
        "relay_failed_total": _metrics["relay_failed_total"],
        "replay_runs_total": _metrics["replay_runs_total"],
        "pending_count": outbox.pending_count(),
        "sent_count": outbox.sent_count(),
    }


@app.post("/api/edge/oculus-prime")
@app.post("/api/edge/intake", deprecated=True)
def enqueue_intake(payload: EdgeEnvelopeIn) -> Dict[str, Any]:
    envelope = EdgeEnvelopeStored.from_input(payload)
    outbox_id = outbox.enqueue(envelope)
    _metrics["accepted_total"] += 1

    relay_result = _attempt_relay(outbox_id, envelope)
    return {
        "status": "accepted",
        "outbox_id": outbox_id,
        "envelope_id": envelope.envelope_id,
        "relay": relay_result,
    }


@app.post("/api/edge/replay")
def replay_pending(limit: int = Query(REPLAY_BATCH_SIZE, ge=1, le=500)) -> Dict[str, Any]:
    global _last_replay_utc
    _metrics["replay_runs_total"] += 1
    _last_replay_utc = datetime.now(timezone.utc).isoformat()

    records = outbox.fetch_pending(limit=limit)
    results = []
    sent = 0
    pending = 0

    for record in records:
        result = _attempt_relay(record.id, record.envelope)
        results.append(
            {
                "outbox_id": record.id,
                "envelope_id": record.envelope.envelope_id,
                "status": result["status"],
                "details": result["details"],
            }
        )
        if result["status"] == "sent":
            sent += 1
        else:
            pending += 1

    return {
        "status": "ok",
        "processed": len(records),
        "sent": sent,
        "still_pending": pending,
        "remaining_pending": outbox.pending_count(),
        "results": results,
    }
