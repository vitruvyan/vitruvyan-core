# core/monitoring/vsgs_metrics.py
"""
📊 VSGS Prometheus Metrics
Sacred Order: Truth Layer (Observability)

Exposes VSGS operational metrics for monitoring and alerting.

Metrics:
- vsgs_grounding_requests_total: Total grounding requests processed
- vsgs_grounding_hits_total: Successful Qdrant retrievals
- vsgs_ingest_total: Semantic states ingested to dual memory
- vsgs_context_chars_total: Total characters injected in LLM prompts

Usage:
    from core.monitoring.vsgs_metrics import (
        vsgs_grounding_requests,
        vsgs_grounding_hits,
        vsgs_ingest_counter,
        vsgs_context_chars
    )
    
    # Increment counters
    vsgs_grounding_requests.inc()
    vsgs_grounding_hits.inc()
    vsgs_ingest_counter.inc()
    vsgs_context_chars.inc(amount=243)  # 243 chars injected

Exposition:
    Metrics exposed at http://vitruvyan_api_graph:8004/metrics
    Compatible with Prometheus scraper
"""

from prometheus_client import Counter

# ============================================================
# VSGS Core Metrics
# ============================================================

vsgs_grounding_requests = Counter(
    'vsgs_grounding_requests_total',
    'Total number of VSGS semantic grounding requests processed',
    ['user_id', 'intent', 'language']
)

vsgs_grounding_hits = Counter(
    'vsgs_grounding_hits_total',
    'Successful VSGS semantic matches retrieved from Qdrant',
    ['user_id', 'collection', 'match_quality']  # match_quality: high/medium/low
)

vsgs_ingest_counter = Counter(
    'vsgs_ingest_total',
    'Semantic states ingested to dual memory (PostgreSQL + Qdrant)',
    ['user_id', 'source']  # source: parse_node, compose_node, etc.
)

vsgs_context_chars = Counter(
    'vsgs_context_chars_total',
    'Total characters of semantic context injected in LLM prompts',
    ['user_id', 'node']  # node: cached_llm, compose, crew
)

# PR-C: Prompt Injection & VEE Integration Metrics
vsgs_prompt_injections = Counter(
    'vsgs_prompt_injections_total',
    'Total semantic context injections into LLM prompts (PR-C)',
    ['user_id', 'node', 'intent']  # Track which nodes inject semantic context
)

vee_generation = Counter(
    'vee_generation_total',
    'Total VEE explanations generated with semantic grounding (PR-C)',
    ['entity_id', 'layers', 'semantic_grounding']  # layers: count, semantic_grounding: true/false
)

# ============================================================
# VSGS Performance Metrics
# ============================================================

vsgs_embedding_latency = Counter(
    'vsgs_embedding_latency_ms_total',
    'Total time spent generating embeddings (milliseconds)',
    ['model']  # model: gemma, minilm
)

vsgs_qdrant_latency = Counter(
    'vsgs_qdrant_latency_ms_total',
    'Total time spent querying Qdrant (milliseconds)',
    ['collection', 'operation']  # operation: search, upsert
)

# ============================================================
# VSGS Error Metrics
# ============================================================

vsgs_errors = Counter(
    'vsgs_errors_total',
    'Total VSGS errors encountered',
    ['error_type', 'component']  # error_type: embedding_failed, qdrant_down, etc.
)

# ============================================================
# Helper Functions
# ============================================================

def record_grounding_request(user_id: str = "demo", intent: str = "unknown", language: str = "en"):
    """Increment grounding requests counter"""
    vsgs_grounding_requests.labels(user_id=user_id, intent=intent, language=language).inc()


def record_grounding_hit(user_id: str = "demo", collection: str = "semantic_states", 
                        match_quality: str = "medium"):
    """
    Increment grounding hits counter
    
    Args:
        match_quality: 'high' (>0.8), 'medium' (0.6-0.8), 'low' (<0.6)
    """
    vsgs_grounding_hits.labels(user_id=user_id, collection=collection, match_quality=match_quality).inc()


def record_ingest(user_id: str = "demo", source: str = "parse_node"):
    """Increment semantic state ingest counter"""
    vsgs_ingest_counter.labels(user_id=user_id, source=source).inc()


def record_context_chars(chars: int, user_id: str = "demo", node: str = "cached_llm"):
    """Increment context characters counter"""
    vsgs_context_chars.labels(user_id=user_id, node=node).inc(amount=chars)


def record_embedding_latency(latency_ms: float, model: str = "gemma"):
    """Record embedding generation latency"""
    vsgs_embedding_latency.labels(model=model).inc(amount=latency_ms)


def record_qdrant_latency(latency_ms: float, collection: str = "semantic_states", 
                         operation: str = "search"):
    """Record Qdrant operation latency"""
    vsgs_qdrant_latency.labels(collection=collection, operation=operation).inc(amount=latency_ms)


def record_error(error_type: str, component: str = "semantic_grounding"):
    """Increment error counter"""
    vsgs_errors.labels(error_type=error_type, component=component).inc()


# ============================================================
# PR-C: New Helper Functions for Prompt Injection & VEE
# ============================================================

def record_prompt_injection(user_id: str = "demo", node: str = "llm_soft_node", 
                           intent: str = "unknown"):
    """
    Increment prompt injection counter (PR-C)
    
    Args:
        user_id: User identifier
        node: LangGraph node that performed injection (llm_soft_node, cached_llm, etc.)
        intent: Detected user intent (trend, sentiment, etc.)
    """
    vsgs_prompt_injections.labels(user_id=user_id, node=node, intent=intent).inc()


def record_vee_generation(entity_id: str, layers: int, semantic_grounding: bool,
                         user_id: str = "demo"):
    """
    Increment VEE generation counter (PR-C)
    
    Args:
        entity_id: Entity entity_id analyzed
        layers: Number of explanation layers generated (3-5)
        semantic_grounding: Whether semantic_context was included
        user_id: User identifier
    """
    vee_generation.labels(
        entity_id=entity_id,
        layers=str(layers),
        semantic_grounding=str(semantic_grounding).lower()
    ).inc()
