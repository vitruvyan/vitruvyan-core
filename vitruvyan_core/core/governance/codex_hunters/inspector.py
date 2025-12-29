# core/agents/codex_hunters/inspector.py
"""
🔬 THE INSPECTOR - Codex Authenticity Agent
===========================================
Validates codex integrity across archives.

Like a medieval scholar examining manuscript authenticity by comparing
different copies in various monasteries, The Inspector validates that
codices stored in the PostgreSQL Archive match their vector embeddings
in the Qdrant Vault.

Detects orphaned records, missing embeddings, calculates consistency scores,
and triggers healing expeditions when corruption is discovered.

Publishes CodexEvent(type="authenticity.verified")
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

from core.foundation.persistence.postgres_agent import PostgresAgent
from core.foundation.persistence.qdrant_agent import QdrantAgent
from core.governance.codex_hunters.hunter import (
    BaseHunter,
    CodexEvent
)

logger = logging.getLogger(__name__)


class Inspector(BaseHunter):
    """
    Authenticity verification agent that validates codex integrity.
    
    Features:
    - Cross-database record count comparison (PostgreSQL ↔ Qdrant)
    - Missing embedding detection
    - Orphaned vector identification
    - Consistency score calculation
    - Healing expedition triggers
    - Integrity report generation
    """
    
    def __init__(self):
        super().__init__("Inspector")
        
        # Validation thresholds
        self.consistency_thresholds = {
            "excellent": 0.95,    # > 95% consistency
            "good": 0.85,         # > 85% consistency  
            "poor": 0.70,         # > 70% consistency
            "critical": 0.50      # > 50% consistency (healing required)
        }
        
        # Collection mappings (PostgreSQL table → Qdrant collection)
        self.collection_mappings = {
            "sentiment_scores": "sentiment_context",
            "phrases": "phrases_embeddings",  # Fixed: use existing collection with 39k embeddings
            "market_data": "market_data"
        }
        
        # Track validation statistics
        self.validation_stats = {
            "inspections_completed": 0,
            "inconsistencies_found": 0,
            "healing_expeditions_triggered": 0,
            "last_inspection": None,
            "average_consistency_score": 0.0
        }
        
        logger.info(f"🔬 {self.name}: Inspector ready for authenticity verification")

    def execute(
        self,
        scope: str = "all",
        healing: bool = True,
        detailed: bool = False
    ) -> Dict[str, Any]:
        """
        Execute comprehensive integrity inspection
        
        Args:
            scope: Inspection scope ('all', 'sentiment', 'phrases', 'market_data')
            healing: Whether to trigger healing expeditions for critical issues
            detailed: Whether to include detailed inconsistency reports
            
        Returns:
            dict: Inspection results with consistency scores and recommendations
        """
        logger.info(f"🔬 {self.name}: Starting authenticity inspection (scope: {scope})")
        
        try:
            inspection_start = datetime.now()
            
            # Determine collections to inspect
            collections_to_inspect = self._get_inspection_scope(scope)
            
            inspection_results = {
                "inspection_id": f"inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": inspection_start.isoformat(),
                "scope": scope,
                "collections": {},
                "overall_consistency": 0.0,
                "recommendations": [],
                "healing_triggered": False
            }
            
            total_consistency = 0.0
            collection_count = 0
            
            # Inspect each collection mapping
            for pg_table, qdrant_collection in collections_to_inspect.items():
                logger.info(f"🔍 Inspecting {pg_table} ↔ {qdrant_collection}")
                
                collection_result = self._inspect_collection_pair(
                    pg_table, 
                    qdrant_collection,
                    detailed=detailed
                )
                
                inspection_results["collections"][pg_table] = collection_result
                total_consistency += collection_result["consistency_score"]
                collection_count += 1
                
                # Check if healing is needed
                if (healing and 
                    collection_result["consistency_score"] < self.consistency_thresholds["critical"]):
                    
                    healing_result = self._trigger_healing_expedition(
                        pg_table, 
                        qdrant_collection,
                        collection_result["inconsistencies"]
                    )
                    
                    collection_result["healing_triggered"] = True
                    collection_result["healing_result"] = healing_result
                    inspection_results["healing_triggered"] = True
            
            # Calculate overall consistency
            inspection_results["overall_consistency"] = (
                total_consistency / collection_count if collection_count > 0 else 0.0
            )
            
            # Calculate total inconsistencies
            inspection_results["total_inconsistencies"] = sum(
                len(result.get("inconsistencies", [])) 
                for result in inspection_results["collections"].values()
            )
            
            # Generate recommendations
            inspection_results["recommendations"] = self._generate_recommendations(
                inspection_results
            )
            
            # Update statistics
            self._update_inspection_stats(inspection_results)
            
            # Publish authenticity verification event
            self.publish_event(
                event_type="codex.authenticity.verified",
                payload={
                    "inspection_id": inspection_results["inspection_id"],
                    "overall_consistency": inspection_results["overall_consistency"],
                    "collections_inspected": list(collections_to_inspect.keys()),
                    "healing_triggered": inspection_results["healing_triggered"]
                },
                severity="info"
            )
            
            # 🚨 Publish audit ready event for Audit Engine processing
            self.publish_event(
                event_type="codex.audit.ready",
                payload={
                    "audit_type": "integrity_inspection",
                    "inspection_id": inspection_results["inspection_id"],
                    "consistency_score": inspection_results["overall_consistency"],
                    "collections_analyzed": len(collections_to_inspect),
                    "issues_found": inspection_results["total_inconsistencies"],
                    "recommendations": inspection_results.get("recommendations", []),
                    "priority": "critical" if inspection_results["overall_consistency"] < 0.70 else "medium",
                    "requires_immediate_action": inspection_results["overall_consistency"] < self.consistency_thresholds["critical"]
                },
                severity="critical" if inspection_results["overall_consistency"] < 0.70 else "info"
            )
            
            # If critical issues found, send alert to Audit Engine
            if inspection_results["overall_consistency"] < self.consistency_thresholds["critical"]:
                self.publish_event(
                    event_type="codex.audit.alert",
                    payload={
                        "alert_type": "critical_consistency",
                        "inspection_id": inspection_results["inspection_id"],
                        "consistency_percentage": inspection_results["overall_consistency"],
                        "affected_collections": [
                            name for name, result in inspection_results["collections"].items()
                            if result.get("status") == "critical"
                        ]
                    },
                    severity="critical"
                )
            
            inspection_duration = (datetime.now() - inspection_start).total_seconds()
            
            logger.info(
                f"✅ {self.name}: Inspection completed in {inspection_duration:.1f}s "
                f"(consistency: {inspection_results['overall_consistency']:.1%})"
            )
            
            return inspection_results
            
        except Exception as e:
            logger.error(f"❌ {self.name}: Inspection failed: {e}")
            self.stats["operations_failed"] += 1
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _get_inspection_scope(self, scope: str) -> Dict[str, str]:
        """Get collection mappings based on inspection scope"""
        if scope == "all":
            return self.collection_mappings
        elif scope == "sentiment":
            return {"sentiment_scores": "sentiment_context"}
        elif scope == "phrases":
            return {"phrases": "phrases_embeddings"}
        elif scope == "market_data":
            return {"market_data": "market_data"}
        else:
            logger.warning(f"⚠️ Unknown scope '{scope}', defaulting to 'all'")
            return self.collection_mappings

    def _inspect_collection_pair(
        self, 
        pg_table: str, 
        qdrant_collection: str,
        detailed: bool = False
    ) -> Dict[str, Any]:
        """
        Inspect a PostgreSQL table ↔ Qdrant collection pair
        
        Returns:
            dict: Collection inspection results
        """
        result = {
            "pg_table": pg_table,
            "qdrant_collection": qdrant_collection,
            "pg_count": 0,
            "qdrant_count": 0,
            "consistency_score": 0.0,
            "inconsistencies": [],
            "status": "unknown"
        }
        
        try:
            # Get PostgreSQL record count
            pg_count = self._get_postgres_record_count(pg_table)
            result["pg_count"] = pg_count
            
            # Get Qdrant vector count
            qdrant_count = self._get_qdrant_vector_count(qdrant_collection)
            result["qdrant_count"] = qdrant_count
            
            # Calculate consistency score
            if pg_count == 0 and qdrant_count == 0:
                result["consistency_score"] = 1.0  # Both empty is consistent
                result["status"] = "empty"
            elif pg_count == 0 or qdrant_count == 0:
                result["consistency_score"] = 0.0  # One empty, one not
                result["status"] = "critical"
                result["inconsistencies"].append(
                    f"One archive empty: PG={pg_count}, Qdrant={qdrant_count}"
                )
            else:
                # Calculate ratio-based consistency
                smaller_count = min(pg_count, qdrant_count)
                larger_count = max(pg_count, qdrant_count)
                result["consistency_score"] = smaller_count / larger_count
                
                # Classify status
                if result["consistency_score"] >= self.consistency_thresholds["excellent"]:
                    result["status"] = "excellent"
                elif result["consistency_score"] >= self.consistency_thresholds["good"]:
                    result["status"] = "good"
                elif result["consistency_score"] >= self.consistency_thresholds["poor"]:
                    result["status"] = "poor"
                else:
                    result["status"] = "critical"
                
                # Add count discrepancy if significant
                count_diff = abs(pg_count - qdrant_count)
                if count_diff > 0:
                    result["inconsistencies"].append(
                        f"Count mismatch: PG={pg_count}, Qdrant={qdrant_count} (diff={count_diff})"
                    )
            
            # Detailed inconsistency analysis if requested
            if detailed and result["consistency_score"] < 1.0:
                detailed_inconsistencies = self._find_detailed_inconsistencies(
                    pg_table, qdrant_collection
                )
                result["detailed_inconsistencies"] = detailed_inconsistencies
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error inspecting {pg_table} ↔ {qdrant_collection}: {e}")
            result["status"] = "error"
            result["error"] = str(e)
            result["inconsistencies"].append(f"Inspection error: {e}")
            return result

    def _get_postgres_record_count(self, table_name: str) -> int:
        """Get record count from PostgreSQL table"""
        try:
            # Rollback any pending transaction first
            try:
                self.postgres_agent.connection.rollback()
            except:
                pass
            
            with self.postgres_agent.connection.cursor() as cursor:
                # Handle different table structures
                if table_name == "sentiment_scores":
                    # Count recent sentiment records (last 30 days)
                    cursor.execute("""
                        SELECT COUNT(*) FROM sentiment_scores 
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    """)
                elif table_name == "phrases":
                    # Count all phrases - try different column combinations
                    try:
                        cursor.execute("SELECT COUNT(*) FROM phrases WHERE embedded = true")
                    except:
                        # Fallback if embedded column doesn't exist
                        cursor.execute("SELECT COUNT(*) FROM phrases")
                elif table_name == "market_data":
                    # Count market data records - check if table exists first
                    try:
                        cursor.execute("SELECT COUNT(*) FROM market_data")
                    except:
                        # Table might not exist
                        return 0
                else:
                    # Generic count for unknown tables
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    except:
                        # Table doesn't exist
                        return 0
                
                result = cursor.fetchone()
                return result[0] if result else 0
                    
        except Exception as e:
            # Rollback on error
            try:
                self.postgres_agent.connection.rollback()
            except:
                pass
            logger.error(f"❌ Error counting PostgreSQL {table_name}: {e}")
            return 0

    def _get_qdrant_vector_count(self, collection_name: str) -> int:
        """Get vector count from Qdrant collection"""
        try:
            # Use scroll to get count (more reliable than collection info)
            scroll_result = self.qdrant_agent.client.scroll(
                collection_name=collection_name,
                limit=1,  # Just need count, not data
                with_payload=False,
                with_vectors=False
            )
            
            if scroll_result and len(scroll_result) >= 2:
                # scroll returns (points, next_page_offset)
                points = scroll_result[0] if scroll_result[0] else []
                
                # If we have points, try to get full count via count API
                if points:
                    try:
                        count_result = self.qdrant_agent.client.count(collection_name=collection_name)
                        if hasattr(count_result, 'count'):
                            return count_result.count
                        elif isinstance(count_result, dict) and 'count' in count_result:
                            return count_result['count']
                    except:
                        pass
                
                # Fallback: estimate from scroll (not accurate for large collections)
                return len(points)
            else:
                return 0
                
        except Exception as e:
            # Fallback to basic collection check
            try:
                # Check if collection exists at least
                collections = self.qdrant_agent.client.get_collections()
                collection_exists = any(c.name == collection_name for c in collections.collections)
                if collection_exists:
                    logger.warning(f"⚠️ Collection {collection_name} exists but count failed: {e}")
                    return 0  # Exists but can't count
                else:
                    logger.warning(f"⚠️ Collection {collection_name} doesn't exist")
                    return 0
            except Exception as e2:
                logger.error(f"❌ Error counting Qdrant {collection_name}: {e2}")
                return 0

    def _find_detailed_inconsistencies(
        self, 
        pg_table: str, 
        qdrant_collection: str
    ) -> Dict[str, Any]:
        """
        Find detailed inconsistencies between PostgreSQL and Qdrant
        
        Returns:
            dict: Detailed inconsistency analysis
        """
        try:
            # Sample recent records from both sources
            pg_sample = self._sample_postgres_records(pg_table, limit=100)
            qdrant_sample = self._sample_qdrant_points(qdrant_collection, limit=100)
            
            # Find orphaned records (in PG but not in Qdrant)
            pg_ids = {self._extract_record_id(record, pg_table) for record in pg_sample}
            qdrant_ids = {str(point.id) for point in qdrant_sample}
            
            orphaned_pg = pg_ids - qdrant_ids
            orphaned_qdrant = qdrant_ids - pg_ids
            
            return {
                "sample_size": {"pg": len(pg_sample), "qdrant": len(qdrant_sample)},
                "orphaned_postgres_records": len(orphaned_pg),
                "orphaned_qdrant_points": len(orphaned_qdrant),
                "orphaned_pg_sample": list(orphaned_pg)[:10],  # First 10 for debugging
                "orphaned_qdrant_sample": list(orphaned_qdrant)[:10]
            }
            
        except Exception as e:
            logger.error(f"❌ Error finding detailed inconsistencies: {e}")
            return {"error": str(e)}

    def _sample_postgres_records(self, table_name: str, limit: int = 100) -> List[Dict]:
        """Sample recent records from PostgreSQL table"""
        try:
            # Rollback any pending transaction first
            try:
                self.postgres_agent.connection.rollback()
            except:
                pass
                
            with self.postgres_agent.connection.cursor() as cursor:
                if table_name == "sentiment_scores":
                    cursor.execute("""
                        SELECT ticker, created_at, dedupe_key 
                        FROM sentiment_scores 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (limit,))
                    columns = ["ticker", "created_at", "dedupe_key"]
                elif table_name == "phrases":
                    try:
                        cursor.execute("""
                            SELECT id, phrase_text, source, created_at 
                            FROM phrases 
                            WHERE embedded = true
                            ORDER BY created_at DESC 
                            LIMIT %s
                        """, (limit,))
                        columns = ["id", "phrase_text", "source", "created_at"]
                    except:
                        # Fallback if columns don't exist
                        cursor.execute("""
                            SELECT id, phrase_text, source, created_at 
                            FROM phrases 
                            ORDER BY created_at DESC 
                            LIMIT %s
                        """, (limit,))
                        columns = ["id", "phrase_text", "source", "created_at"]
                else:
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,))
                        columns = [desc[0] for desc in cursor.description]
                        rows = cursor.fetchall()
                        return [dict(zip(columns, row)) for row in rows]
                    except Exception as table_error:
                        logger.warning(f"⚠️ Table {table_name} not accessible: {table_error}")
                        return []
                
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
                    
        except Exception as e:
            # Rollback on error
            try:
                self.postgres_agent.connection.rollback()
            except:
                pass
            logger.error(f"❌ Error sampling PostgreSQL {table_name}: {e}")
            return []

    def _sample_qdrant_points(self, collection_name: str, limit: int = 100):
        """Sample points from Qdrant collection"""
        try:
            # Get sample points using scroll
            result = self.qdrant_agent.client.scroll(
                collection_name=collection_name,
                limit=limit,
                with_payload=True
            )
            
            return result[0] if result else []
            
        except Exception as e:
            logger.error(f"❌ Error sampling Qdrant {collection_name}: {e}")
            return []

    def _extract_record_id(self, record: Dict, table_name: str) -> str:
        """Extract unique identifier from PostgreSQL record"""
        if table_name == "sentiment_scores":
            return record.get("dedupe_key", "")
        elif table_name == "phrases":
            return str(record.get("id", ""))
        else:
            # Use first available ID field
            for id_field in ["id", "dedupe_key", "ticker"]:
                if id_field in record:
                    return str(record[id_field])
            return ""

    def _trigger_healing_expedition(
        self, 
        pg_table: str, 
        qdrant_collection: str,
        inconsistencies: List[str]
    ) -> Dict[str, Any]:
        """
        Trigger healing expedition for critical inconsistencies
        
        Returns:
            dict: Healing expedition results
        """
        logger.warning(
            f"🚨 {self.name}: Triggering healing expedition for {pg_table} ↔ {qdrant_collection}"
        )
        
        healing_id = f"healing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Publish healing expedition event
            self.publish_event(
                event_type="healing.expedition_triggered",
                payload={
                    "healing_id": healing_id,
                    "pg_table": pg_table,
                    "qdrant_collection": qdrant_collection,
                    "inconsistencies": inconsistencies,
                    "priority": "critical",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Update statistics
            self.validation_stats["healing_expeditions_triggered"] += 1
            
            logger.info(f"✅ {self.name}: Healing expedition {healing_id} triggered")
            
            return {
                "success": True,
                "healing_id": healing_id,
                "message": "Healing expedition triggered successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ {self.name}: Failed to trigger healing expedition: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_recommendations(self, inspection_results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on inspection results"""
        recommendations = []
        
        overall_consistency = inspection_results["overall_consistency"]
        
        if overall_consistency >= self.consistency_thresholds["excellent"]:
            recommendations.append("✅ Archives are in excellent condition")
        elif overall_consistency >= self.consistency_thresholds["good"]:
            recommendations.append("⚠️ Consider minor healing expedition for optimization")
        elif overall_consistency >= self.consistency_thresholds["poor"]:
            recommendations.append("🔧 Schedule healing expedition within 24 hours")
        else:
            recommendations.append("🚨 CRITICAL: Immediate healing expedition required")
        
        # Collection-specific recommendations
        for table_name, collection_result in inspection_results["collections"].items():
            if collection_result["status"] == "critical":
                recommendations.append(
                    f"🚨 {table_name}: Critical inconsistency - "
                    f"{collection_result['consistency_score']:.1%} consistency"
                )
            elif collection_result["status"] == "error":
                recommendations.append(f"❌ {table_name}: Inspection error - manual review needed")
        
        return recommendations

    def _update_inspection_stats(self, inspection_results: Dict[str, Any]) -> None:
        """Update inspection statistics"""
        self.validation_stats["inspections_completed"] += 1
        self.validation_stats["last_inspection"] = datetime.now().isoformat()
        
        # Count inconsistencies
        inconsistency_count = 0
        for collection_result in inspection_results["collections"].values():
            inconsistency_count += len(collection_result.get("inconsistencies", []))
        
        self.validation_stats["inconsistencies_found"] += inconsistency_count
        
        # Update average consistency score
        current_avg = self.validation_stats["average_consistency_score"]
        total_inspections = self.validation_stats["inspections_completed"]
        new_score = inspection_results["overall_consistency"]
        
        self.validation_stats["average_consistency_score"] = (
            (current_avg * (total_inspections - 1) + new_score) / total_inspections
        )

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation statistics"""
        return {
            "inspector": self.name,
            "statistics": self.validation_stats.copy(),
            "thresholds": self.consistency_thresholds.copy(),
            "collection_mappings": self.collection_mappings.copy(),
            "health_status": "healthy" if self.is_healthy() else "unhealthy"
        }


# CLI Test
if __name__ == "__main__":
    import sys
    
    # Create inspector
    inspector = Inspector()
    
    # Parse command line arguments
    scope = sys.argv[1] if len(sys.argv) > 1 else "all"
    healing = "--no-healing" not in sys.argv
    detailed = "--detailed" in sys.argv
    
    print(f"🔬 Testing Inspector Agent")
    print(f"   Scope: {scope}")
    print(f"   Healing: {healing}")
    print(f"   Detailed: {detailed}")
    print("=" * 50)
    
    # Run inspection
    result = inspector.execute(
        scope=scope,
        healing=healing, 
        detailed=detailed
    )
    
    if result.get("success", True):  # Default to True if not specified
        print(f"✅ Inspection completed: {result['inspection_id']}")
        print(f"   Overall Consistency: {result['overall_consistency']:.1%}")
        print(f"   Collections Inspected: {len(result['collections'])}")
        
        for table_name, collection_result in result["collections"].items():
            status_icon = {
                "excellent": "✅", "good": "✅", "poor": "⚠️", 
                "critical": "🚨", "error": "❌", "empty": "📭"
            }.get(collection_result["status"], "❓")
            
            print(f"   {status_icon} {table_name}: {collection_result['consistency_score']:.1%} "
                  f"(PG: {collection_result['pg_count']}, Qdrant: {collection_result['qdrant_count']})")
        
        if result["recommendations"]:
            print("\n📋 Recommendations:")
            for rec in result["recommendations"]:
                print(f"   • {rec}")
                
    else:
        print(f"❌ Inspection failed: {result.get('error', 'Unknown error')}")
    
    # Print validation summary
    summary = inspector.get_validation_summary()
    print(f"\n📊 Inspector Statistics:")
    print(f"   Inspections: {summary['statistics']['inspections_completed']}")
    print(f"   Inconsistencies Found: {summary['statistics']['inconsistencies_found']}")
    print(f"   Healing Triggered: {summary['statistics']['healing_expeditions_triggered']}")
    print(f"   Average Consistency: {summary['statistics']['average_consistency_score']:.1%}")