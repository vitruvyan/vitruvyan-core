# core/leo/qdrant_agent.py

import os
import logging
import time
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchAny,
    SearchRequest
)

# 🔐 Carica env
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class QdrantAgent:
    def __init__(self):
        # Priorità: HOST+PORT → URL
        host = os.getenv("QDRANT_HOST")
        port = os.getenv("QDRANT_PORT")
        url = os.getenv("QDRANT_URL")

        if host and port:
            url = f"http://{host}:{port}"
        elif not url:
            url = "http://localhost:6333"

        api_key = os.getenv("QDRANT_API_KEY") or None
        timeout = float(os.getenv("QDRANT_TIMEOUT", "30.0"))

        self.client = QdrantClient(
            url=url,
            api_key=api_key,
            timeout=30,  # Hardcoded timeout for robustness
        )
        logger.info(f"QdrantAgent inizializzato su {url}")

    # 🔍 Health check
    def health(self) -> Dict[str, Any]:
        try:
            collections = self.client.get_collections()
            return {"status": "ok", "collections": [c.name for c in collections.collections]}
        except Exception as e:
            logger.error(f"Health check fallito: {e}")
            return {"status": "error", "error": str(e)}

    # 🛠 Assicura collezione (SAFE MODE - no data loss)
    def ensure_collection(self, name: str, vector_size: int, distance: str = "Cosine", force_recreate: bool = False):
        """
        Ensure collection exists. By default, creates only if missing.
        
        Args:
            name: Collection name
            vector_size: Vector dimension (384 for MiniLM-L6-v2)
            distance: Distance metric (Cosine or Dot)
            force_recreate: If True, DELETE ALL DATA and recreate (DANGEROUS!)
        
        Returns:
            Dict with status and action taken
        """
        dist = Distance.COSINE if distance.lower() == "cosine" else Distance.DOT
        
        try:
            # Check if collection exists
            try:
                existing = self.client.get_collection(name)
                
                if force_recreate:
                    logger.warning(f"⚠️  FORCE RECREATE: Deleting collection '{name}' with {existing.points_count} points!")
                    self.client.recreate_collection(
                        collection_name=name,
                        vectors_config=VectorParams(size=vector_size, distance=dist),
                    )
                    logger.info(f"✅ Collection '{name}' recreated (dim={vector_size}, dist={distance})")
                    return {"status": "recreated", "warning": "ALL DATA DELETED"}
                else:
                    logger.info(f"✅ Collection '{name}' already exists ({existing.points_count} points) - no action")
                    return {"status": "exists", "points_count": existing.points_count}
                    
            except Exception:
                # Collection doesn't exist, create it
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=vector_size, distance=dist),
                )
                logger.info(f"✅ Collection '{name}' created (dim={vector_size}, dist={distance})")
                return {"status": "created"}
                
        except Exception as e:
            logger.error(f"❌ Error ensure_collection: {e}")
            return {"status": "error", "error": str(e)}

    # ⬆️ Upsert punti
    def upsert(self, collection: str, points: List[Dict[str, Any]]):
        start = time.time()
        try:
            qdrant_points = [
                PointStruct(id=p["id"], vector=p["vector"], payload=p.get("payload", {}))
                for p in points
            ]
            self.client.upsert(collection_name=collection, points=qdrant_points)
            elapsed = time.time() - start
            logger.info(f"✅ Qdrant upsert completed in {elapsed:.2f}s (collection={collection}, points={len(points)})")
            return {"status": "ok", "count": len(points)}
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"❌ Qdrant upsert failed after {elapsed:.2f}s (collection={collection}, points={len(points)}): {e}")
            raise

    # 🔎 Ricerca
    def search(
        self,
        collection: str,
        query_vector: List[float],
        top_k: int = 10,
        qfilter: Optional[Filter] = None,
        with_payload: bool = True,
    ):
        try:
            top_k = max(1, min(top_k, 50))
            res = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=top_k,
                query_filter=qfilter,
                with_payload=with_payload,
            )
            results = [{"id": r.id, "score": r.score, "payload": r.payload} for r in res]
            return {"status": "ok", "results": results}
        except Exception as e:
            logger.error(f"Errore search: {e}")
            return {"status": "error", "error": str(e)}

    # 🔍 Ricerca seed phrases con smart filtering (elimina Reddit/GNews noise)
    def search_phrases(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_financial_only: bool = True,
        collection: str = "phrases_embeddings"
    ) -> Dict[str, Any]:
        """
        Search seed phrases con filtering intelligente.
        
        Args:
            query_vector: Query embedding (384-dim for MiniLM-L6-v2)
            top_k: Number of results (default 10)
            filter_financial_only: If True, exclude non-financial Reddit/GNews noise
            collection: Qdrant collection name (default: phrases_embeddings)
        
        Returns:
            Dict with status, results (list of {score, phrase_text, source, context_type})
        
        Smart Filtering Strategy:
            INCLUDE:
            - seed_human_generated, gpt_paraphrase, seed_multilingual
            - reddit_it/borsaitaliana/*, reddit_it/finanza/*
            - reddit_en/wallstreetbets/*, reddit_en/stocks/*, reddit_en/investing/*
            
            EXCLUDE (noise):
            - reddit_it/italia/*, reddit_it/italy/*
            - reddit_es/mexico/*, reddit_en/general/*
            - gnews_general
        """
        
        # Financial sources whitelist (include subreddit finanziari)
        FINANCIAL_SOURCES = [
            "seed_human_generated",
            "gpt_paraphrase",
            "seed_multilingual",
            "vitruvyan_docs",
            "earnings_reports",
            "financial_news",
            # Financial subreddits (keep)
            "reddit_it/borsaitaliana/top",
            "reddit_it/borsaitaliana/hot",
            "reddit_it/borsaitaliana/new",
            "reddit_it/finanza/top",
            "reddit_it/finanza/hot",
            "reddit_it/finanza/new",
            "reddit_en/wallstreetbets/top",
            "reddit_en/stocks/top",
            "reddit_en/investing/top",
            "reddit_it/criptovalute/top",
            "reddit_es/criptomonedas/top",
        ]
        
        # Build Qdrant filter
        qfilter = None
        if filter_financial_only:
            qfilter = Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchAny(any=FINANCIAL_SOURCES)
                    )
                ]
            )
        
        try:
            top_k = max(1, min(top_k, 50))
            res = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                query_filter=qfilter,
                limit=top_k,
                with_payload=True,
            )
            
            results = [
                {
                    "score": r.score,
                    "phrase_text": r.payload.get("phrase_text", r.payload.get("phrase", "N/A")),
                    "source": r.payload.get("source", "unknown"),
                    "context_type": r.payload.get("context_type", r.payload.get("context", "unknown")),
                    "language": r.payload.get("language", "unknown"),
                }
                for r in res
            ]
            
            logger.info(
                f"✅ search_phrases: {len(results)} results "
                f"(filtered={filter_financial_only}, collection={collection})"
            )
            
            return {"status": "ok", "results": results, "count": len(results)}
            
        except Exception as e:
            logger.error(f"❌ search_phrases error: {e}")
            return {"status": "error", "error": str(e), "results": []}

    # ❌ Delete by IDs
    def delete_by_ids(self, collection: str, ids: List[str]):
        try:
            self.client.delete(
                collection_name=collection,
                points_selector={"points": ids},
            )
            return {"status": "ok", "deleted": len(ids)}
        except Exception as e:
            logger.error(f"Errore delete_by_ids: {e}")
            return {"status": "error", "error": str(e)}

    # ❌ Delete by filter
    def delete_by_filter(self, collection: str, qfilter: Filter):
        try:
            self.client.delete(
                collection_name=collection,
                points_selector={"filter": qfilter.dict()},
            )
            return {"status": "ok"}
        except Exception as e:
            logger.error(f"Errore delete_by_filter: {e}")
            return {"status": "error", "error": str(e)}

    # ============================================================
    # 🧠 VSGS PR-B — Semantic State Persistence to Qdrant
    # ============================================================

    def upsert_semantic_state(self, matches: List[Dict[str, Any]], user_id: str, collection: str = "semantic_states"):
        """
        Upsert semantic grounding matches to Qdrant (VSGS PR-B).
        
        Args:
            matches: List of semantic matches from grounding node
                     Each match must have: id, embedding, text, score, language
            user_id: User ID for payload
            collection: Qdrant collection name (default: semantic_states)
        
        Returns:
            dict: {"status": "ok", "upserted": N} or {"status": "error", "error": str}
        
        Example:
            matches = [
                {
                    "id": "hash_123",
                    "embedding": [0.1, 0.2, ..., 0.384],  # 384-dim vector
                    "text": "analizza AAPL momentum",
                    "score": 0.87,
                    "language": "it"
                }
            ]
            result = agent.upsert_semantic_state(matches, user_id="user123")
        """
        try:
            points = []
            for m in matches:
                # Validate required fields
                if not all(k in m for k in ["id", "embedding", "text"]):
                    logger.warning(f"Skipping invalid match (missing required fields): {m}")
                    continue
                
                point = PointStruct(
                    id=m["id"],
                    vector=m["embedding"],
                    payload={
                        "user_id": user_id,
                        "text": m.get("text"),
                        "score": m.get("score", 0.0),
                        "language": m.get("language", "en"),
                        "phase": "ingest",
                        "created_at": time.time()
                    }
                )
                points.append(point)
            
            if not points:
                logger.warning("No valid points to upsert")
                return {"status": "ok", "upserted": 0}
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=collection,
                points=points
            )
            
            logger.info(f"✅ upsert_semantic_state: {len(points)} points to {collection}")
            return {"status": "ok", "upserted": len(points)}
            
        except Exception as e:
            logger.error(f"❌ upsert_semantic_state error: {e}")
            return {"status": "error", "error": str(e)}

    def count_points(self, collection: str) -> int:
        """
        Count total points in Qdrant collection (for drift monitoring).
        
        Args:
            collection: Qdrant collection name
        
        Returns:
            int: Total number of points in collection
        """
        try:
            collection_info = self.client.get_collection(collection_name=collection)
            return collection_info.points_count
        except Exception as e:
            logger.error(f"❌ count_points error for {collection}: {e}")
            return 0

    def upsert_point_from_grounding(self, grounding_event: Dict[str, Any], collection: str = "semantic_states"):
        """
        Upsert single semantic grounding event to Qdrant (Memory Orders sync).
        
        Args:
            grounding_event: PostgreSQL row from semantic_grounding_events table
                            Must have: id, user_id, embedding_vector, language, phase
            collection: Qdrant collection name
        
        Returns:
            dict: {"status": "ok"} or {"status": "error", "error": str}
        """
        try:
            if not grounding_event.get("embedding_vector"):
                logger.warning(f"Grounding event {grounding_event['id']} has no embedding_vector, skipping")
                return {"status": "skipped", "reason": "no_embedding"}
            
            point = PointStruct(
                id=grounding_event["id"],
                vector=grounding_event["embedding_vector"],
                payload={
                    "user_id": grounding_event["user_id"],
                    "trace_id": grounding_event.get("trace_id"),
                    "language": grounding_event.get("language", "en"),
                    "phase": grounding_event.get("phase", "sync"),
                    "affective_state": grounding_event.get("affective_state"),
                    "query_text": grounding_event.get("query_text"),
                    "grounding_confidence": grounding_event.get("grounding_confidence"),
                    "synced_at": time.time()
                }
            )
            
            self.client.upsert(
                collection_name=collection,
                points=[point]
            )
            
            logger.info(f"✅ upsert_point_from_grounding: ID {grounding_event['id']} to {collection}")
            return {"status": "ok"}
            
        except Exception as e:
            logger.error(f"❌ upsert_point_from_grounding error: {e}")
            return {"status": "error", "error": str(e)}


# 🚀 CLI test rapido
if __name__ == "__main__":
    import argparse, json

    parser = argparse.ArgumentParser(description="QdrantAgent CLI")
    parser.add_argument("--mode", choices=["health", "ensure"], default="health")
    parser.add_argument("--collection", type=str, default="vitruvyan_notes")
    parser.add_argument("--dim", type=int, default=384)
    args = parser.parse_args()

    agent = QdrantAgent()

    if args.mode == "health":
        out = agent.health()
    elif args.mode == "ensure":
        out = agent.ensure_collection(args.collection, args.dim)
    else:
        out = {"error": "Mode non supportato"}

    print(json.dumps(out, indent=2, ensure_ascii=False))
