from datetime import datetime
# api_maestro/main.py
from fastapi import FastAPI, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import logging
import time

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Configure logging FIRST (before VSGS metrics import)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# VSGS metrics (PR-A Bootstrap Phase)
try:
    from core.monitoring.vsgs_metrics import (
        vsgs_grounding_requests,
        vsgs_grounding_hits,
        vsgs_ingest_counter,
        vsgs_context_chars
    )
    logger.info("✅ VSGS metrics imported successfully")
except Exception as e:
    logger.warning(f"⚠️ VSGS metrics import failed: {e} (expected if PR-A not merged)")
    # Graceful degradation: VSGS metrics optional during bootstrap

# Grafo conversazionale
from core.orchestration.langgraph.graph_runner import run_graph_once, run_graph

# DISABLE COMPLEX AUDIT - Use simple monitor instead
# The complex graph_audit_monitor.py requires httpx and causes restart loops
from core.orchestration.langgraph.simple_graph_audit_monitor import (
    initialize_simple_graph_monitoring as initialize_graph_monitoring, 
    shutdown_simple_graph_monitoring as shutdown_graph_monitoring,
    get_simple_graph_monitor as get_graph_monitor
)

app = FastAPI(title="Vitruvyan Graph API", version="1.0.5")

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# Request counters
graph_requests_total = Counter(
    'graph_requests_total',
    'Total number of requests to Graph API',
    ['route', 'method', 'status']
)

graph_failures_total = Counter(
    'graph_failures_total',
    'Total number of failed requests to Graph API',
    ['route', 'error_type']
)

