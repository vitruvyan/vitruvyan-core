#!/usr/bin/env python3
"""
🧪 VAULT KEEPERS TESTING SCRIPT
===============================
Test script per verificare il sistema Vitruvyan Vault Keepers

Uso:
    python3 scripts/test_vault_keepers.py --test [all|base|sentinel|archivist|courier|chamberlain]
"""

import sys
import os
import asyncio
import logging
import argparse
from pathlib import Path
from datetime import datetime
import json
import traceback

# Add project root to Python path
sys.path.insert(0, '/workspaces/vitruvyan')

# Import Vault Keepers
from core.agents.vault_keepers.keeper import BaseKeeper, VaultConfig, VaultEvent, BackupMode
from core.agents.vault_keepers.sentinel import SentinelAgent
from core.agents.vault_keepers.archivist import ArchivistAgent
from core.agents.vault_keepers.courier import CourierAgent
from core.agents.vault_keepers.chamberlain import ChamberlainAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VaultKeepersTester:
    """Tester class for Vault Keepers system"""
    
    def __init__(self):
        self.test_results = {}
        self.config = None
        
    def setup_test_environment(self):
        """Setup test environment and configuration"""
        logger.info("🏗️ Setting up test environment...")
        
        try:
            # Create test configuration
            self.config = VaultConfig()
            logger.info("✅ VaultConfig created successfully")
            
            # Create test directories
            test_vault_path = Path("/var/vitruvyan/test_vault")
            test_vault_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Test vault directory created: {test_vault_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup test environment: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def test_base_keeper(self):
        """Test BaseKeeper foundation"""
        logger.info("🧪 Testing BaseKeeper foundation...")
        
        test_results = {
            "test_name": "BaseKeeper Foundation",
            "started_at": datetime.utcnow().isoformat(),
            "tests": []
        }
        
        try:
            # Test 1: BaseKeeper initialization
            logger.info("   📝 Test 1: BaseKeeper initialization")
            keeper = BaseKeeper(self.config)
            test_results["tests"].append({
                "name": "BaseKeeper_init",
                "status": "passed",
                "message": f"BaseKeeper initialized: {keeper}"
            })
            
            # Test 2: PostgresAgent connection
            logger.info("   📝 Test 2: PostgresAgent connection")
            try:
                # Simple connection test
                test_query = "SELECT 1 as test_connection"
                result = keeper.postgres_agent.fetch_all(test_query, ())
                if result and result[0][0] == 1:
                    test_results["tests"].append({
                        "name": "PostgresAgent_connection",
                        "status": "passed",
                        "message": "PostgresAgent connection successful"
                    })
                else:
                    test_results["tests"].append({
                        "name": "PostgresAgent_connection",
                        "status": "failed",
                        "message": f"Unexpected result: {result}"
                    })
            except Exception as e:
                test_results["tests"].append({
                    "name": "PostgresAgent_connection",
                    "status": "failed",
                    "message": f"PostgresAgent error: {e}"
                })
            
            # Test 3: QdrantAgent connection
            logger.info("   📝 Test 3: QdrantAgent connection")
            try:
                # Simple Qdrant test (if available)
                collections = keeper.qdrant_agent.list_collections()
                test_results["tests"].append({
                    "name": "QdrantAgent_connection",
                    "status": "passed",
                    "message": f"QdrantAgent connected, collections: {len(collections) if collections else 0}"
                })
            except Exception as e:
                test_results["tests"].append({
                    "name": "QdrantAgent_connection",
                    "status": "warning",
                    "message": f"QdrantAgent not available: {e}"
                })
            
            # Test 4: Event publication
            logger.info("   📝 Test 4: Event publication")
            keeper.publish_event("test.base_keeper", {"test": True, "timestamp": datetime.utcnow().isoformat()})
            test_results["tests"].append({
                "name": "Event_publication",
                "status": "passed",
                "message": "Event published successfully"
            })
            
            # Test 5: File hash calculation
            logger.info("   📝 Test 5: File hash calculation")
            test_file = Path("/tmp/test_hash.txt")
            test_file.write_text("Test content for hash calculation")
            
            hash_result = keeper.calculate_file_hash(str(test_file))
            if hash_result and len(hash_result) == 64:  # SHA256 length
                test_results["tests"].append({
                    "name": "File_hash_calculation",
                    "status": "passed",
                    "message": f"Hash calculated: {hash_result[:16]}..."
                })
            else:
                test_results["tests"].append({
                    "name": "File_hash_calculation",
                    "status": "failed",
                    "message": f"Invalid hash: {hash_result}"
                })
            
            test_file.unlink()  # Cleanup
            
        except Exception as e:
            logger.error(f"❌ BaseKeeper test failed: {e}")
            test_results["tests"].append({
                "name": "BaseKeeper_test",
                "status": "failed",
                "message": f"Test exception: {e}"
            })
        
        test_results["completed_at"] = datetime.utcnow().isoformat()
        test_results["passed_tests"] = len([t for t in test_results["tests"] if t["status"] == "passed"])
        test_results["total_tests"] = len(test_results["tests"])
        
        self.test_results["base_keeper"] = test_results
        logger.info(f"✅ BaseKeeper tests completed: {test_results['passed_tests']}/{test_results['total_tests']} passed")
        
        return test_results
    
    async def test_sentinel_agent(self):
        """Test SentinelAgent functionality"""
        logger.info("🔍 Testing SentinelAgent...")
        
        test_results = {
            "test_name": "Sentinel Agent",
            "started_at": datetime.utcnow().isoformat(),
            "tests": []
        }
        
        try:
            # Test 1: Sentinel initialization
            logger.info("   📝 Test 1: Sentinel initialization")
            sentinel = SentinelAgent(self.config)
            test_results["tests"].append({
                "name": "Sentinel_init",
                "status": "passed",
                "message": f"Sentinel initialized: {sentinel}"
            })
            
            # Test 2: Watch status (before starting)
            logger.info("   📝 Test 2: Initial watch status")
            status = sentinel.get_watch_status()
            if not status["watching"]:
                test_results["tests"].append({
                    "name": "Initial_watch_status",
                    "status": "passed",
                    "message": "Sentinel not watching initially (correct)"
                })
            else:
                test_results["tests"].append({
                    "name": "Initial_watch_status",
                    "status": "failed",
                    "message": "Sentinel should not be watching initially"
                })
            
            # Test 3: Start watch (brief test)
            logger.info("   📝 Test 3: Start watch functionality")
            # Start watch in background
            watch_task = asyncio.create_task(sentinel.start_watch())
            
            # Wait a bit for watch to start
            await asyncio.sleep(2)
            
            # Check watch status
            status = sentinel.get_watch_status()
            if status["watching"]:
                test_results["tests"].append({
                    "name": "Start_watch",
                    "status": "passed",
                    "message": "Watch started successfully"
                })
            else:
                test_results["tests"].append({
                    "name": "Start_watch",
                    "status": "failed",
                    "message": "Watch failed to start"
                })
            
            # Test 4: External trigger handling
            logger.info("   📝 Test 4: External trigger handling")
            trigger_data = {
                "severity": "medium",
                "source": "test_script",
                "details": "Test trigger for Sentinel"
            }
            
            await sentinel.handle_external_trigger("test_trigger", trigger_data)
            test_results["tests"].append({
                "name": "External_trigger",
                "status": "passed",
                "message": "External trigger handled"
            })
            
            # Stop watch
            await sentinel.stop_watch()
            watch_task.cancel()
            
            try:
                await watch_task
            except asyncio.CancelledError:
                pass
            
            test_results["tests"].append({
                "name": "Stop_watch",
                "status": "passed",
                "message": "Watch stopped successfully"
            })
            
        except Exception as e:
            logger.error(f"❌ Sentinel test failed: {e}")
            test_results["tests"].append({
                "name": "Sentinel_test",
                "status": "failed",
                "message": f"Test exception: {e}"
            })
        
        test_results["completed_at"] = datetime.utcnow().isoformat()
        test_results["passed_tests"] = len([t for t in test_results["tests"] if t["status"] == "passed"])
        test_results["total_tests"] = len(test_results["tests"])
        
        self.test_results["sentinel"] = test_results
        logger.info(f"✅ Sentinel tests completed: {test_results['passed_tests']}/{test_results['total_tests']} passed")
        
        return test_results
    
    async def test_archivist_agent(self):
        """Test ArchivistAgent functionality"""
        logger.info("📚 Testing ArchivistAgent...")
        
        test_results = {
            "test_name": "Archivist Agent",
            "started_at": datetime.utcnow().isoformat(),
            "tests": []
        }
        
        try:
            # Test 1: Archivist initialization
            logger.info("   📝 Test 1: Archivist initialization")
            archivist = ArchivistAgent(self.config)
            test_results["tests"].append({
                "name": "Archivist_init",
                "status": "passed",
                "message": f"Archivist initialized: {archivist}"
            })
            
            # Test 2: Archive status
            logger.info("   📝 Test 2: Archive status check")
            status = archivist.get_archive_status()
            test_results["tests"].append({
                "name": "Archive_status",
                "status": "passed",
                "message": f"Archive status retrieved: {status['total_backups']} backups"
            })
            
            # Test 3: Incremental backup test
            logger.info("   📝 Test 3: Incremental backup execution")
            try:
                threat_data = {
                    "threats": [
                        {
                            "type": "test_threat",
                            "severity": "low",
                            "source": "table:test_table"
                        }
                    ]
                }
                
                backup_result = await archivist.execute_backup(BackupMode.INCREMENTAL, threat_data)
                
                if backup_result and backup_result.get("backup_id"):
                    test_results["tests"].append({
                        "name": "Incremental_backup",
                        "status": "passed",
                        "message": f"Backup completed: {backup_result['backup_id']}"
                    })
                else:
                    test_results["tests"].append({
                        "name": "Incremental_backup",
                        "status": "failed",
                        "message": f"Backup failed: {backup_result}"
                    })
            except Exception as e:
                test_results["tests"].append({
                    "name": "Incremental_backup",
                    "status": "warning",
                    "message": f"Backup test failed (expected in test env): {e}"
                })
            
            # Test 4: Archive cleanup (dry run)
            logger.info("   📝 Test 4: Archive cleanup test")
            try:
                # Don't actually cleanup, just test the method exists
                if hasattr(archivist, 'cleanup_old_archives'):
                    test_results["tests"].append({
                        "name": "Archive_cleanup",
                        "status": "passed",
                        "message": "Archive cleanup method available"
                    })
                else:
                    test_results["tests"].append({
                        "name": "Archive_cleanup",
                        "status": "failed",
                        "message": "Archive cleanup method missing"
                    })
            except Exception as e:
                test_results["tests"].append({
                    "name": "Archive_cleanup",
                    "status": "warning",
                    "message": f"Cleanup test failed: {e}"
                })
            
        except Exception as e:
            logger.error(f"❌ Archivist test failed: {e}")
            test_results["tests"].append({
                "name": "Archivist_test",
                "status": "failed",
                "message": f"Test exception: {e}"
            })
        
        test_results["completed_at"] = datetime.utcnow().isoformat()
        test_results["passed_tests"] = len([t for t in test_results["tests"] if t["status"] == "passed"])
        test_results["total_tests"] = len(test_results["tests"])
        
        self.test_results["archivist"] = test_results
        logger.info(f"✅ Archivist tests completed: {test_results['passed_tests']}/{test_results['total_tests']} passed")
        
        return test_results
    
    async def test_courier_agent(self):
        """Test CourierAgent functionality"""
        logger.info("🚀 Testing CourierAgent...")
        
        test_results = {
            "test_name": "Courier Agent",
            "started_at": datetime.utcnow().isoformat(),
            "tests": []
        }
        
        try:
            # Test 1: Courier initialization
            logger.info("   📝 Test 1: Courier initialization")
            courier = CourierAgent(self.config)
            test_results["tests"].append({
                "name": "Courier_init",
                "status": "passed",
                "message": f"Courier initialized: {courier}"
            })
            
            # Test 2: Delivery status
            logger.info("   📝 Test 2: Delivery status check")
            status = courier.get_delivery_status()
            test_results["tests"].append({
                "name": "Delivery_status",
                "status": "passed",
                "message": f"Status retrieved: {status['delivery_channels']['total']} channels"
            })
            
            # Test 3: Start delivery service
            logger.info("   📝 Test 3: Start delivery service")
            await courier.start_delivery_service()
            
            status = courier.get_delivery_status()
            if status["service_running"]:
                test_results["tests"].append({
                    "name": "Start_delivery_service",
                    "status": "passed",
                    "message": "Delivery service started"
                })
            else:
                test_results["tests"].append({
                    "name": "Start_delivery_service",
                    "status": "failed",
                    "message": "Delivery service failed to start"
                })
            
            # Test 4: Test delivery channels
            logger.info("   📝 Test 4: Test delivery channels")
            channel_test_result = await courier.test_delivery_channels()
            
            success_rate = channel_test_result.get("success_rate", 0)
            test_results["tests"].append({
                "name": "Test_delivery_channels",
                "status": "passed" if success_rate > 0 else "warning",
                "message": f"Channel tests: {success_rate}% success rate"
            })
            
            # Test 5: Stop delivery service
            logger.info("   📝 Test 5: Stop delivery service")
            await courier.stop_delivery_service()
            test_results["tests"].append({
                "name": "Stop_delivery_service",
                "status": "passed",
                "message": "Delivery service stopped"
            })
            
        except Exception as e:
            logger.error(f"❌ Courier test failed: {e}")
            test_results["tests"].append({
                "name": "Courier_test",
                "status": "failed",
                "message": f"Test exception: {e}"
            })
        
        test_results["completed_at"] = datetime.utcnow().isoformat()
        test_results["passed_tests"] = len([t for t in test_results["tests"] if t["status"] == "passed"])
        test_results["total_tests"] = len(test_results["tests"])
        
        self.test_results["courier"] = test_results
        logger.info(f"✅ Courier tests completed: {test_results['passed_tests']}/{test_results['total_tests']} passed")
        
        return test_results
    
    async def test_chamberlain_agent(self):
        """Test ChamberlainAgent functionality"""
        logger.info("🛡️ Testing ChamberlainAgent...")
        
        test_results = {
            "test_name": "Chamberlain Agent",
            "started_at": datetime.utcnow().isoformat(),
            "tests": []
        }
        
        try:
            # Test 1: Chamberlain initialization
            logger.info("   📝 Test 1: Chamberlain initialization")
            chamberlain = ChamberlainAgent(self.config)
            test_results["tests"].append({
                "name": "Chamberlain_init",
                "status": "passed",
                "message": f"Chamberlain initialized: {chamberlain}"
            })
            
            # Test 2: Vault status
            logger.info("   📝 Test 2: Vault status check")
            status = chamberlain.get_vault_status()
            
            if status and "chamberlain" in status:
                test_results["tests"].append({
                    "name": "Vault_status",
                    "status": "passed",
                    "message": f"Vault status retrieved, health: {status['chamberlain']['health_score']}"
                })
            else:
                test_results["tests"].append({
                    "name": "Vault_status",
                    "status": "failed",
                    "message": f"Invalid vault status: {status}"
                })
            
            # Test 3: Backup trigger handling
            logger.info("   📝 Test 3: Backup trigger handling")
            trigger_data = {
                "severity": "medium",
                "threats": [
                    {
                        "type": "test_threat",
                        "severity": "low",
                        "source": "test_script"
                    }
                ]
            }
            
            workflow_id = await chamberlain.handle_backup_trigger("test_script", trigger_data)
            
            if workflow_id:
                test_results["tests"].append({
                    "name": "Backup_trigger",
                    "status": "passed",
                    "message": f"Backup trigger handled: {workflow_id}"
                })
            else:
                test_results["tests"].append({
                    "name": "Backup_trigger",
                    "status": "failed",
                    "message": "Backup trigger failed"
                })
            
            # Test 4: Workflow history
            logger.info("   📝 Test 4: Workflow history")
            history = chamberlain.get_workflow_history(limit=5)
            test_results["tests"].append({
                "name": "Workflow_history",
                "status": "passed",
                "message": f"Retrieved {len(history)} workflow records"
            })
            
        except Exception as e:
            logger.error(f"❌ Chamberlain test failed: {e}")
            test_results["tests"].append({
                "name": "Chamberlain_test",
                "status": "failed",
                "message": f"Test exception: {e}"
            })
        
        test_results["completed_at"] = datetime.utcnow().isoformat()
        test_results["passed_tests"] = len([t for t in test_results["tests"] if t["status"] == "passed"])
        test_results["total_tests"] = len(test_results["tests"])
        
        self.test_results["chamberlain"] = test_results
        logger.info(f"✅ Chamberlain tests completed: {test_results['passed_tests']}/{test_results['total_tests']} passed")
        
        return test_results
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📊 Generating test report...")
        
        report = {
            "test_session": {
                "started_at": datetime.utcnow().isoformat(),
                "environment": "VPS",
                "python_version": sys.version,
                "project_path": "/workspaces/vitruvyan"
            },
            "summary": {
                "total_test_suites": len(self.test_results),
                "passed_suites": 0,
                "failed_suites": 0,
                "total_individual_tests": 0,
                "passed_individual_tests": 0,
                "failed_individual_tests": 0
            },
            "test_results": self.test_results
        }
        
        # Calculate summary statistics
        for suite_name, suite_result in self.test_results.items():
            passed_tests = suite_result.get("passed_tests", 0)
            total_tests = suite_result.get("total_tests", 0)
            
            if passed_tests == total_tests and total_tests > 0:
                report["summary"]["passed_suites"] += 1
            else:
                report["summary"]["failed_suites"] += 1
            
            report["summary"]["total_individual_tests"] += total_tests
            report["summary"]["passed_individual_tests"] += passed_tests
            report["summary"]["failed_individual_tests"] += (total_tests - passed_tests)
        
        # Save report
        report_file = Path("/tmp/vault_keepers_test_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Test report saved: {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("🏰 VITRUVYAN VAULT KEEPERS - TEST REPORT")
        print("="*60)
        print(f"📊 Test Suites: {report['summary']['passed_suites']}/{report['summary']['total_test_suites']} passed")
        print(f"🧪 Individual Tests: {report['summary']['passed_individual_tests']}/{report['summary']['total_individual_tests']} passed")
        print(f"✅ Success Rate: {(report['summary']['passed_individual_tests']/max(report['summary']['total_individual_tests'],1)*100):.1f}%")
        print("="*60)
        
        for suite_name, suite_result in self.test_results.items():
            status_emoji = "✅" if suite_result.get("passed_tests", 0) == suite_result.get("total_tests", 0) else "⚠️"
            print(f"{status_emoji} {suite_result['test_name']}: {suite_result.get('passed_tests', 0)}/{suite_result.get('total_tests', 0)}")
        
        print("="*60)
        
        return report

async def main():
    """Main test execution function"""
    
    parser = argparse.ArgumentParser(description='Test Vitruvyan Vault Keepers')
    parser.add_argument('--test', choices=['all', 'base', 'sentinel', 'archivist', 'courier', 'chamberlain'], 
                       default='all', help='Which tests to run')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tester = VaultKeepersTester()
    
    # Setup environment
    if not tester.setup_test_environment():
        logger.error("❌ Failed to setup test environment")
        return 1
    
    # Run selected tests
    if args.test in ['all', 'base']:
        await tester.test_base_keeper()
    
    if args.test in ['all', 'sentinel']:
        await tester.test_sentinel_agent()
    
    if args.test in ['all', 'archivist']:
        await tester.test_archivist_agent()
    
    if args.test in ['all', 'courier']:
        await tester.test_courier_agent()
    
    if args.test in ['all', 'chamberlain']:
        await tester.test_chamberlain_agent()
    
    # Generate report
    report = tester.generate_test_report()
    
    # Return appropriate exit code
    if report["summary"]["failed_suites"] == 0:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.warning(f"⚠️ {report['summary']['failed_suites']} test suite(s) failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("🛑 Test execution interrupted")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)