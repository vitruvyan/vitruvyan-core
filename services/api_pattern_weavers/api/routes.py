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
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ..adapters import get_bus_adapter, get_embedding_adapter, get_persistence
from ..models import (
    ErrorResponse,
    HealthStatus,
    PatternMatch,
    TaxonomyStats,
    WeaveRequest,
    WeaveResult,
)

logger = logging.getLogger(__name__)

router = APIRouter()


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
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Get adapters
    embedding_adapter = get_embedding_adapter()
    persistence = get_persistence()
    bus = get_bus_adapter()
    
    # 1. Get embedding
    query_vector = embedding_adapter.get_embedding(request.query)
    if not query_vector:
        raise HTTPException(
            status_code=503,
            detail="Embedding service unavailable",
        )
    
    # 2. Search Qdrant
    from ..config import get_config
    config = get_config()
    
    raw_results = persistence.search_similar(
        collection_name=config.qdrant.collection,
        query_vector=query_vector,
        limit=request.limit,
        score_threshold=request.threshold,
    )
    
    # 3. Process through pure consumer
    weaver = bus.weaver_consumer
    process_result = weaver.process({
        "mode": "process_results",
        "query_text": request.query,
        "similarity_results": raw_results,
        "similarity_threshold": request.threshold,
    })
    
    # 4. Build response
    matches = []
    for match_data in process_result.data.get("matches", []):
        matches.append(PatternMatch(
            name=match_data.get("name", ""),
            category=match_data.get("category", ""),
            score=match_data.get("score", 0.0),
            match_type=match_data.get("match_type", "semantic"),
            metadata=match_data.get("metadata", {}),
        ))
    
    processing_time = (time.time() - start_time) * 1000
    
    # Log the weave
    if request.user_id:
        persistence.log_weave(
            user_id=request.user_id,
            query_text=request.query,
            result={"matches": len(matches), "request_id": request_id},
        )
    
    return WeaveResult(
        request_id=request_id,
        status="completed",
        matches=matches,
        processing_time_ms=processing_time,
        metadata={"query_length": len(request.query)},
    )


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
    
    result = keyword_consumer.process({
        "query_text": request.query,
        "context": request.context or {},
    })
    
    return {
        "request_id": str(uuid.uuid4()),
        "matches": result.data.get("matches", []),
        "method": "keyword",
    }


# =============================================================================
# v3 — Semantic Compilation Endpoint
# =============================================================================

_COMPILE_ENABLED = os.getenv("PATTERN_WEAVERS_V3", "0") == "1"


@router.post("/compile")
async def compile_ontology(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Semantic compilation: query → OntologyPayload via LLM.

    Feature flag: PATTERN_WEAVERS_V3=1 (off by default).

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

    from ..adapters.llm_compiler import get_compiler_adapter

    try:
        from contracts.pattern_weavers import CompileRequest
    except ModuleNotFoundError:
        from vitruvyan_core.contracts.pattern_weavers import CompileRequest

    try:
        compile_req = CompileRequest(
            query=request.get("query", ""),
            user_id=request.get("user_id", "anonymous"),
            language=request.get("language", "auto"),
            domain=request.get("domain", "auto"),
            context=request.get("context", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    adapter = get_compiler_adapter()
    response = adapter.compile(compile_req)

    return response.model_dump()

