# core/logic/vitruvyan_proprietary/vee/vee_memory_adapter.py
"""
🧠 VEE Memory Adapter - Memoria Storica per Explainability

Gestisce la persistenza e recupero di spiegazioni storiche:
- Salva nuove spiegazioni in PostgreSQL
- Recupera spiegazioni precedenti per consistency
- Integra con Qdrant per ricerca semantica
- Garantisce coerenza narrativa nel tempo

Principi:
- Persistenza automatica delle spiegazioni
- Recupero contextuale per ticker/timeframe
- Integrazione con knowledge base esistente
- Fallback graceful per errori di connessione
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

from .vee_analyzer import AnalysisResult
from .vee_generator import ExplanationLevels

# Safe imports with fallbacks
try:
    from core.foundation.persistence.postgres_agent import PostgresAgent
except ImportError:
    PostgresAgent = None

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
except ImportError:
    QdrantClient = None


@dataclass
class HistoricalExplanation:
    """Spiegazione storica recuperata dal database"""
    id: int
    ticker: str
    summary: str
    technical: str
    detailed: str
    language: str
    created_at: datetime
    confidence_level: float
    dominant_factor: str
    sentiment_direction: str
    
    # Metadata per similarity
    kpi_count: int
    overall_intensity: float


class VEEMemoryAdapter:
    """
    Adapter per memoria storica delle spiegazioni
    
    Funzionalità:
    - Store automatico delle nuove spiegazioni
    - Retrieve spiegazioni simili per consistency
    - Search semantico via Qdrant (opzionale)
    - Context enrichment per explainability
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Database connections (lazy initialization)
        self._postgres_agent = None
        self._qdrant_client = None
        
        # Configuration
        self.max_historical_results = 5
        self.similarity_lookback_days = 90
        self.qdrant_collection = "explanations_embeddings"
        
        # Initialize database schema if needed
        self._ensure_schema()
    
    @property
    def postgres_agent(self) -> Optional[PostgresAgent]:
        """Lazy initialization of PostgreSQL connection"""
        if self._postgres_agent is None and PostgresAgent is not None:
            try:
                self._postgres_agent = PostgresAgent()
            except Exception as e:
                self.logger.warning(f"Failed to initialize PostgreSQL: {e}")
        return self._postgres_agent
    
    @property
    def qdrant_client(self) -> Optional[QdrantClient]:
        """Lazy initialization of Qdrant connection"""
        if self._qdrant_client is None and QdrantClient is not None:
            try:
                self._qdrant_client = QdrantClient("localhost", port=6333)
            except Exception as e:
                self.logger.warning(f"Failed to initialize Qdrant: {e}")
        return self._qdrant_client
    
    def store_explanation(self, analysis: AnalysisResult, 
                         explanation: ExplanationLevels) -> bool:
        """
        Salva una nuova spiegazione nel database
        
        Args:
            analysis: Risultato dell'analisi originale
            explanation: Spiegazioni generate
            
        Returns:
            bool: True se salvata con successo
        """
        try:
            if not self.postgres_agent:
                self.logger.warning("PostgreSQL not available, skipping explanation storage")
                return False
            
            # Reset connection in case of previous errors
            try:
                self.postgres_agent.connection.rollback()
            except:
                pass
            
            # Use PostgresAgent pattern with explicit table creation and insert
            with self.postgres_agent.connection.cursor() as cur:
                # Ensure table exists with proper schema
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS vee_explanations (
                        id SERIAL PRIMARY KEY,
                        ticker VARCHAR(10) NOT NULL,
                        summary TEXT NOT NULL,
                        technical TEXT NOT NULL,
                        detailed TEXT NOT NULL,
                        language VARCHAR(5) DEFAULT 'it',
                        confidence_level FLOAT DEFAULT 0.0,
                        dominant_factor VARCHAR(100),
                        sentiment_direction VARCHAR(20),
                        kpi_count INTEGER DEFAULT 0,
                        overall_intensity FLOAT DEFAULT 0.0,
                        analysis_data JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Add missing columns if they don't exist (schema evolution)
                try:
                    cur.execute("ALTER TABLE vee_explanations ADD COLUMN IF NOT EXISTS language VARCHAR(5) DEFAULT 'it'")
                    cur.execute("ALTER TABLE vee_explanations ADD COLUMN IF NOT EXISTS confidence_level FLOAT DEFAULT 0.0")
                    cur.execute("ALTER TABLE vee_explanations ADD COLUMN IF NOT EXISTS dominant_factor VARCHAR(100)")
                    cur.execute("ALTER TABLE vee_explanations ADD COLUMN IF NOT EXISTS sentiment_direction VARCHAR(20)")
                    cur.execute("ALTER TABLE vee_explanations ADD COLUMN IF NOT EXISTS kpi_count INTEGER DEFAULT 0")
                    cur.execute("ALTER TABLE vee_explanations ADD COLUMN IF NOT EXISTS overall_intensity FLOAT DEFAULT 0.0")
                    cur.execute("ALTER TABLE vee_explanations ADD COLUMN IF NOT EXISTS analysis_data JSONB")
                except Exception as e:
                    # Some PostgreSQL versions don't support ADD COLUMN IF NOT EXISTS
                    pass
                
                # Insert explanation
                cur.execute("""
                    INSERT INTO vee_explanations (
                        ticker, summary, technical, detailed, language,
                        confidence_level, dominant_factor, sentiment_direction,
                        kpi_count, overall_intensity, analysis_data, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    analysis.ticker,
                    explanation.summary,
                    explanation.technical,
                    explanation.detailed,
                    explanation.language,
                    analysis.confidence_level,
                    analysis.dominant_factor,
                    analysis.sentiment_direction,
                    analysis.kpi_count,
                    analysis.overall_intensity,
                    json.dumps(asdict(analysis), default=str),
                    datetime.now()
                ))
            
            self.postgres_agent.connection.commit()
            self.logger.info(f"Stored VEE explanation for {analysis.ticker}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing explanation for {analysis.ticker}: {e}")
            try:
                self.postgres_agent.connection.rollback()
            except:
                pass
            return False
                
        except Exception as e:
            self.logger.error(f"Error storing explanation for {analysis.ticker}: {e}")
            return False
    
    def retrieve_similar_explanations(self, ticker: str, 
                                    analysis: Optional[AnalysisResult] = None,
                                    language: str = "it",
                                    limit: int = None) -> List[HistoricalExplanation]:
        """
        Recupera spiegazioni simili storiche
        
        Args:
            ticker: Symbol del ticker
            analysis: Analisi corrente per similarity matching (opzionale)
            language: Lingua preferita
            limit: Numero massimo di risultati
            
        Returns:
            List di HistoricalExplanation ordinate per rilevanza
        """
        try:
            if not self.postgres_agent:
                self.logger.warning("PostgreSQL not available, no historical explanations")
                return []
            
            limit = limit or self.max_historical_results
            cutoff_date = datetime.now() - timedelta(days=self.similarity_lookback_days)
            
            # Base query for ticker-specific explanations
            base_query = """
                SELECT id, ticker, summary, technical, detailed, language,
                       created_at, confidence_level, dominant_factor, sentiment_direction,
                       kpi_count, overall_intensity
                FROM vee_explanations
                WHERE ticker = %s 
                  AND created_at >= %s
                  AND language = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            
            results = self.postgres_agent.fetch_all(base_query, (ticker, cutoff_date, language, limit))
            
            historical = []
            for row in results:
                historical.append(HistoricalExplanation(
                    id=row[0],
                    ticker=row[1],
                    summary=row[2],
                    technical=row[3],
                    detailed=row[4],
                    language=row[5],
                    created_at=row[6],
                    confidence_level=row[7],
                    dominant_factor=row[8],
                    sentiment_direction=row[9],
                    kpi_count=row[10],
                    overall_intensity=row[11]
                ))
            
            # If we have current analysis, try to find semantically similar explanations
            if analysis and len(historical) < limit:
                similar = self._find_semantically_similar(analysis, language, limit - len(historical))
                # Merge and deduplicate
                existing_ids = {h.id for h in historical}
                for sim in similar:
                    if sim.id not in existing_ids:
                        historical.append(sim)
            
            self.logger.info(f"Retrieved {len(historical)} historical explanations for {ticker}")
            return historical
            
        except Exception as e:
            self.logger.error(f"Error retrieving explanations for {ticker}: {e}")
            return []
    
    def enrich_with_context(self, explanation: ExplanationLevels,
                          historical: List[HistoricalExplanation]) -> ExplanationLevels:
        """
        Arricchisce una spiegazione con contesto storico
        
        Args:
            explanation: Spiegazione corrente
            historical: Spiegazioni storiche simili
            
        Returns:
            ExplanationLevels arricchita con contesto
        """
        try:
            if not historical:
                return explanation
            
            # Find most similar historical explanation
            most_similar = self._find_most_similar_explanation(explanation, historical)
            
            if most_similar:
                # Generate contextual reference
                if explanation.language == 'it':
                    context_text = (f"Questa analisi è coerente con {len(historical)} valutazioni precedenti "
                                  f"di {explanation.ticker}. L'ultima analisi simile, del "
                                  f"{most_similar.created_at.strftime('%d/%m/%Y')}, evidenziava "
                                  f"{most_similar.dominant_factor} come fattore dominante.")
                else:
                    context_text = (f"This analysis is consistent with {len(historical)} previous "
                                  f"evaluations of {explanation.ticker}. The most recent similar analysis, "
                                  f"from {most_similar.created_at.strftime('%m/%d/%Y')}, highlighted "
                                  f"{most_similar.dominant_factor} as the dominant factor.")
                
                explanation.contextualized = context_text
                
                # Add historical reference for detailed level
                explanation.historical_reference = most_similar.summary
            
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error enriching context for {explanation.ticker}: {e}")
            return explanation
    
    def get_explanation_trends(self, ticker: str, 
                             days: int = 30) -> Dict[str, Any]:
        """
        Analizza i trend delle spiegazioni per un ticker
        
        Args:
            ticker: Symbol del ticker
            days: Giorni da analizzare
            
        Returns:
            Dict con statistiche e trend
        """
        try:
            if not self.postgres_agent:
                return {}
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT dominant_factor, sentiment_direction, confidence_level,
                       overall_intensity, created_at
                FROM vee_explanations
                WHERE ticker = %s AND created_at >= %s
                ORDER BY created_at DESC
            """
            
            results = self.postgres_agent.fetch_all(query, (ticker, cutoff_date))
            
            if not results:
                return {}
            
            # Analyze trends
            dominant_factors = [r[0] for r in results]
            sentiments = [r[1] for r in results]
            confidences = [r[2] for r in results]
            intensities = [r[3] for r in results]
            
            trends = {
                'total_explanations': len(results),
                'period_days': days,
                'most_common_factor': max(set(dominant_factors), key=dominant_factors.count),
                'most_common_sentiment': max(set(sentiments), key=sentiments.count),
                'average_confidence': sum(confidences) / len(confidences),
                'average_intensity': sum(intensities) / len(intensities),
                'factor_distribution': {f: dominant_factors.count(f) for f in set(dominant_factors)},
                'sentiment_distribution': {s: sentiments.count(s) for s in set(sentiments)}
            }
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends for {ticker}: {e}")
            return {}
    
    def _ensure_schema(self):
        """Assicura che la tabella explanations esista"""
        try:
            if not self.postgres_agent:
                return
            
            create_table_query = """
                CREATE TABLE IF NOT EXISTS explanations (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(10) NOT NULL,
                    summary TEXT NOT NULL,
                    technical TEXT NOT NULL,
                    detailed TEXT NOT NULL,
                    language VARCHAR(5) DEFAULT 'it',
                    confidence_level FLOAT DEFAULT 0.0,
                    dominant_factor VARCHAR(100),
                    sentiment_direction VARCHAR(20),
                    kpi_count INTEGER DEFAULT 0,
                    overall_intensity FLOAT DEFAULT 0.0,
                    analysis_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_explanations_ticker ON explanations(ticker);
                CREATE INDEX IF NOT EXISTS idx_explanations_created_at ON explanations(created_at);
                CREATE INDEX IF NOT EXISTS idx_explanations_ticker_lang ON explanations(ticker, language);
            """
            
            # Create table using PostgresAgent pattern
            with self.postgres_agent.connection.cursor() as cur:
                cur.execute(create_table_query)
            self.postgres_agent.connection.commit()
            self.logger.info("Ensured explanations table schema")
            
        except Exception as e:
            self.logger.error(f"Error ensuring schema: {e}")
    
    def _store_in_qdrant(self, explanation_id: int, analysis: AnalysisResult, 
                        explanation: ExplanationLevels):
        """Store explanation in Qdrant for semantic search"""
        try:
            if not self.qdrant_client:
                return
            
            # Create embedding text from explanation
            embedding_text = f"{explanation.summary} {explanation.technical}"
            
            # For now, we'll use a simple hash as embedding (in production, use actual embeddings)
            # This is a placeholder - in real implementation, use sentence transformers
            import hashlib
            text_hash = hashlib.md5(embedding_text.encode()).hexdigest()
            # Convert hash to pseudo-embedding vector (384 dimensions for MiniLM compatibility)
            pseudo_embedding = [float(int(text_hash[i:i+2], 16)) / 255.0 for i in range(0, min(len(text_hash), 48), 2)]
            # Pad to 384 dimensions
            while len(pseudo_embedding) < 384:
                pseudo_embedding.extend(pseudo_embedding[:min(384-len(pseudo_embedding), len(pseudo_embedding))])
            pseudo_embedding = pseudo_embedding[:384]
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=self.qdrant_collection,
                points=[
                    PointStruct(
                        id=explanation_id,
                        vector=pseudo_embedding,
                        payload={
                            "ticker": analysis.ticker,
                            "dominant_factor": analysis.dominant_factor,
                            "sentiment_direction": analysis.sentiment_direction,
                            "language": explanation.language,
                            "confidence_level": analysis.confidence_level,
                            "created_at": explanation.timestamp.isoformat(),
                            "text": embedding_text
                        }
                    )
                ]
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to store in Qdrant: {e}")
    
    def _find_semantically_similar(self, analysis: AnalysisResult, 
                                 language: str, limit: int) -> List[HistoricalExplanation]:
        """Find semantically similar explanations using Qdrant"""
        try:
            if not self.qdrant_client:
                return []
            
            # This is a simplified version - in production, use proper embeddings
            # For now, filter by similar characteristics
            search_results = self.qdrant_client.scroll(
                collection_name=self.qdrant_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="language", match=MatchValue(value=language)),
                        FieldCondition(key="dominant_factor", match=MatchValue(value=analysis.dominant_factor))
                    ]
                ),
                limit=limit
            )
            
            # Convert results back to HistoricalExplanation
            # This would need to fetch full data from PostgreSQL
            return []  # Simplified for now
            
        except Exception as e:
            self.logger.warning(f"Semantic search failed: {e}")
            return []
    
    def _find_most_similar_explanation(self, current: ExplanationLevels,
                                     historical: List[HistoricalExplanation]) -> Optional[HistoricalExplanation]:
        """Find the most similar historical explanation"""
        if not historical:
            return None
        
        # Simple similarity based on creation time (most recent)
        # In production, could use semantic similarity
        return max(historical, key=lambda h: h.created_at)


# Convenience functions for standalone usage
def store_explanation(analysis: AnalysisResult, explanation: ExplanationLevels) -> bool:
    """
    Convenience function per storage standalone
    
    Args:
        analysis: Risultato dell'analisi
        explanation: Spiegazioni generate
        
    Returns:
        bool: True se salvata con successo
    """
    adapter = VEEMemoryAdapter()
    return adapter.store_explanation(analysis, explanation)


def retrieve_similar_explanations(ticker: str, language: str = "it", 
                                limit: int = 3) -> List[HistoricalExplanation]:
    """
    Convenience function per retrieve standalone
    
    Args:
        ticker: Symbol del ticker
        language: Lingua preferita
        limit: Numero massimo di risultati
        
    Returns:
        List di spiegazioni storiche
    """
    adapter = VEEMemoryAdapter()
    return adapter.retrieve_similar_explanations(ticker, language=language, limit=limit)


if __name__ == "__main__":
    # Test standalone
    from .vee_analyzer import analyze_kpi
    from .vee_generator import generate_explanation
    
    # Test data
    test_kpi = {
        'momentum_z': 0.8,
        'sentiment_z': 0.3,
        'technical_score': 65,
        'risk_score': 45
    }
    
    # Create analysis and explanation
    analysis = analyze_kpi("AAPL", test_kpi)
    explanation = generate_explanation("AAPL", analysis, {'lang': 'it'})
    
    # Test memory adapter
    adapter = VEEMemoryAdapter()
    
    print("=== VEE Memory Adapter Test ===")
    
    # Test storage
    stored = adapter.store_explanation(analysis, explanation)
    print(f"Storage result: {stored}")
    
    # Test retrieval
    historical = adapter.retrieve_similar_explanations("AAPL", language="it")
    print(f"Retrieved {len(historical)} historical explanations")
    
    for h in historical:
        print(f"- {h.created_at.strftime('%Y-%m-%d')}: {h.summary[:100]}...")
    
    # Test context enrichment
    enriched = adapter.enrich_with_context(explanation, historical)
    if enriched.contextualized:
        print(f"Contextualized: {enriched.contextualized}")
    
    # Test trends
    trends = adapter.get_explanation_trends("AAPL", days=30)
    if trends:
        print(f"Trends: {trends}")