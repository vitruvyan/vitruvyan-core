# api_semantic/main_semantic.py

import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from core.cognitive.semantic_engine.semantic_engine import parse_user_input

app = FastAPI(
    title="Vitruvyan Semantic API",
    description="Motore semantico per parsing input + sentiment batch",
    version="1.0.1"
)

# ===========================
# PROMETHEUS METRICS
# ===========================

http_requests_total = Counter(
    'semantic_http_requests_total',
    'Total HTTP requests to Semantic Engine',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'semantic_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

semantic_matches_total = Counter(
    'semantic_matches_total',
    'Total semantic matching operations performed'
)

semantic_match_duration_seconds = Histogram(
    'semantic_match_duration_seconds',
    'Semantic matching processing time in seconds',
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

semantic_engine_status = Gauge(
    'semantic_engine_status',
    'Semantic engine operational status (1=operational, 0=degraded)'
)

@app.post("/semantic_match")
async def semantic_match(request: Request):
    start_time = time.time()
    
    try:
        data = await request.json()
        user_input = data.get("query", "")
        parsed = parse_user_input(user_input)
        
        # Track metrics
        duration = time.time() - start_time
        semantic_matches_total.inc()
        semantic_match_duration_seconds.observe(duration)
        http_requests_total.labels(method='POST', endpoint='/semantic_match', status='200').inc()
        http_request_duration_seconds.labels(method='POST', endpoint='/semantic_match').observe(duration)
        
        return {
            "semantic_matches": parsed.get("semantic_matches", [])
        }
    except Exception as e:
        duration = time.time() - start_time
        http_requests_total.labels(method='POST', endpoint='/semantic_match', status='500').inc()
        http_request_duration_seconds.labels(method='POST', endpoint='/semantic_match').observe(duration)
        raise

# ✅ Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint for Semantic Engine"""
    try:
        # Update status gauge (1 = operational)
        semantic_engine_status.set(1)
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except Exception:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
