"""
Sacred Monitoring module for Orthodoxy Wardens.
Contains health checks and Synaptic Conclave integration utilities.
"""

from api_orthodoxy_wardens.monitoring.health import (
    setup_synaptic_conclave_listeners
)

__all__ = ["setup_synaptic_conclave_listeners"]