# Latency histograms
graph_request_duration_seconds = Histogram(
    'graph_request_duration_seconds',
    'Request duration in seconds',
    ['route', 'method'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

graph_execution_duration_seconds = Histogram(
    'graph_execution_duration_seconds',
    'Graph execution duration in seconds',
    ['graph_type'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 80.0]
)

# Gauge for inflight requests
api_requests_inflight = Gauge(
    'api_requests_inflight',
    'Number of requests currently being processed'
)

# CrewAI agent specific metrics
crew_agent_latency_seconds = Histogram(
    'crew_agent_latency_seconds',
    'CrewAI agent execution latency',
    ['agent_type'],
    buckets=[1.0, 2.0, 5.0, 10.0, 20.0, 40.0, 60.0, 120.0]
)

# Graph node execution metrics
graph_node_executions_total = Counter(
    'graph_node_executions_total',
    'Total number of graph node executions',
    ['node_name', 'status']
)

# ============================================================================
# PROMETHEUS MIDDLEWARE
# ============================================================================

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Middleware to collect Prometheus metrics for all requests"""
    # Skip metrics endpoint itself
    if request.url.path == "/metrics":
        return await call_next(request)
    
    # Track inflight requests
    api_requests_inflight.inc()
    
    # Start timer
    start_time = time.time()
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        route = request.url.path
        method = request.method
        status = response.status_code
        
        graph_requests_total.labels(route=route, method=method, status=status).inc()
        graph_request_duration_seconds.labels(route=route, method=method).observe(duration)
        
        # Track failures (4xx and 5xx)
        if status >= 400:
            error_type = "client_error" if status < 500 else "server_error"
            graph_failures_total.labels(route=route, error_type=error_type).inc()
        
        return response
        
    except Exception as e:
        # Record exception
        duration = time.time() - start_time
        route = request.url.path
        method = request.method
        
        graph_failures_total.labels(route=route, error_type="exception").inc()
        graph_requests_total.labels(route=route, method=method, status=500).inc()
        graph_request_duration_seconds.labels(route=route, method=method).observe(duration)
        
        raise
        
    finally:
        # Decrement inflight counter
        api_requests_inflight.dec()

# --- CORS (Enabled for Vercel UI + dev.vitruvyan.com) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",            # Local development (port 3000)
        "http://localhost:3001",            # Local development (port 3001)
        "https://*.vercel.app",             # Vercel deployments
        "https://vitruvyan-ui.vercel.app",  # Production Vercel
        "https://dev.vitruvyan.com",        # Production UI (Nginx SSL)
        "http://161.97.140.157:3000",       # VPS UI (if needed)
        "http://161.97.140.157:3001",       # VPS UI port 3001
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class GraphInput(BaseModel):
    input_text: str
    user_id: Optional[str] = None   # se mancante, default "demo"

# --- Healthcheck ---
@app.on_event("startup")
async def startup_event():
    """Initialize audit monitoring on startup"""
    logger.info("🚀 Starting Graph API WITHOUT audit monitoring (testing)")
    # await initialize_graph_monitoring()  # TEMPORARILY DISABLED

@app.on_event("shutdown") 
async def shutdown_event():
    """Shutdown audit monitoring"""
    logger.info("🛑 Shutting down Graph API (no audit monitoring)")
    # await shutdown_graph_monitoring()  # TEMPORARILY DISABLED

@app.get("/health")
async def health():
    """Health check endpoint for container monitoring"""
    # monitor = get_graph_monitor()  # TEMPORARILY DISABLED
    
    return {
        "status": "healthy",
        "service": "graph_orchestrator", 
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.5",
        "audit_monitoring": "disabled_for_testing",
        "heartbeat_count": 0,
        "last_heartbeat": "disabled",
        "portainer_anti_restart": "testing_without_audit"
    }

# --- Endpoints principali ---
@app.post("/graph/dispatch")
async def graph_dispatch(payload: dict = Body(...)):
    """
    Esegue il grafo Leonardo con audit monitoring integrato.
    Restituisce JSON one-line + messaggio umano.
    """
    monitor = get_graph_monitor()
    
    # Monitor graph execution with audit
    async with monitor.monitor_graph_execution(payload):
        result = run_graph(payload)
        json_one_line = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        human = "Leonardo: grafo eseguito con audit monitoring. Se mancano slot chiave ti chiedo un chiarimento."
        
        # Add audit information to result
        result_with_audit = {
            "json": json_one_line, 
            "human": human,
            "audit_monitored": True,
            "timestamp": datetime.now().isoformat()
        }
        
        return result_with_audit

# --- Alias retrocompatibile (/dispatch) ---
@app.post("/dispatch")
async def graph_dispatch_alias(payload: dict = Body(...)):
    """
    Alias diretto verso run_graph (retrocompatibilità con test dispatcher).
    """
    return run_graph(payload)

# --- Endpoint principale compatibile ---
@app.post("/run")
async def run_graph_alias(data: GraphInput):
    """
    Compatibile con pipeline: riceve {input_text, user_id} e passa al grafo con audit.
    """
    input_text = data.input_text
    user_id = data.user_id or "demo"
    
    monitor = get_graph_monitor()
    
    # Monitor single graph execution
    context = {"input_text": input_text, "user_id": user_id}
    async with monitor.monitor_graph_execution(context):
        result = run_graph_once(input_text, user_id=user_id)
        
        # Add audit metadata
        result["audit_monitored"] = True
        result["execution_timestamp"] = datetime.now().isoformat()
        
        return result

# --- Futuri endpoint PG/Qdrant ---
@app.get("/pg/health")
async def pg_health():
    return {"status": "pg_placeholder"}

@app.get("/qdrant/health")
async def qdrant_health():
    return {"status": "qdrant_placeholder"}

# --- Audit endpoints ---
@app.get("/audit/graph/health")
async def graph_audit_health():
    """Get health status of graph audit monitoring"""
    monitor = get_graph_monitor()
    return {
        "status": "healthy" if monitor.monitoring_active else "inactive",
        "monitoring_active": monitor.monitoring_active,
        "current_session_id": monitor.audit_session_id,
        "performance_metrics": monitor.performance_metrics,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/audit/graph/metrics")
async def get_graph_metrics():
    """Get current graph performance metrics"""
    monitor = get_graph_monitor()
    return {
        "metrics": monitor.performance_metrics,
        "monitoring_active": monitor.monitoring_active,
        "session_id": monitor.audit_session_id,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/audit/graph/trigger")
async def trigger_graph_audit():
    """Manually trigger a comprehensive graph audit"""
    try:
        monitor = get_graph_monitor()
        
        # Perform basic system check (simplified)
        findings = []
        
        # Basic health checks without psutil dependency
        monitor = get_graph_monitor()
        current_executions = monitor.performance_metrics.get("executions", 0)
        
        if current_executions > 1000:  # High load indicator
            findings.append({
                "category": "high_load",
                "severity": "medium",
                "description": f"High execution count detected: {current_executions}"
            })
        
        # Check for recent errors
        errors = monitor.performance_metrics.get("errors", [])
        recent_errors = [e for e in errors if (datetime.now() - datetime.fromisoformat(e["timestamp"])).total_seconds() < 3600]  # Last hour
        
        if len(recent_errors) > 5:
            findings.append({
                "category": "high_error_rate", 
                "severity": "high",
                "description": f"High error rate detected: {len(recent_errors)} errors in last hour"
            })
        
        # Log findings (simplified without database)
        for finding in findings:
            logger.info(f"🔍 Manual audit finding: {finding['category']} - {finding['description']}")
        
        return {
            "status": "completed",
            "session_id": monitor.session_id,
            "findings_count": len(findings),
            "execution_count": current_executions,
            "recent_errors": len(recent_errors),
            "findings": findings,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Manual graph audit failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# --- Grafana Alert Webhook ---
@app.post("/webhook/grafana/alert")
async def grafana_alert_webhook(payload: dict = Body(...)):
    """
    Webhook endpoint per ricevere alert da Grafana e inoltrarli su Telegram.
    
    Grafana invia payload con struttura:
    {
        "title": "Alert Title",
        "state": "alerting" | "ok" | "no_data",
        "message": "Alert description",
        "ruleName": "Rule name",
        "ruleUrl": "Link to rule",
        "evalMatches": [...],
        "tags": {...}
    }
    """
    try:
        # TODO: Implement grafana_alerts module
        # from core.notifier.grafana_alerts import send_grafana_alert
        
        logger.info(f"📨 Received Grafana webhook: {payload.get('title', 'No title')}")
        
        # Estrai informazioni dal payload Grafana
        alert_data = {
            "title": payload.get("title", payload.get("ruleName", "Grafana Alert")),
            "state": payload.get("state", "alerting"),
            "message": payload.get("message", "Nessuna descrizione disponibile"),
            "severity": "critical" if payload.get("state") == "alerting" else "info",
            "dashboard_url": payload.get("ruleUrl", "https://dash.vitruvyan.com"),
            "tags": payload.get("tags", {})
        }
        
        # Estrai valore e threshold da evalMatches se disponibili
        eval_matches = payload.get("evalMatches", [])
        if eval_matches and len(eval_matches) > 0:
            first_match = eval_matches[0]
            alert_data["value"] = first_match.get("value")
            alert_data["threshold"] = payload.get("threshold")
        
        # Invia su Telegram
        send_grafana_alert(alert_data)
        
        logger.info(f"✅ Grafana alert forwarded to Telegram: {alert_data['title']}")
        
        return {
            "status": "success",
            "message": "Alert forwarded to Telegram",
            "alert_title": alert_data["title"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to process Grafana webhook: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# --- Semantic Clusters Endpoint ---
@app.get("/clusters/semantic")
async def get_semantic_clusters():
    """
    Get semantic clusters from documentation.
    Returns clustered knowledge organization from docs_archive.
    """
    from core.foundation.persistence.postgres_agent import PostgresAgent
    
    pg = PostgresAgent()
    try:
        with pg.connection.cursor() as cur:
            cur.execute("""
                SELECT 
                    id,
                    cluster_label,
                    keywords,
                    representative_phrases,
                    n_points,
                    created_at
                FROM semantic_clusters
                ORDER BY n_points DESC
            """)
            clusters = cur.fetchall()
            
            return {
                "status": "success",
                "clusters": [
                    {
                        "id": row[0],
                        "label": row[1],
                        "keywords": row[2],
                        "representative_phrases": row[3],
                        "size": row[4],
                        "created_at": row[5].isoformat() if row[5] else None
                    }
                    for row in clusters
                ],
                "total_clusters": len(clusters),
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error fetching semantic clusters: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    finally:
        pg.connection.close()

# --- Fuzzy Ticker Search Endpoint ---
@app.get("/api/tickers/search")
async def search_tickers(q: str = ""):
    """
    Fuzzy ticker search endpoint for UI autocomplete.
    Searches both ticker symbols and company names.
    
    Args:
        q: Query string (partial ticker or company name)
    
    Returns:
        List of matching tickers with metadata:
        [
            {
                "ticker": "C",
                "name": "Citigroup Inc.",
                "sector": "Finance",
                "match_score": 0.95
            },
            ...
        ]
    
    Example:
        /api/tickers/search?q=citi → Returns Citigroup (C)
        /api/tickers/search?q=micro → Returns Microsoft (MSFT), MicroStrategy (MSTR)
    """
    from core.foundation.persistence.postgres_agent import PostgresAgent
    
    start_time = time.time()
    
    if not q or len(q) < 2:
        return {
            "status": "error",
            "message": "Query must be at least 2 characters",
            "results": []
        }
    
    try:
        pg = PostgresAgent()
        query_upper = q.upper()
        query_lower = q.lower()
        
        # Fuzzy search query with PostgreSQL ILIKE + similarity scoring
        # Priority 1: Exact ticker match
        # Priority 2: Ticker starts with query
        # Priority 3: Company name contains query (case-insensitive)
        sql_query = """
            SELECT 
                ticker,
                company_name,
                sector,
                CASE
                    WHEN ticker = %s THEN 1.0
                    WHEN ticker LIKE %s THEN 0.9
                    WHEN LOWER(company_name) LIKE %s THEN 0.7
                    WHEN LOWER(company_name) LIKE %s THEN 0.5
                    ELSE 0.3
                END as match_score
            FROM tickers
            WHERE 
                ticker = %s
                OR ticker LIKE %s
                OR LOWER(company_name) LIKE %s
                OR LOWER(company_name) LIKE %s
            ORDER BY match_score DESC, ticker ASC
            LIMIT 10
        """
        
        # Parameters: exact, starts_with, name_contains_start, name_contains_anywhere
        params = (
            query_upper,  # exact match
            f"{query_upper}%",  # starts with
            f"{query_lower}%",  # name starts with
            f"%{query_lower}%",  # name contains
            query_upper,  # WHERE exact
            f"{query_upper}%",  # WHERE starts
            f"{query_lower}%",  # WHERE name starts
            f"%{query_lower}%"  # WHERE name contains
        )
        
        rows = pg.fetch_all(sql_query, params)
        
        results = [
            {
                "ticker": row[0],
                "name": row[1],
                "sector": row[2] or "Unknown",
                "match_score": float(row[3])
            }
            for row in rows
        ]
        
        duration = time.time() - start_time
        
        logger.info(f"[TickerSearch] query='{q}' results={len(results)} duration={duration:.3f}s")
        
        return {
            "status": "success",
            "query": q,
            "results": results,
            "total": len(results),
            "duration_ms": int(duration * 1000)
        }
        
    except Exception as e:
        logger.error(f"[TickerSearch] Error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "results": []
        }
    finally:
        pg.connection.close()

# --- Prometheus Metrics Endpoint ---
@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    Exposes all collected metrics in Prometheus format.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

