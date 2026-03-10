#!/usr/bin/env python3
"""
🎯 Listener Metrics Server
Simple HTTP server to expose Prometheus metrics for listener services

Usage:
    from core.synaptic_conclave.monitoring.metrics_server import start_metrics_server
    
    # In listener main():
    start_metrics_server(port=8019)  # Runs in separate thread
"""

import os
from prometheus_client import start_http_server
import structlog

logger = structlog.get_logger("synaptic_conclave.metrics_server")


def start_metrics_server(port: int = None, addr: str = '0.0.0.0'):
    """
    Start Prometheus metrics HTTP server in separate thread.
    
    Args:
        port: HTTP port (default from METRICS_PORT env or 8019)
        addr: Bind address (default 0.0.0.0)
    
    Exposes:
        GET /metrics - Prometheus metrics endpoint
    
    Note: Runs in daemon thread, doesn't block main event loop
    """
    port = port or int(os.getenv('METRICS_PORT', '8019'))
    
    try:
        start_http_server(port, addr=addr)
        logger.info("🎯 Metrics server started", 
                   endpoint=f"http://{addr}:{port}/metrics",
                   prometheus_compatible=True)
    except OSError as e:
        if "Address already in use" in str(e):
            logger.warning(f"⚠️ Metrics port {port} already in use (likely already started)")
        else:
            logger.error(f"❌ Failed to start metrics server on port {port}: {e}")
            raise
