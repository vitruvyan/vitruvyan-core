"""
Pattern Weaver Engine — Core Semantic Contextualization Logic

Epistemic Order: REASON (Semantic Layer)
Sacred Order: Pattern Weavers

Provides semantic enrichment by connecting concepts, sectors, regions,
and risk profiles to user queries using Qdrant vector similarity.

Key Features:
- QdrantAgent integration (no direct QdrantClient)
- Cooperative embedding API (vitruvyan_api_embedding:8010)
- UUID v5 deterministic point_id
- PostgreSQL audit logging
- Multi-language support (84 languages via MiniLM-L6-v2)

Author: Sacred Orders
Created: November 9, 2025
"""

import os
import uuid
import time
import yaml
import httpx
from typing import Dict, List, Any, Optional
from pathlib import Path

from core.foundation.persistence.qdrant_agent import QdrantAgent
from core.foundation.persistence.postgres_agent import PostgresAgent


class PatternWeaverEngine:
    """
    Main Pattern Weaver engine for semantic contextualization.
    
    Uses:
    - QdrantAgent for vector search (golden rule compliance)
    - Cooperative embedding API (vitruvyan_api_embedding:8010)
    - PostgreSQL logging via PostgresAgent
    """
    
    def __init__(
        self,
        collection_name: str = "weave_embeddings",
        embedding_api_url: str = None,
        config_path: str = None
    ):
        """
        Initialize Pattern Weaver engine.
        
        Args:
            collection_name: Qdrant collection for weave embeddings
            embedding_api_url: Cooperative embedding API URL
            config_path: Path to weave_rules.yaml
        """
        # Qdrant agent (GOLDEN RULE: always use QdrantAgent)
        self.qdrant = QdrantAgent()
        self.collection_name = collection_name
        
        # PostgreSQL agent (GOLDEN RULE: always use PostgresAgent)
        self.postgres = PostgresAgent()
        
        # Cooperative embedding API (GOLDEN RULE: never load model locally)
        from config.api_config import get_embedding_url
        self.embedding_api_url = embedding_api_url or get_embedding_url()
        
        # Load weave rules configuration
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "weave_rules.yaml"
        self.config = self._load_config(config_path)
        
        # Cache for embeddings (7-day TTL)
        self._embedding_cache: Dict[str, List[float]] = {}
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load weave_rules.yaml configuration."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            print(f"⚠️ Config not found: {config_path}, using empty config")
            return {"concepts": [], "regions": [], "sectors": [], "risk_profiles": []}
    
    def _get_embedding(self, text: str, language: str = "auto") -> List[float]:
        """
        Get multilingual embedding vector from Babel Gardens.
        
        Uses /v1/embeddings/multilingual (84 languages, Unicode-based detection)
        
        Args:
            text: Input text to embed
            language: ISO 639-1 language code ('auto' for detection)
            
        Returns:
            384-dimensional embedding vector
        """
        # Check cache first
        cache_key = f"{text}:{language}"
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        # Try Babel Gardens multilingual endpoint (PRIMARY)
        from config.api_config import get_babel_url
        babel_url = get_babel_url(endpoint="/v1/embeddings/multilingual")
        
        for url in [babel_url]:
            try:
                response = httpx.post(
                    url,
                    json={
                        "text": text,
                        "language": language,
                        "use_cache": True
                    },
                    timeout=5.0
                )
                response.raise_for_status()
                
                data = response.json()
                embedding = data.get("embedding", [0.0] * 384)
                
                # Cache for future use
                self._embedding_cache[cache_key] = embedding
                
                return embedding
            
            except Exception:
                continue  # Try next Babel URL
        
        # Fallback: local embedding API (if Babel Gardens unreachable)
        try:
            response = httpx.post(
                f"{self.embedding_api_url}/v1/embeddings/create",
                json={"text": text},
                timeout=5.0
            )
            response.raise_for_status()
            
            data = response.json()
            embedding = data.get("embedding", [0.0] * 384)
            
            # Cache for future use
            self._embedding_cache[cache_key] = embedding
            
            return embedding
        
        except Exception as e:
            print(f"❌ All embedding APIs failed: {e}")
            # Last resort: zero vector (will match nothing)
            return [0.0] * 384
    
    def _generate_point_id(self, name: str, type_: str) -> str:
        """
        Generate deterministic UUID v5 for point_id.
        
        Same strategy as qdrant_consolidate.py UUID fix.
        
        Args:
            name: Concept/sector/region name
            type_: Type (concept, sector, region, risk_profile)
            
        Returns:
            UUID v5 string
        """
        namespace = uuid.UUID("00000000-0000-0000-0000-000000000000")
        unique_string = f"pattern_weavers:{type_}:{name}"
        return str(uuid.uuid5(namespace, unique_string))
    
    def weave(
        self,
        query_text: str,
        user_id: str,
        language: str = "auto",
        top_k: int = 5,
        similarity_threshold: float = 0.4  # 🟣 LOWERED from 0.6 to 0.4 (Dec 10, 2025) - Financials matches at 0.41
    ) -> Dict[str, Any]:
        """
        Main weaving function: extract concepts, sectors, regions from query.
        
        Args:
            query_text: User query text
            user_id: User identifier
            language: ISO 639-1 language code ('auto' for detection via Babel Gardens)
            top_k: Number of top matches to return
            similarity_threshold: Minimum cosine similarity (0.0-1.0)
            
        Returns:
            Dict with concepts, patterns, risk_profile
        """
        start_time = time.time()
        
        # 1. Get query embedding (using Babel Gardens multilingual)
        query_embedding = self._get_embedding(query_text, language=language)
        
        # 2. Search Qdrant for similar concepts
        search_response = self.qdrant.search(
            collection=self.collection_name,
            query_vector=query_embedding,
            top_k=top_k
        )
        
        # Check for errors
        if search_response.get("status") != "ok":
            print(f"⚠️ Qdrant search error: {search_response.get('error')}")
            return {
                "concepts": [],
                "patterns": [],
                "risk_profile": {},
                "latency_ms": (time.time() - start_time) * 1000
            }
        
        # 🔍 DEBUG: Log search results (Dec 10, 2025)
        results = search_response.get("results", [])
        print(f"🔍 [Pattern Weavers] Qdrant returned {len(results)} results")
        if results:
            print(f"   Top result: score={results[0]['score']:.3f}, payload type={results[0]['payload'].get('type')}")
            print(f"   Threshold: {similarity_threshold}")
        
        # 3. Filter by similarity threshold
        concepts = []
        patterns = []
        
        for result in results:
            score = result["score"]
            payload = result["payload"]
            
            if score < similarity_threshold:
                continue
            
            # Extract concept
            if payload.get("type") == "concept":
                concepts.append(payload.get("name"))
                patterns.append({
                    "type": "concept",
                    "value": payload.get("name"),
                    "confidence": round(score, 3),
                    "sector": payload.get("sector"),
                    "region": payload.get("region")
                })
            
            # Extract sector
            elif payload.get("type") == "sector":
                patterns.append({
                    "type": "sector",
                    "value": payload.get("name"),
                    "confidence": round(score, 3),
                    "risk_level": payload.get("risk_level")
                })
            
            # Extract region
            elif payload.get("type") == "region":
                patterns.append({
                    "type": "region",
                    "value": payload.get("name"),
                    "confidence": round(score, 3),
                    "countries": payload.get("countries", [])
                })
            
            # Extract risk profile
            elif payload.get("type") == "risk_profile":
                patterns.append({
                    "type": "risk_profile",
                    "value": payload.get("name"),
                    "confidence": round(score, 3),
                    "risk_level": payload.get("risk_level")
                })
        
        # 4. Build risk profile summary
        risk_profile = self._build_risk_profile(patterns)
        
        # 5. Log to PostgreSQL
        latency_ms = (time.time() - start_time) * 1000
        self._log_query(
            user_id=user_id,
            query_text=query_text,
            concepts=concepts,
            patterns=patterns,
            latency_ms=latency_ms
        )
        
        return {
            "concepts": concepts,
            "patterns": patterns,
            "risk_profile": risk_profile,
            "latency_ms": round(latency_ms, 2)
        }
    
    def _build_risk_profile(self, patterns: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Build aggregated risk profile from patterns.
        
        Args:
            patterns: List of matched patterns
            
        Returns:
            Dict with risk dimensions (volatility, liquidity, etc.)
        """
        risk_profile = {}
        
        # Extract risk levels from sectors
        sector_risks = [
            p["risk_level"] for p in patterns 
            if p["type"] == "sector" and "risk_level" in p
        ]
        
        if sector_risks:
            # Aggregate (simple mode)
            risk_profile["sector_risk"] = max(sector_risks, key=sector_risks.count)
        
        # Extract risk profiles
        risk_profiles = [
            p["value"] for p in patterns 
            if p["type"] == "risk_profile"
        ]
        
        if risk_profiles:
            risk_profile["dimensions"] = risk_profiles
        
        return risk_profile or {"sector_risk": "unknown", "dimensions": []}
    
    def _log_query(
        self,
        user_id: str,
        query_text: str,
        concepts: List[str],
        patterns: List[Dict[str, Any]],
        latency_ms: float
    ):
        """
        Log weaver query to PostgreSQL.
        
        Uses PostgresAgent (GOLDEN RULE: no direct psycopg2.connect)
        
        Args:
            user_id: User identifier
            query_text: Query text
            concepts: Extracted concepts
            patterns: Matched patterns
            latency_ms: Query latency in milliseconds
        """
        try:
            import json
            
            # Insert into weaver_queries table using proper PostgresAgent pattern
            query = """
                INSERT INTO weaver_queries (user_id, query_text, concepts, patterns, latency_ms)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            with self.postgres.connection.cursor() as cur:
                cur.execute(
                    query,
                    (
                        user_id,
                        query_text,
                        json.dumps(concepts),  # Proper JSON serialization
                        json.dumps(patterns),  # Proper JSON serialization
                        latency_ms
                    )
                )
            self.postgres.connection.commit()
        
        except Exception as e:
            print(f"⚠️ Failed to log weaver query: {e}")
            # Non-blocking: query still succeeds even if logging fails


# Module-level API for easy import
def weave_query(
    query_text: str,
    user_id: str,
    top_k: int = 5,
    similarity_threshold: float = 0.6
) -> Dict[str, Any]:
    """
    Convenience function for weaving queries.
    
    Args:
        query_text: User query text
        user_id: User identifier
        top_k: Number of top matches
        similarity_threshold: Minimum similarity score
        
    Returns:
        Weaver result dict
    """
    engine = PatternWeaverEngine()
    return engine.weave(
        query_text=query_text,
        user_id=user_id,
        top_k=top_k,
        similarity_threshold=similarity_threshold
    )
