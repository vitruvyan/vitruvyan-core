"""
Pattern Weavers API Routes
==========================

Thin HTTP endpoints that validate → delegate → return.
All business logic is in LIVELLO 1 consumers via adapters.
"""

import logging
import os
import time
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from ..adapters import get_bus_adapter, get_embedding_adapter, get_persistence
from ..models import (
    HealthStatus,
    PatternMatch,
    TaxonomyStats,
    WeaveRequest,
    WeaveResult,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _normalize_match(raw_match: Any) -> Dict[str, Any]:
    """Normalize PatternMatch-like objects to plain dict."""
    if hasattr(raw_match, "to_dict"):
        return raw_match.to_dict()
    if isinstance(raw_match, dict):
        return raw_match
    return {}


def _to_api_matches(raw_matches: List[Any]) -> List[PatternMatch]:
    """Map domain matches to API schema."""
    matches: List[PatternMatch] = []
    for raw_match in raw_matches:
        match_data = _normalize_match(raw_match)
        if not match_data:
            continue
        matches.append(
            PatternMatch(
                name=match_data.get("name", ""),
                category=match_data.get("category", ""),
                score=match_data.get("score", 0.0),
                match_type=match_data.get("match_type", "semantic"),
                metadata=match_data.get("metadata", {}),
            )
        )
    return matches


def run_weave_pipeline(request: WeaveRequest) -> Dict[str, Any]:
    """
    Execute Pattern Weavers pipeline and return normalized payload.

    Shared by `/weave` and finance-specific weave route.
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())

    embedding_adapter = get_embedding_adapter()
    persistence = get_persistence()
    bus = get_bus_adapter()

    # 1) Embedding
    query_vector = embedding_adapter.get_embedding(request.query)
    if not query_vector:
        raise HTTPException(
            status_code=503,
            detail="Embedding service unavailable",
        )

    # 2) Qdrant search
    from ..config import get_config

    config = get_config()
    raw_results = persistence.search_similar(
        collection_name=config.qdrant.collection,
        query_vector=query_vector,
        limit=request.limit,
        score_threshold=request.threshold,
    )

    # 3) Domain consumer
    weaver = bus.weaver_consumer
    process_result = weaver.process(
        {
            "mode": "process_results",
            "query_text": request.query,
            "similarity_results": raw_results,
            "similarity_threshold": request.threshold,
            "categories": request.categories,
        }
    )

    if not process_result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Weave processing failed: {process_result.errors}",
        )

    domain_result = process_result.data.get("result")
    if domain_result is None:
        raise HTTPException(
            status_code=500,
            detail="Weave processing failed: empty domain result",
        )

    matches = _to_api_matches(getattr(domain_result, "matches", []))
    extracted_concepts = list(getattr(domain_result, "extracted_concepts", []))
    processing_time = (time.time() - start_time) * 1000

    if request.user_id:
        persistence.log_weave(
            user_id=request.user_id,
            query_text=request.query,
            result={
                "matches": len(matches),
                "request_id": request_id,
                "extracted_concepts": extracted_concepts,
            },
        )

    return {
        "request_id": request_id,
        "status": getattr(getattr(domain_result, "status", None), "value", "completed"),
        "matches": matches,
        "processing_time_ms": processing_time,
        "metadata": {
            "query_length": len(request.query),
            "match_count": len(matches),
            "extracted_concepts": extracted_concepts,
        },
    }


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """Check service health."""
    persistence = get_persistence()
    bus = get_bus_adapter()
    embedding = get_embedding_adapter()
    
    return HealthStatus(
        status="healthy",
        qdrant=persistence.check_qdrant_health(),
        postgres=persistence.check_database_health(),
        redis=bus.check_health(),
        embedding_service=embedding.check_health(),
    )


@router.post("/weave", response_model=WeaveResult)
async def weave_patterns(request: WeaveRequest):
    """
    Weave patterns for a query.
    
    Flow:
    1. Get embedding from Babel Gardens
    2. Search Qdrant for similar patterns
    3. Process results through pure consumer
    4. Return structured result
    """
    result = run_weave_pipeline(request)
    return WeaveResult(**result)


@router.get("/taxonomy/stats", response_model=TaxonomyStats)
async def get_taxonomy_stats():
    """Get taxonomy statistics."""
    try:
        from core.cognitive.pattern_weavers.domain import get_config as get_domain_config
        domain_config = get_domain_config()
        
        categories = []
        total = 0
        if domain_config.taxonomy:
            categories = list(domain_config.taxonomy.categories.keys())
            total = sum(len(v) for v in domain_config.taxonomy.categories.values())
        
        return TaxonomyStats(
            total_entries=total,
            categories=categories,
        )
    except Exception as e:
        logger.warning(f"Could not get taxonomy: {e}")
        return TaxonomyStats()


@router.post("/keyword-match")
async def keyword_match(request: WeaveRequest) -> Dict[str, Any]:
    """
    Fallback keyword matching (no embedding required).
    """
    bus = get_bus_adapter()
    keyword_consumer = bus.keyword_consumer
    
    result = keyword_consumer.process(
        {
            "query_text": request.query,
            "context": request.context or {},
            "categories": request.categories,
        }
    )

    raw_matches = result.data.get("matches", [])
    serialized_matches = []
    for item in raw_matches:
        normalized = _normalize_match(item)
        if normalized:
            serialized_matches.append(normalized)

    return {
        "request_id": str(uuid.uuid4()),
        "matches": serialized_matches,
        "method": "keyword",
    }


# =============================================================================
# v3 — Semantic Compilation Endpoint
# =============================================================================

_COMPILE_ENABLED = os.getenv("PATTERN_WEAVERS_V3", "0") == "1"


def _ensure_finance_plugin_registered():
    """Register finance semantic plugin if PATTERN_DOMAIN=finance (once)."""
    from ..config import get_config

    if get_config().service.pattern_domain != "finance":
        return

    from ..adapters.llm_compiler import get_compiler_adapter

    adapter = get_compiler_adapter()
    if adapter._registry.has_domain("finance"):
        return  # Already registered

    try:
        from domains.finance.pattern_weavers.finance_semantic_plugin import (
            FinanceSemanticPlugin,
        )
    except ModuleNotFoundError:
        from core.domains.finance.pattern_weavers.finance_semantic_plugin import (
            FinanceSemanticPlugin,
        )

    adapter.register_plugin(FinanceSemanticPlugin())
    logger.info("Finance semantic plugin registered for /compile")


@router.post("/compile")
async def compile_ontology(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Semantic compilation: query → OntologyPayload via LLM.

    Feature flag: PATTERN_WEAVERS_V3=1 (off by default).
    When PATTERN_DOMAIN=finance, auto-registers FinanceSemanticPlugin.

    Flow:
    1. Select domain plugin (auto-detect or explicit)
    2. Call LLM with domain system prompt
    3. Parse response into OntologyPayload (strict schema)
    4. Domain plugin validation
    5. Return CompileResponse
    """
    if not _COMPILE_ENABLED:
        raise HTTPException(
            status_code=404,
            detail="Compile endpoint disabled. Set PATTERN_WEAVERS_V3=1 to enable.",
        )

    _ensure_finance_plugin_registered()

    from ..adapters.llm_compiler import get_compiler_adapter

    try:
        from contracts.pattern_weavers import CompileRequest
    except ModuleNotFoundError:
        from contracts.pattern_weavers import CompileRequest

    # Determine domain: if PATTERN_DOMAIN=finance and request says "auto", use finance
    from ..config import get_config
    config = get_config()
    request_domain = request.get("domain", "auto")
    if request_domain == "auto" and config.service.pattern_domain == "finance":
        request_domain = "finance"

    try:
        compile_req = CompileRequest(
            query=request.get("query", ""),
            user_id=request.get("user_id", "anonymous"),
            language=request.get("language", "auto"),
            domain=request_domain,
            context=request.get("context", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    adapter = get_compiler_adapter()
    response = adapter.compile(compile_req)

    return response.model_dump()
