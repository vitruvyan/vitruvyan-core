#!/usr/bin/env python3
"""
🏰 VITRUVYAN VAULT KEEPERS - END-TO-END TEST
============================================
Test completo del workflow orchestrato dal Chamberlain

Test Phases:
1. Initialization - Verifica inizializzazione tutti i keeper
2. Detection - Test Sentinel monitoring e threat detection  
3. Preparation - Test Archivist preparation e space check
4. Execution - Test backup creation (mode: incremental)
5. Delivery - Test Courier delivery channels
6. Verification - Test backup integrity check
7. Metrics - Verifica performance metrics
"""

import asyncio
import sys
import json
from datetime import datetime
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from core.agents.vault_keepers.chamberlain import ChamberlainAgent

async def test_vault_keepers_end_to_end():
    """
    🛡️ Test End-to-End del Sistema Vault Keepers
    =============================================
    """
    print("🏰" + "="*60)
    print("🏰 VITRUVYAN VAULT KEEPERS - END-TO-END TEST")  
    print("🏰" + "="*60)
    print()
    
    try:
        # === PHASE 1: INITIALIZATION ===
        print("📋 PHASE 1: INITIALIZATION")
        print("-" * 40)
        
        print("🏰 Initializing Chamberlain...")
        chamberlain = ChamberlainAgent()
        
        print(f"✅ Chamberlain ready: {chamberlain}")
        print(f"📊 Status: {json.dumps(chamberlain.get_status(), indent=2)}")
        print()
        
        # === PHASE 2: WORKFLOW EXECUTION ===
        print("🛡️ PHASE 2: FULL WORKFLOW EXECUTION")
        print("-" * 40)
        
        # Test context per il backup
        test_context = {
            "test_mode": True,
            "triggered_by": "end_to_end_test",
            "timestamp": datetime.now().isoformat(),
            "description": "Vault Keepers end-to-end validation"
        }
        
        print("🚀 Starting backup workflow (mode: incremental)...")
        workflow_result = await chamberlain.execute_backup_workflow(
            mode="incremental", 
            trigger="end_to_end_test",
            context=test_context
        )
        
        print()
        print("📊 WORKFLOW RESULTS:")
        print("=" * 50)
        print(json.dumps(workflow_result, indent=2))
        print()
        
        # === PHASE 3: DETAILED ANALYSIS ===
        print("🔍 PHASE 3: DETAILED ANALYSIS")
        print("-" * 40)
        
        success = workflow_result.get("success", False)
        phases = workflow_result.get("phases", {})
        
        print(f"🎯 Overall Success: {success}")
        print(f"⏱️  Total Duration: {workflow_result.get('duration', 0):.2f}s")
        print(f"🆔 Workflow ID: {workflow_result.get('workflow_id')}")
        print()
        
        # Analisi dettagliata di ogni fase
        phase_names = ["detection", "preparation", "execution", "delivery", "verification"]
        for phase_name in phase_names:
            phase_data = phases.get(phase_name, {})
            phase_success = phase_data.get("success", False)
            status_icon = "✅" if phase_success else "❌"
            
            print(f"{status_icon} {phase_name.upper()}: {phase_success}")
            if not phase_success and phase_data.get("error"):
                print(f"   Error: {phase_data['error']}")
            elif phase_success:
                # Mostra dettagli interessanti per fase
                if phase_name == "detection":
                    print(f"   Changes: {phase_data.get('changes_detected', 'N/A')}")
                    print(f"   Tables: {phase_data.get('monitored_tables', 0)}")
                    print(f"   Paths: {phase_data.get('monitored_paths', 0)}")
                elif phase_name == "execution":
                    print(f"   Backup ID: {phase_data.get('backup_id', 'N/A')}")
                    print(f"   Size: {phase_data.get('backup_size_mb', 0)}MB")
                    print(f"   Files: {phase_data.get('files_backed_up', 0)}")
                elif phase_name == "delivery":
                    print(f"   Channels: {len(phase_data.get('delivery_channels', []))}")
                    print(f"   Job ID: {phase_data.get('job_id', 'N/A')}")
            print()
        
        # === PHASE 4: METRICS VALIDATION ===
        print("📈 PHASE 4: METRICS VALIDATION")
        print("-" * 40)
        
        final_status = chamberlain.get_status()
        metrics = final_status.get("metrics", {})
        
        print(f"📊 Total Workflows: {metrics.get('total_workflows', 0)}")
        print(f"✅ Successful: {metrics.get('successful_workflows', 0)}")
        print(f"❌ Failed: {metrics.get('failed_workflows', 0)}")
        print(f"⏱️  Average Duration: {metrics.get('average_duration', 0):.2f}s")
        print()
        
        # === FINAL SUMMARY ===
        print("🏆 FINAL SUMMARY")
        print("=" * 50)
        
        if success:
            print("🎉 END-TO-END TEST: SUCCESS!")
            print("✅ All Vault Keepers functioning correctly")
            print("✅ Workflow coordination operational")  
            print("✅ Medieval backup system ready for deployment")
            print()
            print("🏰 'No treasure left unguarded!' - Mission accomplished! ⚔️")
            return True
        else:
            print("❌ END-TO-END TEST: FAILED!")
            print(f"❌ Error: {workflow_result.get('message', 'Unknown error')}")
            print("🔧 System requires debugging before deployment")
            return False
            
    except Exception as e:
        print(f"💥 CRITICAL ERROR during end-to-end test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🏰 Starting Vitruvyan Vault Keepers End-to-End Test...")
    print()
    
    # Run the async test
    success = asyncio.run(test_vault_keepers_end_to_end())
    
    # Exit with appropriate code
    exit_code = 0 if success else 1
    print(f"\n🏰 Test completed with exit code: {exit_code}")
    sys.exit(exit_code)