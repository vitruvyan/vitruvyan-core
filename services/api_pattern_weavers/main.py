"""
Pattern Weavers API Service — FastAPI Application

Epistemic Order: REASON (Semantic Layer)
Port: 8011

Provides REST API for Pattern Weaver semantic contextualization.

Endpoints:
- POST /weave: Main weaving endpoint
- GET /health: Health check
- GET /metrics: Prometheus metrics

Author: Sacred Orders
Created: November 9, 2025
"""

import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Import Pattern Weaver engine and schemas
from core.cognition.pattern_weavers.weaver_engine import PatternWeaverEngine
from core.cognition.pattern_weavers.schemas import WeaveRequest, WeaveResponse

# Initialize FastAPI app
app = FastAPI(
    title="Pattern Weavers API",
    description="Semantic Contextualization for Financial Analysis",
    version="1.0.0"
)

# Initialize Pattern Weaver engine
weaver = PatternWeaverEngine()

# Prometheus metrics
weaver_queries_total = Counter(
    'weaver_queries_total',
    'Total Pattern Weaver queries processed',
    ['status']
)

weaver_latency = Histogram(
    'weaver_query_duration_seconds',
    'Pattern Weaver query processing latency',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

weaver_concepts_found = Counter(
    'weaver_concepts_found_total',
    'Total concepts found by Pattern Weaver'
)


@app.post("/weave", response_model=WeaveResponse)
async def weave_endpoint(request: WeaveRequest):
    """
    Main Pattern Weaver endpoint.
    
    Extracts semantic context (concepts, sectors, regions, risk) from query text.
    
    Args:
        request: WeaveRequest with query_text, user_id, top_k, similarity_threshold
        
    Returns:
        WeaveResponse with concepts, patterns, risk_profile
    """
    start_time = time.time()
    
    try:
        # Call weaver engine (with multilingual support via Babel Gardens)
        result = weaver.weave(
            query_text=request.query_text,
            user_id=request.user_id,
            language=request.language if hasattr(request, 'language') else "auto",
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        # Record metrics
        latency = time.time() - start_time
        weaver_latency.observe(latency)
        weaver_queries_total.labels(status="success").inc()
        weaver_concepts_found.inc(len(result["concepts"]))
        
        return WeaveResponse(**result)
    
    except Exception as e:
        # Record error metrics
        weaver_queries_total.labels(status="error").inc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Pattern Weaver error: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status dict
    """
    return {
        "status": "healthy",
        "service": "pattern_weavers",
        "version": "1.0.0",
        "epistemic_order": "REASON",
        "layer": "SEMANTIC"
    }


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns:
        Prometheus metrics in text format
    """
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/")
async def root():
    """
    Root endpoint with API info.
    
    Returns:
        API information
    """
    return {
        "service": "Pattern Weavers API",
        "version": "1.0.0",
        "epistemic_order": "REASON (Semantic Layer)",
        "sacred_order": "#5",
        "endpoints": {
            "POST /weave": "Main weaving endpoint",
            "GET /health": "Health check",
            "GET /metrics": "Prometheus metrics"
        },
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8017))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
