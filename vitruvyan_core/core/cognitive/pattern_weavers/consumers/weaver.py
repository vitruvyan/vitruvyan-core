"""
Pattern Weavers - Weaver Consumer
=================================

Pure semantic contextualization logic.
NO I/O - actual embedding and vector search is done by adapters.

The Weaver:
- Validates weave requests
- Prepares queries for embedding
- Processes similarity results into PatternMatch objects
- Aggregates risk profiles

Author: Vitruvyan Core Team
Created: February 2026
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import re

from .base import BaseConsumer, ProcessResult
from ..domain import (
    PatternConfig,
    WeaveRequest,
    WeaveResult,
    WeaveStatus,
    PatternMatch,
    MatchType,
)

logger = logging.getLogger(__name__)


class WeaverConsumer(BaseConsumer):
    """
    Main weaving consumer for Pattern Weavers.
    
    Responsibilities:
    - Validate weave requests
    - Preprocess query text (normalization, language detection prep)
    - Process similarity search results into PatternMatch objects
    - Aggregate risk profiles from matches
    - Extract concepts from results
    
    NOT responsible for (handled by LIVELLO 2):
    - Calling embedding API
    - Querying Qdrant for similarity
    - Logging to PostgreSQL
    - Redis event publishing
    """
    
    def process(self, data: Dict[str, Any]) -> ProcessResult:
        """
        Process a weave request.
        
        Expected input (for request validation):
            query_text: str - User query to analyze
            user_id: str - User identifier
            language: str - ISO 639-1 language code
            top_k: int - Number of results
            similarity_threshold: float - Minimum similarity
            
        Or (for result processing):
            mode: "process_results"
            query_text: str - Original query
            similarity_results: List[Dict] - Results from Qdrant
            
        Returns:
            ProcessResult with WeaveResult in data["result"]
        """
        start_time = datetime.utcnow()
        
        mode = data.get("mode", "validate_request")
        
        if mode == "validate_request":
            return self._validate_request(data, start_time)
        elif mode == "process_results":
            return self._process_results(data, start_time)
        else:
            return ProcessResult(
                success=False,
                data={},
                errors=[f"Unknown mode: {mode}. Use 'validate_request' or 'process_results'"],
            )
    
    def _validate_request(self, data: Dict[str, Any], start_time: datetime) -> ProcessResult:
        """Validate and preprocess a weave request."""
        errors = self.validate_input(data, ["query_text"])
        if errors:
            self._record_error()
            return ProcessResult(success=False, data={}, errors=errors)
        
        query_text = data["query_text"]
        
        # Validate query length
        if len(query_text) > self.config.max_query_length:
            self._record_error()
            return ProcessResult(
                success=False,
                data={},
                errors=[f"Query too long: {len(query_text)} > {self.config.max_query_length}"],
            )
        
        # Create WeaveRequest
        request = WeaveRequest(
            query_text=query_text.strip(),
            user_id=data.get("user_id", "anonymous"),
            language=data.get("language", self.config.default_language),
            top_k=data.get("top_k", self.config.top_k),
            similarity_threshold=data.get("similarity_threshold", self.config.similarity_threshold),
            categories=data.get("categories"),
            correlation_id=data.get("correlation_id"),
        )
        
        # Preprocess query
        preprocessed = self._preprocess_query(request.query_text)
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        self._record_success()
        
        return ProcessResult(
            success=True,
            data={
                "request": request,
                "preprocessed_query": preprocessed,
                "ready_for_embedding": True,
            },
            processing_time_ms=processing_time,
        )
    
    def _process_results(self, data: Dict[str, Any], start_time: datetime) -> ProcessResult:
        """Process similarity search results into WeaveResult."""
        errors = self.validate_input(data, ["similarity_results"])
        if errors:
            self._record_error()
            return ProcessResult(success=False, data={}, errors=errors)
        
        similarity_results = data.get("similarity_results", [])
        threshold = data.get("similarity_threshold", self.config.similarity_threshold)
        
        # Convert to PatternMatch objects
        matches = []
        concepts = []
        
        for result in similarity_results:
            score = result.get("score", 0.0)
            
            # Skip below threshold
            if score < threshold:
                continue
            
            payload = result.get("payload", {})
            
            match = PatternMatch(
                category=payload.get("category", "unknown"),
                name=payload.get("name", ""),
                score=score,
                match_type=MatchType.SEMANTIC,
                metadata=payload,
            )
            matches.append(match)
            
            # Extract concept names
            if match.name:
                concepts.append(match.name)
        
        # Create WeaveResult
        result = WeaveResult(
            status=WeaveStatus.COMPLETED,
            matches=matches,
            extracted_concepts=list(set(concepts)),
            latency_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
        )
        
        self._record_success()
        
        return ProcessResult(
            success=True,
            data={
                "result": result,
                "match_count": len(matches),
                "concept_count": len(result.extracted_concepts),
            },
            processing_time_ms=result.latency_ms,
        )
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess query text for embedding.
        
        - Normalize whitespace
        - Remove excessive punctuation
        - Limit length
        """
        # Normalize whitespace
        preprocessed = " ".join(query.split())
        
        # Remove excessive punctuation (keep sentence structure)
        preprocessed = re.sub(r'[!?]{2,}', '?', preprocessed)
        preprocessed = re.sub(r'\.{2,}', '.', preprocessed)
        
        return preprocessed
    
    def _aggregate_risk(self, matches: List[PatternMatch]) -> RiskProfile:
        """
        Aggregate risk profile from matches.
        
        Combines risk_level metadata from matches to compute overall risk.
        """
        risk_counts = {"low": 0, "medium": 0, "high": 0, "very_high": 0}
        factors = []
        
        for match in matches:
            risk_level = match.metadata.get("risk_level", "medium")
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1
            
            # Collect risk factors
            if risk_level in ("high", "very_high"):
                factors.append(f"{match.name} ({risk_level})")
        
        # Determine overall level
        if risk_counts["very_high"] > 0:
            overall = "very_high"
        elif risk_counts["high"] > risk_counts["medium"]:
            overall = "high"
        elif risk_counts["medium"] > 0:
            overall = "medium"
        else:
            overall = "low"
        
        # Compute dimensions (normalized)
        total = sum(risk_counts.values()) or 1
        dimensions = {
            level: count / total
            for level, count in risk_counts.items()
        }
        
        return RiskProfile(
            overall_level=overall,
            dimensions=dimensions,
            factors=factors,
        )
