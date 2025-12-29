"""
vitruvyan_os.services.governance.api_orthodoxy_wardens
=======================================================

FastAPI service for Orthodoxy Wardens audit operations.

Port: 8006
Sacred Order: Truth/Governance (Order V)

Endpoints:
----------
- POST /orthodoxy/validate_schema: Validate database schema
- POST /orthodoxy/audit: Perform integrity audit
- GET /orthodoxy/status: System compliance status
- GET /orthodoxy/violations: List detected violations
- GET /health: Health check
- GET /metrics: Prometheus metrics

The Orthodoxy Wardens ensure epistemic integrity through automated
validation and compliance monitoring.

Metrics:
--------
- orthodoxy_validations_total (Counter)
- orthodoxy_violations_detected (Counter)
- orthodoxy_audit_duration_seconds (Histogram)

Dependencies:
-------------
- vitruvyan_os.core.governance.orthodoxy_wardens: Core validation logic
- vitruvyan_os.core.foundation.persistence: PostgresAgent
- vitruvyan_os.core.foundation.cognitive_bus: Event handling

Version: 2.0.0
"""

__version__ = '2.0.0'
__port__ = 8006
__sacred_order__ = 'Truth/Governance (Order V)'
