# core/logic/vitruvyan_proprietary/algorithm_memory_adapter.py
"""
🗃️ Algorithm Memory Adapter - PostgreSQL & Qdrant Integration

Unified logging system for all Vitruvyan proprietary algorithms:
- VARE Risk Analysis → vare_risk_analysis table
- VHSW Strength Analysis → vhsw_strength_analysis table  
- VMFL Factor Analysis → vmfl_factor_analysis table
- Qdrant semantic embeddings for all results

Principi:
- Persistenza automatica dei risultati
- Recupero storico per consistency
- Integrazione Qdrant per ricerca semantica
- Fallback graceful per errori connessione
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import asdict

# Safe imports
try:
    from core.foundation.persistence.postgres_agent import PostgresAgent
except ImportError:
    PostgresAgent = None

try:
    from core.foundation.persistence.qdrant_agent import QdrantAgent
except ImportError:
    QdrantAgent = None

logger = logging.getLogger(__name__)


class AlgorithmMemoryAdapter:
    """
    Unified memory adapter for all proprietary algorithms
    
    Handles PostgreSQL persistence and Qdrant embeddings for:
    - VARE Risk Analysis results
    - VHSW Strength Analysis results
    - VMFL Factor Analysis results
    """
    
    def __init__(self):
        # Initialize agents
        self.postgres_agent = None
        self.qdrant_agent = None
        
        try:
            if PostgresAgent:
                self.postgres_agent = PostgresAgent()
                logger.info("PostgreSQL agent initialized for algorithm logging")
        except Exception as e:
            logger.warning(f"PostgreSQL not available: {e}")
            
        try:
            if QdrantAgent:
                self.qdrant_agent = QdrantAgent()
                logger.info("Qdrant agent initialized for algorithm embeddings")
        except Exception as e:
            logger.warning(f"Qdrant not available: {e}")
    
    def store_vare_result(self, result) -> bool:
        """Store VARE risk analysis result"""
        return self._store_result(
            table='vare_risk_analysis',
            result=result,
            collection='vare_embeddings'
        )
    
    def store_vhsw_result(self, result) -> bool:
        """Store VHSW strength analysis result"""
        return self._store_result(
            table='vhsw_strength_analysis', 
            result=result,
            collection='vhsw_embeddings'
        )
    
    def store_vmfl_result(self, result) -> bool:
        """Store VMFL factor analysis result"""
        return self._store_result(
            table='vmfl_factor_analysis',
            result=result,
            collection='vmfl_embeddings'
        )
    
    def _store_result(self, table: str, result, collection: str) -> bool:
        """Generic result storage method"""
        try:
            if not self.postgres_agent:
                logger.warning("PostgreSQL not available, skipping storage")
                return False
            
            # Reset connection in case of previous errors
            try:
                self.postgres_agent.connection.rollback()
            except:
                pass
            
            # Store in PostgreSQL
            stored = self._store_in_postgres(table, result)
            
            # Store in Qdrant if available
            if stored and self.qdrant_agent:
                self._store_in_qdrant(collection, result)
            
            return stored
            
        except Exception as e:
            logger.error(f"Error storing {table} result for {result.entity_id}: {e}")
            try:
                self.postgres_agent.connection.rollback()
            except:
                pass
            return False
    
    def _store_in_postgres(self, table: str, result) -> bool:
        """Store result in PostgreSQL table"""
        with self.postgres_agent.connection.cursor() as cur:
            if table == 'vare_risk_analysis':
                cur.execute("""
                    INSERT INTO vare_risk_analysis (
                        entity_id, market_risk, volatility_risk, liquidity_risk,
                        correlation_risk, overall_risk, risk_category, confidence,
                        risk_factors, explanation, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    result.entity_id, result.market_risk, result.volatility_risk,
                    result.liquidity_risk, result.correlation_risk, result.overall_risk,
                    result.risk_category, result.confidence,
                    json.dumps(self._clean_json_data(result.risk_factors), default=str),
                    json.dumps(self._clean_json_data(result.explanation), default=str),
                    datetime.now()
                ))
                
            elif table == 'vhsw_strength_analysis':
                cur.execute("""
                    INSERT INTO vhsw_strength_analysis (
                        entity_id, momentum_score, stability_score, volatility_score,
                        trend_strength, confidence, windows_analyzed, explanation,
                        technical_details, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    result.entity_id, result.momentum_score, result.stability_score,
                    result.volatility_score, result.trend_strength, result.confidence,
                    json.dumps(self._clean_json_data(result.windows_analyzed), default=str),
                    json.dumps(self._clean_json_data(result.explanation), default=str),
                    json.dumps(self._clean_json_data(result.technical_details), default=str),
                    datetime.now()
                ))
                
            elif table == 'vmfl_factor_analysis':
                cur.execute("""
                    INSERT INTO vmfl_factor_analysis (
                        entity_id, technical_score, fundamental_score, sentiment_score,
                        momentum_score, composite_score, strength_category, confidence,
                        factor_weights, factor_details, pattern_signals, explanation,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    result.entity_id, result.technical_score, result.fundamental_score,
                    result.sentiment_score, result.momentum_score, result.composite_score,
                    result.strength_category, result.confidence,
                    json.dumps(self._clean_json_data(result.factor_weights), default=str),
                    json.dumps(self._clean_json_data(result.factor_details), default=str),
                    json.dumps(self._clean_json_data(result.pattern_signals), default=str),
                    json.dumps(self._clean_json_data(result.explanation), default=str),
                    datetime.now()
                ))
            
        self.postgres_agent.connection.commit()
        logger.info(f"Stored {table} result for {result.entity_id}")
        return True
    
    def _store_in_qdrant(self, collection: str, result):
        """Store result embeddings in Qdrant"""
        try:
            # Create embedding from result summary/explanation
            embedding_text = self._create_embedding_text(result)
            
            # For now, create a simple hash-based vector
            # In production, use a proper embedding model
            vector = self._create_simple_vector(embedding_text)
            
            # Ensure collection exists
            self.qdrant_agent.ensure_collection(collection, len(vector))
            
            # Store point with integer ID
            point = {
                "id": int(result.timestamp.timestamp()),
                "vector": vector,
                "payload": {
                    "entity_id": result.entity_id,
                    "timestamp": result.timestamp.isoformat(),
                    "algorithm": collection.replace('_embeddings', ''),
                    "summary": embedding_text[:500]  # Truncate for storage
                }
            }
            
            self.qdrant_agent.upsert(collection, [point])
            logger.info(f"Stored {collection} embedding for {result.entity_id}")
            
        except Exception as e:
            logger.warning(f"Failed to store Qdrant embedding: {e}")
    
    def _create_embedding_text(self, result) -> str:
        """Create text representation for embedding"""
        if hasattr(result, 'explanation') and isinstance(result.explanation, dict):
            return " ".join(result.explanation.values())
        elif hasattr(result, 'entity_id'):
            return f"Analysis result for {result.entity_id}"
        else:
            return str(result)
    
    def _create_simple_vector(self, text: str, dim: int = 384) -> List[float]:
        """Create a simple vector from text (hash-based)"""
        import hashlib
        import struct
        
        # Create hash and convert to numbers
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Extend hash to desired dimension
        vector = []
        for i in range(dim):
            byte_idx = i % len(hash_bytes)
            value = struct.unpack('B', hash_bytes[byte_idx:byte_idx+1])[0]
            # Normalize to [-1, 1]
            vector.append((value - 127.5) / 127.5)
        
        return vector
    
    def _clean_json_data(self, data) -> Any:
        """Clean data for JSON serialization (remove NaN, Infinity)"""
        import math
        
        if isinstance(data, dict):
            return {k: self._clean_json_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_json_data(item) for item in data]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return None
            return data
        else:
            return data
    
    def get_historical_results(self, algorithm: str, entity_id: str, 
                             limit: int = 10) -> List[Dict]:
        """Retrieve historical results for a entity_id"""
        if not self.postgres_agent:
            return []
        
        table_map = {
            'vare': 'vare_risk_analysis',
            'vhsw': 'vhsw_strength_analysis', 
            'vmfl': 'vmfl_factor_analysis'
        }
        
        table = table_map.get(algorithm)
        if not table:
            return []
        
        try:
            results = self.postgres_agent.fetch_all(f"""
                SELECT * FROM {table}
                WHERE entity_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (entity_id, limit))
            
            return [dict(zip([desc[0] for desc in self.postgres_agent.connection.cursor().description], row)) 
                   for row in results]
        except Exception as e:
            logger.error(f"Error retrieving historical {algorithm} results: {e}")
            return []


# Global instance
algorithm_memory = AlgorithmMemoryAdapter()


# Convenience functions
def store_vare_result(result) -> bool:
    """Store VARE result globally"""
    return algorithm_memory.store_vare_result(result)

def store_vhsw_result(result) -> bool:
    """Store VHSW result globally"""
    return algorithm_memory.store_vhsw_result(result)

def store_vmfl_result(result) -> bool:
    """Store VMFL result globally"""
    return algorithm_memory.store_vmfl_result(result)