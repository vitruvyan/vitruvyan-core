#!/usr/bin/env python3
"""
Vitruvyan Codex Hunters - Cartographer Agent
============================================

The Cartographer is a discovery mapping and audit reporting agent within the Codex Hunters
medieval data intelligence system. It creates detailed consistency maps, visual reports,
and comprehensive analytics for database integrity across PostgreSQL and Qdrant systems.

This agent specializes in:

- Creating visual consistency maps and topology diagrams
- Generating comprehensive audit reports with trends analysis  
- Detecting patterns in inconsistency data across time and collections
- Providing detailed forensic analysis of database integrity issues
- Mapping data flow and relationships between storage systems

The Cartographer serves as the primary intelligence gathering and reporting tool,
providing actionable insights for database administrators and development teams.

Author: Vitruvyan Development Team
Created: 2025-01-14
Phase: 3.3 - Discovery Mapping
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
from collections import defaultdict, Counter
import csv
import io

from .base_hunter import BaseHunter, CodexEvent
from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.persistence.qdrant_agent import QdrantAgent

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, Gauge
    
    cartographer_macro_fetches = Counter(
        'cartographer_macro_fetches_total',
        'Total macro data fetches',
        ['status']
    )
    cartographer_fetch_duration = Histogram(
        'cartographer_macro_fetch_duration_seconds',
        'Macro data fetch duration'
    )
    cartographer_last_fetch = Gauge(
        'cartographer_last_macro_fetch_timestamp',
        'Timestamp of last macro fetch'
    )
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False


class ReportType(Enum):
    """Types of reports the Cartographer can generate"""
    CONSISTENCY_AUDIT = "consistency_audit"
    TREND_ANALYSIS = "trend_analysis"
    FORENSIC_DEEP_DIVE = "forensic_analysis"
    TOPOLOGY_MAP = "topology_mapping"
    PERFORMANCE_IMPACT = "performance_impact"
    EXECUTIVE_SUMMARY = "executive_summary"


class InconsistencyPattern(Enum):
    """Patterns detected in inconsistency data"""
    RANDOM_MISSING = "random_missing"
    BATCH_MISSING = "batch_missing"
    SYSTEMATIC_DRIFT = "systematic_drift"
    CASCADE_FAILURE = "cascade_failure"
    TEMPORAL_CLUSTERING = "temporal_clustering"
    COLLECTION_SPECIFIC = "collection_specific"


@dataclass
class ConsistencyMapEntry:
    """Represents a single entry in the consistency map"""
    collection_name: str
    postgres_count: int
    qdrant_count: int
    consistency_percentage: float
    missing_in_qdrant: int
    extra_in_qdrant: int
    last_sync_time: datetime
    embedding_model: str
    data_freshness_hours: float
    health_status: str  # "excellent", "good", "warning", "critical"
    
    @property
    def total_inconsistencies(self) -> int:
        return self.missing_in_qdrant + self.extra_in_qdrant


@dataclass
class TrendDataPoint:
    """Single data point for trend analysis"""
    timestamp: datetime
    collection: str
    consistency_score: float
    missing_count: int
    extra_count: int
    total_records: int
    expedition_triggered: bool


@dataclass
class InconsistencyCluster:
    """Represents a cluster of related inconsistencies"""
    cluster_id: str
    collections: List[str]
    pattern_type: InconsistencyPattern
    first_detected: datetime
    last_detected: datetime
    total_affected_records: int
    confidence_score: float
    root_cause_hypothesis: str


@dataclass
class AuditReport:
    """Comprehensive audit report structure"""
    report_id: str
    report_type: ReportType
    generated_at: datetime
    time_period: Tuple[datetime, datetime]
    collections_analyzed: List[str]
    
    # Summary metrics
    total_records: int
    total_inconsistencies: int
    overall_consistency: float
    
    # Detailed findings
    consistency_map: List[ConsistencyMapEntry]
    trend_data: List[TrendDataPoint]
    detected_patterns: List[InconsistencyCluster]
    
    # Recommendations
    critical_issues: List[str]
    recommendations: List[str]
    
    # Metadata
    generation_duration_seconds: float
    data_sources_queried: List[str]


class Cartographer(BaseHunter):
    """
    Cartographer Agent - Discovery Mapping and Audit Reporting
    
    The Cartographer creates comprehensive maps of database consistency, analyzes
    trends over time, and generates detailed audit reports. It serves as the primary
    intelligence gathering tool for the Codex Hunters system, providing actionable
    insights for maintaining database integrity.
    """
    
    def __init__(self, postgres_agent: PostgresAgent, qdrant_agent: QdrantAgent):
        super().__init__()
        self.postgres_agent = postgres_agent
        self.qdrant_agent = qdrant_agent
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.trend_analysis_days = 30
        self.pattern_detection_threshold = 0.7
        self.consistency_thresholds = {
            "excellent": 98.0,
            "good": 95.0,
            "warning": 90.0,
            "critical": 85.0
        }
        
        # Caching for performance
        self.cached_consistency_map: Optional[List[ConsistencyMapEntry]] = None
        self.cache_expiry: Optional[datetime] = None
        self.cache_duration_minutes = 15
    
    async def activate(self) -> None:
        """Activate the Cartographer and begin mapping operations"""
        self.logger.info("🗺️ Cartographer activating - Discovery mapping initiated")
        
        try:
            # Initialize mapping systems
            await self._initialize_mapping_systems()
            
            # Generate initial consistency baseline
            await self._generate_consistency_baseline()
            
            # Emit activation event
            await self.emit_event(CodexEvent(
                event_type="mapping.cartographer_activated",
                source="cartographer",
                data={
                    "timestamp": datetime.utcnow().isoformat(),
                    "mapping_systems": "initialized",
                    "status": "discovery_mapping_active"
                }
            ))
            
            self.logger.info("✅ Cartographer activated - Ready for discovery mapping")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to activate Cartographer: {str(e)}")
            raise
    
    async def generate_consistency_map(self, force_refresh: bool = False) -> List[ConsistencyMapEntry]:
        """
        Generate comprehensive consistency map for all collections
        
        Args:
            force_refresh: Force regeneration even if cached data exists
            
        Returns:
            List[ConsistencyMapEntry]: Current consistency state for all collections
        """
        self.logger.info("🗺️ Generating consistency map")
        
        # Check cache first
        if not force_refresh and self._is_cache_valid():
            self.logger.info("📋 Using cached consistency map")
            return self.cached_consistency_map
        
        try:
            start_time = datetime.utcnow()
            consistency_map = []
            
            # Get all available collections
            collections = await self._discover_all_collections()
            
            for collection in collections:
                entry = await self._map_collection_consistency(collection)
                if entry:
                    consistency_map.append(entry)
            
            # Update cache
            self.cached_consistency_map = consistency_map
            self.cache_expiry = datetime.utcnow() + timedelta(minutes=self.cache_duration_minutes)
            
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Emit mapping event
            await self.emit_event(CodexEvent(
                event_type="mapping.consistency_map_generated",
                source="cartographer",
                data={
                    "collections_mapped": len(consistency_map),
                    "generation_time_seconds": generation_time,
                    "total_records": sum(entry.postgres_count for entry in consistency_map),
                    "total_inconsistencies": sum(entry.total_inconsistencies for entry in consistency_map)
                }
            ))
            
            self.logger.info(f"✅ Consistency map generated - {len(consistency_map)} collections mapped")
            return consistency_map
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate consistency map: {str(e)}")
            raise
    
    async def analyze_trends(self, days_back: int = None) -> List[TrendDataPoint]:
        """
        Analyze consistency trends over time
        
        Args:
            days_back: Number of days to analyze (default: trend_analysis_days)
            
        Returns:
            List[TrendDataPoint]: Trend data points over the specified period
        """
        if days_back is None:
            days_back = self.trend_analysis_days
        
        self.logger.info(f"📈 Analyzing consistency trends over {days_back} days")
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Query historical consistency data from agent logs
            trend_data = await self._extract_historical_consistency_data(start_date)
            
            # Emit trend analysis event
            await self.emit_event(CodexEvent(
                event_type="mapping.trend_analysis_completed",
                source="cartographer",
                data={
                    "days_analyzed": days_back,
                    "data_points": len(trend_data),
                    "collections_tracked": len(set(dp.collection for dp in trend_data))
                }
            ))
            
            self.logger.info(f"✅ Trend analysis completed - {len(trend_data)} data points")
            return trend_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to analyze trends: {str(e)}")
            raise
    
    async def detect_patterns(self, trend_data: List[TrendDataPoint] = None) -> List[InconsistencyCluster]:
        """
        Detect patterns in inconsistency data
        
        Args:
            trend_data: Trend data to analyze (will generate if not provided)
            
        Returns:
            List[InconsistencyCluster]: Detected inconsistency patterns
        """
        self.logger.info("🔍 Detecting inconsistency patterns")
        
        if trend_data is None:
            trend_data = await self.analyze_trends()
        
        try:
            clusters = []
            
            # Group data by collection for pattern analysis
            collection_data = defaultdict(list)
            for dp in trend_data:
                collection_data[dp.collection].append(dp)
            
            # Analyze each collection for patterns
            for collection, data_points in collection_data.items():
                collection_patterns = await self._analyze_collection_patterns(collection, data_points)
                clusters.extend(collection_patterns)
            
            # Analyze cross-collection patterns
            cross_patterns = await self._analyze_cross_collection_patterns(trend_data)
            clusters.extend(cross_patterns)
            
            # Emit pattern detection event
            await self.emit_event(CodexEvent(
                event_type="mapping.patterns_detected",
                source="cartographer",
                data={
                    "patterns_detected": len(clusters),
                    "collections_analyzed": len(collection_data),
                    "high_confidence_patterns": sum(1 for c in clusters if c.confidence_score > 0.8)
                }
            ))
            
            self.logger.info(f"✅ Pattern detection completed - {len(clusters)} patterns found")
            return clusters
            
        except Exception as e:
            self.logger.error(f"❌ Failed to detect patterns: {str(e)}")
            raise
    
    async def generate_audit_report(self, report_type: ReportType = ReportType.CONSISTENCY_AUDIT,
                                  time_period_days: int = 7) -> AuditReport:
        """
        Generate comprehensive audit report
        
        Args:
            report_type: Type of report to generate
            time_period_days: Time period to analyze
            
        Returns:
            AuditReport: Comprehensive audit report
        """
        self.logger.info(f"📊 Generating {report_type.value} audit report")
        
        try:
            start_time = datetime.utcnow()
            end_date = start_time
            start_date = end_date - timedelta(days=time_period_days)
            
            # Generate consistency map
            consistency_map = await self.generate_consistency_map()
            
            # Analyze trends
            trend_data = await self.analyze_trends(time_period_days)
            
            # Detect patterns
            patterns = await self.detect_patterns(trend_data)
            
            # Calculate summary metrics
            total_records = sum(entry.postgres_count for entry in consistency_map)
            total_inconsistencies = sum(entry.total_inconsistencies for entry in consistency_map)
            overall_consistency = 100.0 - (total_inconsistencies / total_records * 100) if total_records > 0 else 100.0
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(consistency_map, patterns)
            
            # Identify critical issues
            critical_issues = await self._identify_critical_issues(consistency_map, patterns)
            
            # Create audit report
            report = AuditReport(
                report_id=f"audit_{report_type.value}_{int(start_time.timestamp())}",
                report_type=report_type,
                generated_at=start_time,
                time_period=(start_date, end_date),
                collections_analyzed=[entry.collection_name for entry in consistency_map],
                total_records=total_records,
                total_inconsistencies=total_inconsistencies,
                overall_consistency=overall_consistency,
                consistency_map=consistency_map,
                trend_data=trend_data,
                detected_patterns=patterns,
                critical_issues=critical_issues,
                recommendations=recommendations,
                generation_duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                data_sources_queried=["postgresql", "qdrant", "agent_logs"]
            )
            
            # Log report generation
            await self._log_audit_report(report)
            
            # Emit report generation event
            await self.emit_event(CodexEvent(
                event_type="mapping.audit_report_generated",
                source="cartographer",
                data={
                    "report_id": report.report_id,
                    "report_type": report_type.value,
                    "overall_consistency": overall_consistency,
                    "critical_issues": len(critical_issues),
                    "recommendations": len(recommendations)
                }
            ))
            
            # 🚨 Emit audit ready event for Audit Engine integration
            await self.emit_event(CodexEvent(
                event_type="codex.audit.ready",
                source="cartographer",
                target="audit_engine",
                data={
                    "audit_type": "comprehensive_mapping",
                    "report_id": report.report_id,
                    "consistency_score": overall_consistency,
                    "collections_count": len(consistency_map),
                    "critical_issues_count": len(critical_issues),
                    "recommendations_count": len(recommendations),
                    "total_records_analyzed": total_records,
                    "inconsistencies_detected": total_inconsistencies,
                    "priority": "critical" if overall_consistency < 70.0 else "medium",
                    "requires_immediate_attention": len(critical_issues) > 0,
                    "report_available": True,
                    "suggested_actions": [rec.action for rec in recommendations[:3]]  # Top 3 actions
                }
            ))
            
            self.logger.info(f"✅ Audit report generated - ID: {report.report_id}")
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate audit report: {str(e)}")
            raise
    
    async def export_report(self, report: AuditReport, format: str = "json") -> str:
        """
        Export audit report in specified format
        
        Args:
            report: Audit report to export
            format: Export format ("json", "csv", "html")
            
        Returns:
            str: Exported report content
        """
        self.logger.info(f"📄 Exporting report {report.report_id} as {format}")
        
        try:
            if format.lower() == "json":
                return await self._export_report_json(report)
            elif format.lower() == "csv":
                return await self._export_report_csv(report)
            elif format.lower() == "html":
                return await self._export_report_html(report)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to export report: {str(e)}")
            raise
    
    async def fetch_macro_data(self, fred_series: List[str] = None) -> Dict[str, Any]:
        """
        Fetch macro-economic data from FRED API and store in macro_outlook table.
        
        This method extends Cartographer's capabilities to include economic mapping.
        
        Args:
            fred_series: List of FRED series IDs (default: ["CPIAUCSL", "FEDFUNDS", "VIXCLS"])
        
        Returns:
            Dict with fetch status and stored data
        """
        if fred_series is None:
            fred_series = ["CPIAUCSL", "FEDFUNDS", "VIXCLS"]  # Inflation, Fed Funds, VIX
        
        self.logger.info(f"🌍 Fetching macro data from FRED: {fred_series}")
        
        # Start metrics timer
        if METRICS_ENABLED:
            import time
            start_time = time.time()
        
        try:
            from datetime import date
            import os
            import requests
            
            # Get FRED API key from environment
            fred_api_key = os.getenv("FRED_API_KEY")
            if not fred_api_key:
                self.logger.warning("⚠️ FRED_API_KEY not set - using mock data")
                if METRICS_ENABLED:
                    cartographer_macro_fetches.labels(status="mock").inc()
                return await self._store_mock_macro_data()
            
            # Fetch data from FRED
            fred_data = {}
            base_url = "https://api.stlouisfed.org/fred/series/observations"
            
            for series_id in fred_series:
                try:
                    params = {
                        "series_id": series_id,
                        "api_key": fred_api_key,
                        "file_type": "json",
                        "sort_order": "desc",
                        "limit": 1  # Get most recent value only
                    }
                    
                    response = requests.get(base_url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    if "observations" in data and len(data["observations"]) > 0:
                        latest = data["observations"][0]
                        fred_data[series_id] = {
                            "value": float(latest["value"]),
                            "date": latest["date"]
                        }
                        self.logger.info(f"✅ Fetched {series_id}: {latest['value']} (date: {latest['date']})")
                    else:
                        self.logger.warning(f"⚠️ No data for {series_id}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Failed to fetch {series_id}: {e}")
                    continue
            
            if not fred_data:
                self.logger.warning("⚠️ No FRED data fetched - using mock data")
                if METRICS_ENABLED:
                    cartographer_macro_fetches.labels(status="failed").inc()
                return await self._store_mock_macro_data()
            
            # Store in macro_outlook table using raw SQL
            today = date.today()
            
            with self.postgres_agent.connection.cursor() as cur:
                # Map FRED series to table columns
                inflation_rate = fred_data.get("CPIAUCSL", {}).get("value")
                interest_rate = fred_data.get("FEDFUNDS", {}).get("value")
                market_volatility = fred_data.get("VIXCLS", {}).get("value")
                
                # UPSERT into macro_outlook
                cur.execute("""
                    INSERT INTO macro_outlook 
                    (date, inflation_rate, interest_rate, market_volatility, source)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (date, source) DO UPDATE SET
                        inflation_rate = EXCLUDED.inflation_rate,
                        interest_rate = EXCLUDED.interest_rate,
                        market_volatility = EXCLUDED.market_volatility,
                        created_at = CURRENT_TIMESTAMP
                """, (
                    today,
                    inflation_rate,
                    interest_rate,
                    market_volatility,
                    "cartographer"
                ))
            
            self.postgres_agent.connection.commit()
            
            result = {
                "status": "success",
                "date": today.isoformat(),
                "source": "fred_api",
                "data_stored": {
                    "inflation_rate": inflation_rate,
                    "interest_rate": interest_rate,
                    "market_volatility": market_volatility
                },
                "series_fetched": list(fred_data.keys())
            }
            
            self.logger.info(f"✅ Macro data stored in macro_outlook table")
            
            # Update Prometheus metrics
            if METRICS_ENABLED:
                cartographer_macro_fetches.labels(status="success").inc()
                cartographer_fetch_duration.observe(time.time() - start_time)
                cartographer_last_fetch.set(time.time())
            
            # Emit event
            await self.emit_event(CodexEvent(
                event_type="mapping.macro_data_fetched",
                source="cartographer",
                data=result
            ))
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Failed to fetch/store macro data: {e}")
            if METRICS_ENABLED:
                cartographer_macro_fetches.labels(status="error").inc()
            # Try mock data as fallback
            return await self._store_mock_macro_data()
    
    async def _store_mock_macro_data(self) -> Dict[str, Any]:
        """Store mock macro data when FRED API is unavailable"""
        from datetime import date
        import random
        
        self.logger.info("📝 Storing mock macro data (FRED API unavailable)")
        
        try:
            today = date.today()
            
            # Generate realistic mock values
            inflation_rate = round(2.5 + random.uniform(-0.5, 0.5), 2)  # ~2.5%
            interest_rate = round(5.0 + random.uniform(-0.3, 0.3), 2)   # ~5.0%
            market_volatility = round(15.0 + random.uniform(-3.0, 3.0), 2)  # ~15 VIX
            
            with self.postgres_agent.connection.cursor() as cur:
                cur.execute("""
                    INSERT INTO macro_outlook 
                    (date, inflation_rate, interest_rate, market_volatility, source)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (date, source) DO UPDATE SET
                        inflation_rate = EXCLUDED.inflation_rate,
                        interest_rate = EXCLUDED.interest_rate,
                        market_volatility = EXCLUDED.market_volatility,
                        created_at = CURRENT_TIMESTAMP
                """, (
                    today,
                    inflation_rate,
                    interest_rate,
                    market_volatility,
                    "cartographer_mock"
                ))
            
            self.postgres_agent.connection.commit()
            
            return {
                "status": "success_mock",
                "date": today.isoformat(),
                "source": "mock_data",
                "data_stored": {
                    "inflation_rate": inflation_rate,
                    "interest_rate": interest_rate,
                    "market_volatility": market_volatility
                },
                "warning": "Using mock data - FRED API unavailable"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store mock macro data: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def get_topology_map(self) -> Dict[str, Any]:
        """
        Generate system topology map showing data flow and relationships
        
        Returns:
            Dict[str, Any]: Topology map structure
        """
        self.logger.info("🌐 Generating system topology map")
        
        try:
            consistency_map = await self.generate_consistency_map()
            
            # Create topology structure
            topology = {
                "nodes": [],
                "connections": [],
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "total_collections": len(consistency_map),
                    "data_flow_direction": "postgres -> embedding -> qdrant"
                }
            }
            
            # Add PostgreSQL node
            postgres_node = {
                "id": "postgresql",
                "type": "database",
                "name": "PostgreSQL",
                "status": "active",
                "total_records": sum(entry.postgres_count for entry in consistency_map),
                "collections": len(consistency_map)
            }
            topology["nodes"].append(postgres_node)
            
            # Add Qdrant node
            qdrant_node = {
                "id": "qdrant",
                "type": "vector_database",
                "name": "Qdrant Vector DB",
                "status": "active",
                "total_vectors": sum(entry.qdrant_count for entry in consistency_map),
                "collections": len([e for e in consistency_map if e.qdrant_count > 0])
            }
            topology["nodes"].append(qdrant_node)
            
            # Add embedding service node
            embedding_node = {
                "id": "embedding_service",
                "type": "processing",
                "name": "Embedding Service",
                "status": "active",
                "model": "sentence-transformers/all-MiniLM-L6-v2"
            }
            topology["nodes"].append(embedding_node)
            
            # Add connections
            topology["connections"].extend([
                {
                    "from": "postgresql",
                    "to": "embedding_service",
                    "type": "data_extraction",
                    "status": "active"
                },
                {
                    "from": "embedding_service",
                    "to": "qdrant",
                    "type": "vector_storage",
                    "status": "active"
                }
            ])
            
            # Add collection-specific details
            for entry in consistency_map:
                collection_node = {
                    "id": f"collection_{entry.collection_name}",
                    "type": "collection",
                    "name": entry.collection_name,
                    "consistency": entry.consistency_percentage,
                    "health": entry.health_status,
                    "postgres_records": entry.postgres_count,
                    "qdrant_vectors": entry.qdrant_count,
                    "inconsistencies": entry.total_inconsistencies
                }
                topology["nodes"].append(collection_node)
            
            return topology
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate topology map: {str(e)}")
            raise
    
    # Private methods
    
    def _is_cache_valid(self) -> bool:
        """Check if consistency map cache is still valid"""
        return (self.cached_consistency_map is not None and 
                self.cache_expiry is not None and 
                datetime.utcnow() < self.cache_expiry)
    
    async def _initialize_mapping_systems(self) -> None:
        """Initialize mapping and discovery systems"""
        self.logger.info("⚙️ Initializing mapping systems")
        
        # Clear any existing caches
        self.cached_consistency_map = None
        self.cache_expiry = None
        
        # Test database connections
        try:
            await self.postgres_agent.test_connection()
            self.logger.info("✅ PostgreSQL connection verified")
        except Exception as e:
            self.logger.warning(f"⚠️ PostgreSQL connection issue: {str(e)}")
        
        try:
            await self.qdrant_agent.test_connection()
            self.logger.info("✅ Qdrant connection verified")
        except Exception as e:
            self.logger.warning(f"⚠️ Qdrant connection issue: {str(e)}")
    
    async def _generate_consistency_baseline(self) -> None:
        """Generate initial consistency baseline for monitoring"""
        self.logger.info("📊 Generating consistency baseline")
        
        try:
            consistency_map = await self.generate_consistency_map(force_refresh=True)
            
            baseline_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_collections": len(consistency_map),
                "overall_consistency": sum(e.consistency_percentage for e in consistency_map) / len(consistency_map) if consistency_map else 100.0,
                "total_records": sum(e.postgres_count for e in consistency_map),
                "total_vectors": sum(e.qdrant_count for e in consistency_map)
            }
            
            # Log baseline
            with self.postgres_agent.connection.cursor() as cur:
                # Ensure log_agent table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS log_agent (
                        id SERIAL PRIMARY KEY,
                        agent_name TEXT,
                        action TEXT,
                        details TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        collection_name TEXT
                    )
                """)
                
                cur.execute("""
                    INSERT INTO log_agent (agent_name, action, details, timestamp)
                    VALUES (%s, %s, %s, %s)
                """, ("cartographer", "baseline_generated", json.dumps(baseline_data), datetime.utcnow()))
            
            self.postgres_agent.connection.commit()
            
            self.logger.info(f"✅ Consistency baseline established - {baseline_data['overall_consistency']:.2f}% overall")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not generate baseline: {str(e)}")
    
    async def _discover_all_collections(self) -> List[str]:
        """Discover all collections across PostgreSQL and Qdrant"""
        collections = set()
        
        try:
            # Get PostgreSQL tables with embeddings
            pg_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('phrases', 'sentiment_scores')
            """
            
            pg_result = await self.postgres_agent.fetch_all(pg_query)
            pg_collections = [row[0] for row in pg_result] if pg_result else []
            collections.update(pg_collections)
            
            # Get Qdrant collections
            qdrant_collections = await self.qdrant_agent.list_collections()
            collections.update(qdrant_collections)
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error discovering collections: {str(e)}")
            # Fallback to known collections
            collections = {"phrases", "sentiment_scores"}
        
        return list(collections)
    
    async def _map_collection_consistency(self, collection: str) -> Optional[ConsistencyMapEntry]:
        """Map consistency for a single collection"""
        try:
            # Get PostgreSQL count
            if collection == "phrases":
                pg_query = "SELECT COUNT(*) FROM phrases WHERE embedded IS NOT NULL"
            elif collection == "sentiment_scores":
                pg_query = "SELECT COUNT(*) FROM sentiment_scores WHERE embedding_vector IS NOT NULL"
            else:
                return None
            
            pg_result = await self.postgres_agent.fetch_one(pg_query)
            postgres_count = pg_result[0] if pg_result else 0
            
            # Get Qdrant count
            qdrant_count = await self.qdrant_agent.count_vectors(collection)
            
            # Calculate consistency
            if postgres_count == 0 and qdrant_count == 0:
                consistency_percentage = 100.0
            elif postgres_count == 0:
                consistency_percentage = 0.0
            else:
                consistency_percentage = min(100.0, (qdrant_count / postgres_count) * 100)
            
            # Calculate missing and extra records
            missing_in_qdrant = max(0, postgres_count - qdrant_count)
            extra_in_qdrant = max(0, qdrant_count - postgres_count)
            
            # Determine health status
            if consistency_percentage >= self.consistency_thresholds["excellent"]:
                health_status = "excellent"
            elif consistency_percentage >= self.consistency_thresholds["good"]:
                health_status = "good"
            elif consistency_percentage >= self.consistency_thresholds["warning"]:
                health_status = "warning"
            else:
                health_status = "critical"
            
            # Calculate data freshness (simplified)
            data_freshness_hours = 0.0  # Would calculate based on last update timestamps
            
            return ConsistencyMapEntry(
                collection_name=collection,
                postgres_count=postgres_count,
                qdrant_count=qdrant_count,
                consistency_percentage=consistency_percentage,
                missing_in_qdrant=missing_in_qdrant,
                extra_in_qdrant=extra_in_qdrant,
                last_sync_time=datetime.utcnow(),  # Simplified
                embedding_model="sentence-transformers/all-MiniLM-L6-v2",
                data_freshness_hours=data_freshness_hours,
                health_status=health_status
            )
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to map collection {collection}: {str(e)}")
            return None
    
    async def _extract_historical_consistency_data(self, start_date: datetime) -> List[TrendDataPoint]:
        """Extract historical consistency data from logs"""
        try:
            query = """
            SELECT 
                timestamp,
                collection_name,
                details
            FROM log_agent 
            WHERE agent_name = 'inspector' 
            AND action = 'inspection_completed'
            AND timestamp >= %s
            ORDER BY timestamp
            """
            
            result = await self.postgres_agent.fetch_all(query, (start_date,))
            trend_data = []
            
            for row in result:
                timestamp, collection, details_str = row
                
                try:
                    details = json.loads(details_str) if details_str else {}
                    
                    # Extract consistency metrics
                    consistency_score = details.get('consistency_percentage', 0.0)
                    missing_count = details.get('missing_in_qdrant', 0)
                    extra_count = details.get('extra_in_qdrant', 0)
                    total_records = details.get('postgres_count', 0)
                    expedition_triggered = details.get('healing_expedition_triggered', False)
                    
                    trend_data.append(TrendDataPoint(
                        timestamp=timestamp,
                        collection=collection or "unknown",
                        consistency_score=consistency_score,
                        missing_count=missing_count,
                        extra_count=extra_count,
                        total_records=total_records,
                        expedition_triggered=expedition_triggered
                    ))
                    
                except json.JSONDecodeError:
                    continue
            
            return trend_data
            
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to extract historical data: {str(e)}")
            return []
    
    async def _analyze_collection_patterns(self, collection: str, 
                                         data_points: List[TrendDataPoint]) -> List[InconsistencyCluster]:
        """Analyze patterns within a single collection"""
        if len(data_points) < 3:
            return []
        
        clusters = []
        
        # Sort by timestamp
        data_points.sort(key=lambda x: x.timestamp)
        
        # Analyze for systematic drift
        consistency_scores = [dp.consistency_score for dp in data_points]
        if len(consistency_scores) >= 5:
            # Check for declining trend
            recent_avg = statistics.mean(consistency_scores[-3:])
            earlier_avg = statistics.mean(consistency_scores[:3])
            
            if earlier_avg - recent_avg > 10.0:  # Significant decline
                cluster = InconsistencyCluster(
                    cluster_id=f"drift_{collection}_{int(datetime.utcnow().timestamp())}",
                    collections=[collection],
                    pattern_type=InconsistencyPattern.SYSTEMATIC_DRIFT,
                    first_detected=data_points[0].timestamp,
                    last_detected=data_points[-1].timestamp,
                    total_affected_records=sum(dp.missing_count + dp.extra_count for dp in data_points),
                    confidence_score=0.8,
                    root_cause_hypothesis=f"Systematic degradation in {collection} consistency over time"
                )
                clusters.append(cluster)
        
        return clusters
    
    async def _analyze_cross_collection_patterns(self, trend_data: List[TrendDataPoint]) -> List[InconsistencyCluster]:
        """Analyze patterns across multiple collections"""
        clusters = []
        
        # Group by timestamp to find concurrent issues
        time_groups = defaultdict(list)
        for dp in trend_data:
            # Group by hour
            hour_key = dp.timestamp.replace(minute=0, second=0, microsecond=0)
            time_groups[hour_key].append(dp)
        
        # Look for temporal clustering
        for timestamp, data_points in time_groups.items():
            if len(data_points) >= 2:  # Multiple collections affected at same time
                affected_collections = [dp.collection for dp in data_points 
                                      if dp.consistency_score < 90.0]
                
                if len(affected_collections) >= 2:
                    cluster = InconsistencyCluster(
                        cluster_id=f"temporal_{int(timestamp.timestamp())}",
                        collections=affected_collections,
                        pattern_type=InconsistencyPattern.TEMPORAL_CLUSTERING,
                        first_detected=timestamp,
                        last_detected=timestamp,
                        total_affected_records=sum(dp.missing_count + dp.extra_count for dp in data_points),
                        confidence_score=0.9,
                        root_cause_hypothesis="Concurrent system issue affecting multiple collections"
                    )
                    clusters.append(cluster)
        
        return clusters
    
    async def _generate_recommendations(self, consistency_map: List[ConsistencyMapEntry],
                                      patterns: List[InconsistencyCluster]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Check for critical collections
        critical_collections = [e for e in consistency_map if e.health_status == "critical"]
        if critical_collections:
            recommendations.append(
                f"URGENT: {len(critical_collections)} collections in critical state requiring immediate attention"
            )
        
        # Check for systematic issues
        drift_patterns = [p for p in patterns if p.pattern_type == InconsistencyPattern.SYSTEMATIC_DRIFT]
        if drift_patterns:
            recommendations.append(
                "Systematic drift detected - Consider reviewing embedding pipeline and sync processes"
            )
        
        # Check for temporal clustering
        temporal_patterns = [p for p in patterns if p.pattern_type == InconsistencyPattern.TEMPORAL_CLUSTERING]
        if temporal_patterns:
            recommendations.append(
                "Multiple collections affected simultaneously - Investigate system-wide issues"
            )
        
        # General recommendations
        if any(e.consistency_percentage < 95.0 for e in consistency_map):
            recommendations.append(
                "Schedule regular healing expeditions to maintain consistency above 95%"
            )
        
        return recommendations
    
    async def _identify_critical_issues(self, consistency_map: List[ConsistencyMapEntry],
                                      patterns: List[InconsistencyCluster]) -> List[str]:
        """Identify critical issues requiring immediate attention"""
        critical_issues = []
        
        # Critical consistency levels
        for entry in consistency_map:
            if entry.consistency_percentage < 50.0:
                critical_issues.append(
                    f"Collection '{entry.collection_name}' has critically low consistency: {entry.consistency_percentage:.1f}%"
                )
        
        # High-impact patterns
        for pattern in patterns:
            if pattern.confidence_score > 0.8 and pattern.total_affected_records > 1000:
                critical_issues.append(
                    f"High-impact pattern detected: {pattern.pattern_type.value} affecting {pattern.total_affected_records} records"
                )
        
        return critical_issues
    
    async def _log_audit_report(self, report: AuditReport) -> None:
        """Log audit report generation to database"""
        try:
            with self.postgres_agent.connection.cursor() as cur:
                # Ensure log_agent table exists
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS log_agent (
                        id SERIAL PRIMARY KEY,
                        agent_name TEXT,
                        action TEXT,
                        details TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        collection_name TEXT
                    )
                """)
                
                details = {
                    "report_id": report.report_id,
                    "report_type": report.report_type.value,
                    "collections_analyzed": len(report.collections_analyzed),
                    "overall_consistency": report.overall_consistency,
                    "critical_issues": len(report.critical_issues),
                    "recommendations": len(report.recommendations),
                    "patterns_detected": len(report.detected_patterns)
                }
                
                cur.execute("""
                    INSERT INTO log_agent (agent_name, action, details, timestamp)
                    VALUES (%s, %s, %s, %s)
                """, ("cartographer", "audit_report_generated", json.dumps(details), report.generated_at))
            
            self.postgres_agent.connection.commit()
            
        except Exception as e:
            self.logger.warning(f"⚠️ Could not log audit report: {str(e)}")
    
    async def _export_report_json(self, report: AuditReport) -> str:
        """Export report as JSON"""
        # Convert dataclasses to dicts for JSON serialization
        def serialize_dataclass(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return asdict(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, Enum):
                return obj.value
            else:
                return obj
        
        report_dict = asdict(report)
        return json.dumps(report_dict, default=serialize_dataclass, indent=2)
    
    async def _export_report_csv(self, report: AuditReport) -> str:
        """Export report as CSV (consistency map only)"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Collection', 'PostgreSQL Count', 'Qdrant Count', 'Consistency %',
            'Missing in Qdrant', 'Extra in Qdrant', 'Health Status',
            'Total Inconsistencies'
        ])
        
        # Write data
        for entry in report.consistency_map:
            writer.writerow([
                entry.collection_name,
                entry.postgres_count,
                entry.qdrant_count,
                f"{entry.consistency_percentage:.2f}",
                entry.missing_in_qdrant,
                entry.extra_in_qdrant,
                entry.health_status,
                entry.total_inconsistencies
            ])
        
        return output.getvalue()
    
    async def _export_report_html(self, report: AuditReport) -> str:
        """Export report as HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Vitruvyan Consistency Audit Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }}
                .critical {{ background-color: #ffebee; }}
                .warning {{ background-color: #fff3e0; }}
                .good {{ background-color: #e8f5e8; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Vitruvyan Database Consistency Audit</h1>
                <p><strong>Report ID:</strong> {report.report_id}</p>
                <p><strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Period:</strong> {report.time_period[0].strftime('%Y-%m-%d')} to {report.time_period[1].strftime('%Y-%m-%d')}</p>
            </div>
            
            <div class="metric">
                <strong>Overall Consistency:</strong> {report.overall_consistency:.2f}%
            </div>
            <div class="metric">
                <strong>Total Records:</strong> {report.total_records:,}
            </div>
            <div class="metric">
                <strong>Total Inconsistencies:</strong> {report.total_inconsistencies:,}
            </div>
            
            <h2>Collection Status</h2>
            <table>
                <tr>
                    <th>Collection</th>
                    <th>PostgreSQL</th>
                    <th>Qdrant</th>
                    <th>Consistency</th>
                    <th>Status</th>
                    <th>Missing</th>
                </tr>
        """
        
        for entry in report.consistency_map:
            status_class = entry.health_status
            html += f"""
                <tr class="{status_class}">
                    <td>{entry.collection_name}</td>
                    <td>{entry.postgres_count:,}</td>
                    <td>{entry.qdrant_count:,}</td>
                    <td>{entry.consistency_percentage:.1f}%</td>
                    <td>{entry.health_status.upper()}</td>
                    <td>{entry.missing_in_qdrant:,}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>Critical Issues</h2>
            <ul>
        """
        
        for issue in report.critical_issues:
            html += f"<li>{issue}</li>"
        
        html += """
            </ul>
            
            <h2>Recommendations</h2>
            <ul>
        """
        
        for rec in report.recommendations:
            html += f"<li>{rec}</li>"
        
        html += """
            </ul>
        </body>
        </html>
        """
        
        return html