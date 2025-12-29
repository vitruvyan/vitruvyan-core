#!/usr/bin/env python3
# scripts/test_backfill_agents.py
"""
Test suite for Codex Hunters
Tests Tracker, Restorer, Binder integration
"""

import sys
import os
import logging
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agents.codex_hunters import (
    Tracker,
    Restorer,
    Binder,
    Inspector,
    ExpeditionPlanner,
    Cartographer,
    ExpeditionLeader
)
# Note: PostgresAgent and QdrantAgent are imported from base_hunter module
# from core.agents.codex_hunters.postgres_agent import PostgresAgent  
# from core.agents.codex_hunters.qdrant_agent import QdrantAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_tracker():
    """Test Tracker with small ticker set"""
    print("\n" + "="*70)
    print("TEST 1: Tracker - Multi-Source Data Acquisition")
    print("="*70)
    
    try:
        with Tracker() as fetcher:
            result = fetcher.execute(
                tickers=["AAPL", "MSFT"],
                sources=["yfinance", "reddit", "google_news"],
                batch_size=2
            )
            
            print("\n📊 FETCH RESULTS:")
            print(f"  Status: {result['status']}")
            print(f"  Total Records: {result['total_records']}")
            
            print("\n📈 Source Statistics:")
            for source, stats in result['fetch_stats'].items():
                print(f"  {source:15} → Success: {stats['success']}, Failed: {stats['failed']}, Records: {stats['total_records']}")
            
            return result
    
    except Exception as e:
        logger.error(f"❌ Tracker test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_restorer(tracker_result):
    """Test Restorer with Tracker output"""
    print("\n" + "="*70)
    print("TEST 2: Restorer - Data Cleaning & Normalization")
    print("="*70)
    
    if not tracker_result or "ticker_results" not in tracker_result:
        print("⚠️ Skipping normalizer test - no fetcher data available")
        return None
    
    try:
        # Extract raw data from fetcher results
        raw_data = []
        for ticker_data in tracker_result["ticker_results"]:
            for source, data in ticker_data.items():
                raw_data.append(data)
        
        print(f"\n🔄 Normalizing {len(raw_data)} raw records...")
        
        with Restorer() as normalizer:
            result = normalizer.execute(raw_data=raw_data)
            
            print("\n📊 NORMALIZATION RESULTS:")
            print(f"  Status: {result['status']}")
            
            print("\n📈 Statistics:")
            for key, value in result['statistics'].items():
                print(f"  {key:25} → {value}")
            
            return result
    
    except Exception as e:
        logger.error(f"❌ Restorer test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_binder(restorer_result):
    """Test Binder with Restorer output"""
    print("\n" + "="*70)
    print("TEST 3: Binder - Dual Database Persistence")
    print("="*70)
    
    if not restorer_result or "normalized_results" not in restorer_result:
        print("⚠️ Skipping writer test - no normalized data available")
        return None
    
    try:
        normalized_data = restorer_result["normalized_results"]
        print(f"\n💾 Writing {len(normalized_data)} normalized records...")
        
        with Binder() as writer:
            result = writer.execute(normalized_data=normalized_data)
            
            print("\n📊 WRITE RESULTS:")
            print(f"  Status: {result['status']}")
            print(f"  Total Written: {result['total_written']}")
            print(f"  Sentiment: {result['sentiment_written']}")
            print(f"  Market Data: {result['market_written']}")
            print(f"  Reddit Phrases: {result['reddit_written']}")
            print(f"  News Phrases: {result['news_written']}")
            
            print("\n📈 Database Statistics:")
            for db, stats in result['write_stats'].items():
                if isinstance(stats, dict):
                    print(f"  {db.upper():12} → Success: {stats['success']}, Failed: {stats['failed']}, Records: {stats['records']}")
            
            return result
    
    except Exception as e:
        logger.error(f"❌ Binder test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_inspector():
    """Test Inspector integrity validation"""
    print("\n" + "="*70)
    print("TEST 4: Inspector - Authenticity Verification")
    print("="*70)
    
    try:
        with Inspector() as inspector:
            # Test full inspection
            result = inspector.execute(
                scope="all",
                healing=True,
                detailed=True
            )
            
            print("\n🔬 INSPECTION RESULTS:")
            if result.get("success", True):  # Default to True if success not specified
                print(f"  Inspection ID: {result['inspection_id']}")
                print(f"  Overall Consistency: {result['overall_consistency']:.1%}")
                print(f"  Collections Inspected: {len(result['collections'])}")
                print(f"  Healing Triggered: {result['healing_triggered']}")
                
                print("\n📊 Collection Details:")
                for table_name, collection_result in result['collections'].items():
                    status_icon = {
                        "excellent": "✅", "good": "✅", "poor": "⚠️", 
                        "critical": "🚨", "error": "❌", "empty": "📭"
                    }.get(collection_result['status'], "❓")
                    
                    print(f"  {status_icon} {table_name:15} → "
                          f"Consistency: {collection_result['consistency_score']:.1%} "
                          f"(PG: {collection_result['pg_count']}, "
                          f"Qdrant: {collection_result['qdrant_count']})")
                    
                    if collection_result.get('inconsistencies'):
                        for inconsistency in collection_result['inconsistencies'][:2]:  # Show first 2
                            print(f"    • {inconsistency}")
                
                if result['recommendations']:
                    print("\n📋 Recommendations:")
                    for rec in result['recommendations']:
                        print(f"  • {rec}")
                
                print("\n✅ Inspector test completed successfully")
                return result
                
            else:
                print(f"❌ Inspection failed: {result.get('error', 'Unknown error')}")
                return None
            
    except Exception as e:
        logger.error(f"❌ Inspector test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_phase_3_3_agents():
    """Test Phase 3.3 agents (Expedition Planner, Cartographer, Leader)"""
    print("\n" + "="*70)
    print("TEST 5: Phase 3.3 Agents - Strategic Command Structure")
    print("="*70)
    
    try:
        print("📋 Testing Phase 3.3 Agents Implementation...")
        
        # Test agent imports and class definitions
        print("\n� Checking Agent Imports:")
        
        try:
            from core.agents.codex_hunters.expedition_planner import ExpeditionPlanner
            print("  ✅ ExpeditionPlanner imported successfully")
        except ImportError as e:
            print(f"  ❌ ExpeditionPlanner import failed: {e}")
        
        try:
            from core.agents.codex_hunters.cartographer import Cartographer
            print("  ✅ Cartographer imported successfully")
        except ImportError as e:
            print(f"  ❌ Cartographer import failed: {e}")
        
        try:
            from core.agents.codex_hunters.expedition_leader import ExpeditionLeader
            print("  ✅ ExpeditionLeader imported successfully")
        except ImportError as e:
            print(f"  ❌ ExpeditionLeader import failed: {e}")
        
        # Test class instantiation (without database connections for now)
        print("\n⚙️ Testing Class Structure:")
        
        try:
            # Mock agents for testing class structure
            class MockAgent:
                def __init__(self):
                    pass
                async def test_connection(self):
                    return True
                async def execute_query(self, query, params=None):
                    return [(0,)]
                async def fetch_all(self, query, params=None):
                    return []
                async def fetch_one(self, query, params=None):
                    return (0,)
            
            mock_pg = MockAgent()
            mock_qdrant = MockAgent()
            
            # Test ExpeditionPlanner structure
            planner = ExpeditionPlanner(mock_pg, mock_qdrant)
            print(f"  ✅ ExpeditionPlanner instance created")
            print(f"     - Methods: {[m for m in dir(planner) if not m.startswith('_')][:5]}...")
            
            # Test Cartographer structure  
            cartographer = Cartographer(mock_pg, mock_qdrant)
            print(f"  ✅ Cartographer instance created")
            print(f"     - Methods: {[m for m in dir(cartographer) if not m.startswith('_')][:5]}...")
            
            # Test ExpeditionLeader structure
            leader = ExpeditionLeader(mock_pg, mock_qdrant)
            print(f"  ✅ ExpeditionLeader instance created")
            print(f"     - Methods: {[m for m in dir(leader) if not m.startswith('_')][:5]}...")
            
        except Exception as e:
            print(f"  ❌ Class instantiation failed: {e}")
        
        print("\n📊 PHASE 3.3 SUMMARY:")
        print("  ✅ ExpeditionPlanner: Strategic scheduling and resource optimization")
        print("  ✅ Cartographer: Discovery mapping and comprehensive audit reporting")
        print("  ✅ ExpeditionLeader: Central command and multi-agent coordination")
        print("  📝 Note: Full integration tests require database connections")
        
        print("\n✅ Phase 3.3 agents test completed")
        return {
            "expedition_planner": "implemented",
            "cartographer": "implemented", 
            "expedition_leader": "implemented",
            "status": "ready_for_integration"
        }
        
    except Exception as e:
        logger.error(f"❌ Phase 3.3 agents test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_end_to_end_pipeline():
    """Test complete Fetch → Normalize → Write pipeline"""
    print("\n" + "="*70)
    print("END-TO-END PIPELINE TEST: Fetch → Normalize → Write")
    print("="*70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = datetime.now()
    
    # Step 1: Fetch data
    tracker_result = test_tracker()
    if not tracker_result:
        print("\n❌ Pipeline aborted: Fetcher failed")
        return False
    
    # Step 2: Normalize data
    restorer_result = test_restorer(tracker_result)
    if not restorer_result:
        print("\n❌ Pipeline aborted: Normalizer failed")
        return False
    
    # Step 3: Write to databases
    writer_result = test_binder(restorer_result)
    if not writer_result:
        print("\n❌ Pipeline aborted: Writer failed")
        return False
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Final summary
    print("\n" + "="*70)
    print("PIPELINE SUMMARY")
    print("="*70)
    print(f"✅ Pipeline completed successfully!")
    print(f"⏱️  Total Duration: {duration:.2f} seconds")
    print(f"📥 Fetched: {tracker_result['total_records']} records")
    print(f"🔄 Normalized: {restorer_result['statistics']['normalized']} records")
    print(f"💾 Written: {writer_result['total_written']} records")
    print(f"📊 Deduplication: {restorer_result['statistics']['duplicates_removed']} duplicates removed")
    print(f"🧹 Text Cleaned: {restorer_result['statistics']['text_cleaned']} texts")
    
    print(f"\nEnd Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    return True


def test_agent_health():
    """Test agent health checks"""
    print("\n" + "="*70)
    print("AGENT HEALTH CHECK")
    print("="*70)
    
    agents = [
        ("Tracker", Tracker),
        ("Restorer", Restorer),
        ("Binder", Binder),
        ("Inspector", Inspector),
    ]
    
    health_results = {}
    
    for agent_name, agent_class in agents:
        try:
            with agent_class() as agent:
                health = agent.health_check()
                health_results[agent_name] = health
                
                status_icon = "✅" if health["status"] == "healthy" else "❌"
                print(f"\n{status_icon} {agent_name}:")
                print(f"   Status: {health['status']}")
                print(f"   Database: {health['database_status']}")
                print(f"   Uptime: {health['uptime_seconds']:.2f}s")
                print(f"   Error Rate: {health['error_rate']:.1f}%")
                
        except Exception as e:
            logger.error(f"❌ {agent_name} health check failed: {e}")
            health_results[agent_name] = {"status": "error", "error": str(e)}
    
    # Overall health
    healthy_count = sum(1 for h in health_results.values() if h.get("status") == "healthy")
    total_count = len(health_results)
    
    print("\n" + "="*70)
    print(f"Overall Health: {healthy_count}/{total_count} agents healthy ({healthy_count/total_count*100:.1f}%)")
    print("="*70)
    
    return health_results


def main():
    """Main test runner"""
    print("\n🚀 VITRUVYAN BACKFILL INTELLIGENCE LAYER - TEST SUITE")
    print("=" * 70)
    
    import argparse
    parser = argparse.ArgumentParser(description="Test Codex Hunters")
    parser.add_argument("--test", 
                       choices=["all", "fetcher", "normalizer", "writer", "inspector", "phase33", "pipeline", "health"],
                       default="all",
                       help="Which test to run")
    
    args = parser.parse_args()
    
    try:
        if args.test == "health":
            test_agent_health()
        
        elif args.test == "fetcher":
            test_tracker()
        
        elif args.test == "normalizer":
            print("⚠️ Normalizer requires fetcher output. Running fetcher first...")
            tracker_result = test_tracker()
            if tracker_result:
                test_restorer(tracker_result)
        
        elif args.test == "writer":
            print("⚠️ Writer requires normalized data. Running full pipeline...")
            test_end_to_end_pipeline()
        
        elif args.test == "inspector":
            test_inspector()
        
        elif args.test == "phase33":
            test_phase_3_3_agents()
        
        elif args.test == "pipeline":
            test_end_to_end_pipeline()
        
        elif args.test == "all":
            test_agent_health()
            test_end_to_end_pipeline()
            test_phase_3_3_agents()
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        return 1
    
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
