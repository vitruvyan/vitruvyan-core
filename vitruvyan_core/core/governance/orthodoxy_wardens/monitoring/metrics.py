"""
Orthodoxy Wardens — Prometheus Metrics Definitions

Metric counters and histograms for observability.
These are DEFINITIONS only — the service layer registers them with Prometheus.
The foundational layer never collects or exposes metrics directly.

Sacred Order: Truth & Governance
Layer: Foundational (monitoring)
"""

# =============================================================================
# Metric Name Constants
# =============================================================================
# These follow Prometheus naming conventions:
#   <sacred_order>_<domain>_<metric>_<unit>

# Confession metrics
CONFESSIONS_RECEIVED_TOTAL = "orthodoxy_confessions_received_total"
CONFESSIONS_ACCEPTED_TOTAL = "orthodoxy_confessions_accepted_total"
CONFESSIONS_REJECTED_TOTAL = "orthodoxy_confessions_rejected_total"

# Examination metrics
EXAMINATIONS_DURATION_SECONDS = "orthodoxy_examinations_duration_seconds"
EXAMINATIONS_TOTAL = "orthodoxy_examinations_total"

# Finding metrics
FINDINGS_TOTAL = "orthodoxy_findings_total"
FINDINGS_BY_TYPE = "orthodoxy_findings_by_type_total"
FINDINGS_BY_SEVERITY = "orthodoxy_findings_by_severity_total"
FINDINGS_BY_CATEGORY = "orthodoxy_findings_by_category_total"

# Verdict metrics
VERDICTS_TOTAL = "orthodoxy_verdicts_total"
VERDICTS_BY_STATUS = "orthodoxy_verdicts_by_status_total"
VERDICTS_BLESSED_TOTAL = "orthodoxy_verdicts_blessed_total"
VERDICTS_HERETICAL_TOTAL = "orthodoxy_verdicts_heretical_total"
VERDICTS_NON_LIQUET_TOTAL = "orthodoxy_verdicts_non_liquet_total"
VERDICTS_CONFIDENCE_HISTOGRAM = "orthodoxy_verdicts_confidence"

# LogDecision metrics
LOG_DECISIONS_TOTAL = "orthodoxy_log_decisions_total"
LOG_DECISIONS_SKIPPED_TOTAL = "orthodoxy_log_decisions_skipped_total"

# Purification metrics
PURIFICATIONS_REQUESTED_TOTAL = "orthodoxy_purifications_requested_total"
PURIFICATIONS_REPORTED_TOTAL = "orthodoxy_purifications_reported_total"

# Surveillance metrics
SURVEILLANCE_CYCLES_TOTAL = "orthodoxy_surveillance_cycles_total"
SURVEILLANCE_CYCLE_DURATION_SECONDS = "orthodoxy_surveillance_cycle_duration_seconds"


# =============================================================================
# Label definitions — for consistent labeling across metrics
# =============================================================================

FINDING_TYPE_LABELS = ("violation", "warning", "anomaly", "blessing")
SEVERITY_LABELS = ("critical", "high", "medium", "low")
CATEGORY_LABELS = (
    "compliance", "data_quality", "architectural",
    "performance", "hallucination", "epistemic",
)
VERDICT_STATUS_LABELS = (
    "blessed", "purified", "heretical",
    "non_liquet", "clarification_needed",
)
RETENTION_LABELS = ("permanent", "long", "medium", "short", "ephemeral")
