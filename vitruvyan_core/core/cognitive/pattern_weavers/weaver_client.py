"""
Pattern Weaver Client — REST API Client

Provides HTTP interface to Pattern Weaver API service.
Used by LangGraph nodes to call weaver_node.

Author: Sacred Orders
Created: November 9, 2025
"""

import httpx
from typing import Dict, List, Any, Optional


class PatternWeaverClient:
    """
    REST client for Pattern Weaver API.
    
    Communicates with vitruvyan_api_weavers:8011
    """
    
    def __init__(self, base_url: str = None):
        """
        Initialize Pattern Weaver client.
        
        Args:
            base_url: API base URL (default: from config.api_config)
        """
        from config.api_config import get_weavers_url
        self.base_url = base_url or get_weavers_url()
        self.client = httpx.Client(timeout=10.0)
    
    def weave(
        self,
        query_text: str,
        user_id: str,
        top_k: int = 5,
        similarity_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Call Pattern Weaver API to extract concepts.
        
        Args:
            query_text: User query text
            user_id: User identifier
            top_k: Number of top matches
            similarity_threshold: Minimum similarity score
            
        Returns:
            Weaver result dict with concepts, patterns, risk_profile
        """
        try:
            response = self.client.post(
                f"{self.base_url}/weave",
                json={
                    "query_text": query_text,
                    "user_id": user_id,
                    "top_k": top_k,
                    "similarity_threshold": similarity_threshold
                }
            )
            response.raise_for_status()
            
            return response.json()
        
        except httpx.HTTPStatusError as e:
            print(f"❌ Pattern Weaver API error: {e.response.status_code}")
            return self._empty_result()
        
        except httpx.RequestError as e:
            print(f"❌ Pattern Weaver API unreachable: {e}")
            return self._empty_result()
        
        except Exception as e:
            print(f"❌ Pattern Weaver client error: {e}")
            return self._empty_result()
    
    def health(self) -> Dict[str, Any]:
        """
        Check Pattern Weaver API health.
        
        Returns:
            Health status dict
        """
        try:
            response = self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            print(f"❌ Pattern Weaver health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def _empty_result(self) -> Dict[str, Any]:
        """
        Return empty result on error (fail gracefully).
        
        Returns:
            Empty weaver result
        """
        return {
            "concepts": [],
            "patterns": [],
            "risk_profile": {},
            "latency_ms": 0.0
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.client.close()
