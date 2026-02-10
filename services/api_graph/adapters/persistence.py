"""
Graph Orchestrator Persistence Layer

Wraps PostgreSQL queries for semantic clusters and entity search.
ALL database operations must go through this adapter.

Layer: LIVELLO 2 (Service — I/O operations)
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from core.agents.postgres_agent import PostgresAgent

logger = logging.getLogger(__name__)


class GraphPersistence:
    """
    Persistence adapter for Graph Orchestrator.
    
    Responsibilities:
    - Semantic clusters retrieval
    - Entity fuzzy search (autocomplete)
    """
    
    def __init__(self):
        """Initialize PostgreSQL connection."""
        self.pg = PostgresAgent()
    
    def get_semantic_clusters(self) -> Dict[str, Any]:
        """
        Fetch semantic clusters from documentation.
        Returns clustered knowledge organization from docs_archive.
        
        Returns:
            Dict with status, clusters list, total count
        """
        try:
            with self.pg.connection.cursor() as cur:
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
            logger.error(f"Error fetching semantic clusters: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        finally:
            self.pg.connection.close()
    
    def search_entities(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Fuzzy entity_id search for UI autocomplete.
        Searches both entity_id symbols and company names.
        
        Args:
            query: Query string (partial entity_id or company name)
            limit: Maximum results to return (default: 10)
        
        Returns:
            Dict with status, results list, total count
            
        Example:
            search_entities("citi") → Returns Citigroup (C)
            search_entities("micro") → Returns Microsoft (MSFT), MicroStrategy (MSTR)
        """
        if not query or len(query) < 2:
            return {
                "status": "error",
                "message": "Query must be at least 2 characters",
                "results": []
            }
        
        try:
            query_upper = query.upper()
            query_lower = query.lower()
            
            # Fuzzy search query with PostgreSQL ILIKE + similarity scoring
            # Priority 1: Exact entity_id match (score 1.0)
            # Priority 2: Entity_id starts with query (score 0.9)
            # Priority 3: Company name starts with query (score 0.7)
            # Priority 4: Company name contains query (score 0.5)
            sql_query = """
                SELECT 
                    entity_id,
                    company_name,
                    sector,
                    CASE
                        WHEN entity_id = %s THEN 1.0
                        WHEN entity_id LIKE %s THEN 0.9
                        WHEN LOWER(company_name) LIKE %s THEN 0.7
                        WHEN LOWER(company_name) LIKE %s THEN 0.5
                        ELSE 0.3
                    END as match_score
                FROM entity_ids
                WHERE 
                    entity_id = %s
                    OR entity_id LIKE %s
                    OR LOWER(company_name) LIKE %s
                    OR LOWER(company_name) LIKE %s
                ORDER BY match_score DESC, entity_id ASC
                LIMIT %s
            """
            
            # Parameters for fuzzy matching
            params = (
                query_upper,  # exact match
                f"{query_upper}%",  # starts with (entity_id)
                f"{query_lower}%",  # starts with (company name)
                f"%{query_lower}%",  # contains (company name)
                query_upper,  # WHERE exact
                f"{query_upper}%",  # WHERE starts (entity_id)
                f"{query_lower}%",  # WHERE starts (company name)
                f"%{query_lower}%",  # WHERE contains (company name)
                limit
            )
            
            rows = self.pg.fetch(sql_query, params)
            
            results = [
                {
                    "entity_id": row[0],
                    "name": row[1],
                    "sector": row[2] or "Unknown",
                    "match_score": float(row[3])
                }
                for row in rows
            ]
            
            logger.info(f"[EntitySearch] query='{query}' results={len(results)}")
            
            return {
                "status": "success",
                "query": query,
                "results": results,
                "total": len(results)
            }
            
        except Exception as e:
            logger.error(f"[EntitySearch] Error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "results": []
            }
        finally:
            self.pg.connection.close()
