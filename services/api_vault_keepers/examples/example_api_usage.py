#!/usr/bin/env python3
"""
API Vault Keepers — Usage Examples

This script demonstrates how to interact with the API Vault Keepers service
for data integrity monitoring, backup, and recovery operations.

Prerequisites:
- API Vault Keepers service running on localhost:8001
- Or adjust BASE_URL accordingly

Run with: python examples/example_api_usage.py
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8001"

def check_integrity(target: str = "postgresql", scope: str = "sample") -> Dict[str, Any]:
    """Check data integrity for specified target."""
    payload = {
        "target": target,
        "scope": scope
    }

    try:
        response = requests.post(f"{BASE_URL}/integrity/check", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking integrity: {e}")
        return {}

def get_integrity_status() -> Dict[str, Any]:
    """Get current integrity status across all systems."""
    try:
        response = requests.get(f"{BASE_URL}/integrity/status")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting status: {e}")
        return {}

def create_backup(backup_type: str = "incremental", systems: list = None) -> Dict[str, Any]:
    """Create a new backup."""
    if systems is None:
        systems = ["postgresql"]

    payload = {
        "type": backup_type,
        "systems": systems
    }

    try:
        response = requests.post(f"{BASE_URL}/backup/create", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating backup: {e}")
        return {}

def list_backups() -> Dict[str, Any]:
    """List available backups."""
    try:
        response = requests.get(f"{BASE_URL}/backup/list")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error listing backups: {e}")
        return {}

def get_audit_events(limit: int = 10) -> Dict[str, Any]:
    """Get recent audit events."""
    try:
        response = requests.get(f"{BASE_URL}/audit/events?limit={limit}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting audit events: {e}")
        return {}

def main():
    """Run example API calls."""
    print("🛡️ API Vault Keepers — Data Integrity & Backup Examples")
    print("=" * 60)

    # Example 1: Integrity check
    print("\n1. Checking PostgreSQL integrity:")
    result = check_integrity("postgresql", "sample")
    if result:
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Corruption detected: {result.get('corruption_detected', 'unknown')}")
        details = result.get('details', {})
        print(f"   Records checked: {details.get('records_checked', 0)}")

    # Example 2: Overall integrity status
    print("\n2. Getting overall integrity status:")
    status = get_integrity_status()
    if status:
        print(f"   Overall status: {status.get('overall_status', 'unknown')}")
        systems = status.get('systems', {})
        for sys, sys_status in systems.items():
            print(f"   {sys}: {sys_status}")

    # Example 3: Create backup
    print("\n3. Creating incremental backup:")
    backup = create_backup("incremental", ["postgresql"])
    if backup:
        print(f"   Backup ID: {backup.get('backup_id', 'unknown')}")
        print(f"   Status: {backup.get('status', 'unknown')}")
        print(f"   Started at: {backup.get('started_at', 'unknown')}")

    # Example 4: List backups
    print("\n4. Listing available backups:")
    backups = list_backups()
    if backups:
        backup_list = backups.get('backups', [])
        print(f"   Found {len(backup_list)} backups")
        for i, bkp in enumerate(backup_list[:3]):  # Show first 3
            print(f"   Backup {i+1}: {bkp.get('backup_id', 'unknown')} "
                  f"({bkp.get('type', 'unknown')}) - {bkp.get('status', 'unknown')}")

    # Example 5: Audit trail
    print("\n5. Recent audit events:")
    audit = get_audit_events(5)
    if audit:
        events = audit.get('events', [])
        print(f"   Found {len(events)} recent events")
        for i, event in enumerate(events):
            print(f"   Event {i+1}: {event.get('operation', 'unknown')} "
                  f"on {event.get('target', 'unknown')} - {event.get('timestamp', 'unknown')}")

    print("\n✅ Examples completed!")
    print("\n💡 Tip: Start the service with:")
    print("   cd services/api_vault_keepers && python main.py")
    print("   Or: docker compose up -d api_vault_keepers")

if __name__ == "__main__":
    main()