"""
Orthodoxy Wardens — Monitoring

Prometheus metric name constants and label definitions.
The service layer instantiates these as actual Prometheus collectors.
"""

from .metrics import (
    CONFESSIONS_RECEIVED_TOTAL,
    VERDICTS_TOTAL,
    VERDICTS_BY_STATUS,
    FINDINGS_TOTAL,
    FINDINGS_BY_SEVERITY,
    EXAMINATIONS_DURATION_SECONDS,
)

__all__ = [
    "CONFESSIONS_RECEIVED_TOTAL",
    "VERDICTS_TOTAL",
    "VERDICTS_BY_STATUS",
    "FINDINGS_TOTAL",
    "FINDINGS_BY_SEVERITY",
    "EXAMINATIONS_DURATION_SECONDS",
]
