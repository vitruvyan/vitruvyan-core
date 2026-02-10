#!/usr/bin/env python3
"""
Vault Keepers — Example: Integrity Check and Backup Operations

Demonstrates the complete domain flow for vault operations:
  Integrity Check → Backup Creation → Snapshot Validation

Run standalone: python -m examples.example_vault_operations
Requires: NO infrastructure (no Redis, no PostgreSQL, no Docker)

Sacred Order: Truth (Memory & Archival)
Layer: Foundational (examples)
"""

import sys
import os

# Add vitruvyan_core to path for standalone execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

from core.governance.vault_keepers.domain.vault_objects import IntegrityReport, VaultSnapshot
from core.governance.vault_keepers.consumers.sentinel import Sentinel
from core.governance.vault_keepers.consumers.archivist import Archivist


def main():
    print("=" * 60)
    print("Vault Keepers — Integrity Check & Backup Operations")
    print("=" * 60)

    # ─────────────────────────────────────────────────────────────
    # 1. Integrity Check: Sentinel validates data integrity
    # ─────────────────────────────────────────────────────────────
    print("\n1. Running integrity check with Sentinel:")

    sentinel = Sentinel()
    integrity_input = {
        "operation": "integrity_check",
        "target": "postgresql",
        "scope": "full",
        "sample_size": 1000,
        "corruption_threshold": 0.01
    }

    integrity_report = sentinel.process(integrity_input)
    print(f"   Integrity Report: {integrity_report.status}")
    print(f"   Records checked: {integrity_report.records_checked}")
    print(f"   Corruption detected: {integrity_report.corruption_detected}")
    print(f"   Corruption rate: {integrity_report.corruption_rate:.4f}")

    # ─────────────────────────────────────────────────────────────
    # 2. Backup Creation: Archivist creates snapshot metadata
    # ─────────────────────────────────────────────────────────────
    print("\n2. Creating backup snapshot with Archivist:")

    archivist = Archivist()
    backup_input = {
        "operation": "create_backup",
        "type": "full",
        "systems": ["postgresql", "qdrant"],
        "timestamp": "2026-02-10T10:00:00Z",
        "metadata": [
            ("initiator", "scheduled_backup"),
            ("retention_days", "30")
        ]
    }

    snapshot = archivist.process(backup_input)
    print(f"   Snapshot created: {snapshot.snapshot_id}")
    print(f"   Scope: {snapshot.scope}")
    print(f"   Status: {snapshot.status}")
    print(f"   Size: {snapshot.size_bytes} bytes")
    print(f"   PostgreSQL path: {snapshot.postgresql_backup_path}")
    print(f"   Qdrant path: {snapshot.qdrant_backup_path}")

    # ─────────────────────────────────────────────────────────────
    # 3. Validation: Cross-check integrity and backup
    # ─────────────────────────────────────────────────────────────
    print("\n3. Validating backup integrity:")

    # Simulate post-backup integrity check
    post_backup_input = integrity_input.copy()
    post_backup_input["timestamp"] = "2026-02-10T10:05:00Z"

    post_backup_report = sentinel.process(post_backup_input)
    print(f"   Post-backup integrity: {post_backup_report.status}")
    print(f"   Corruption rate: {post_backup_report.corruption_rate:.4f}")

    # Check if backup was successful
    backup_successful = (
        snapshot.status == "completed" and
        post_backup_report.status == "blessed" and
        not post_backup_report.corruption_detected
    )

    print(f"   Backup validation: {'✅ SUCCESSFUL' if backup_successful else '❌ FAILED'}")

    # ─────────────────────────────────────────────────────────────
    # 4. Audit Trail: Log all operations
    # ─────────────────────────────────────────────────────────────
    print("\n4. Audit trail of operations:")

    operations = [
        ("integrity_check_pre", integrity_report),
        ("backup_creation", snapshot),
        ("integrity_check_post", post_backup_report)
    ]

    for op_name, op_result in operations:
        print(f"   {op_name}: {type(op_result).__name__} - {getattr(op_result, 'status', 'completed')}")

    print("\n✅ Vault operations example completed!")
    print("\n💡 This demonstrates pure domain logic - no I/O, no databases, no network calls")
    print("   The service layer (api_vault_keepers) handles persistence and event publishing")


if __name__ == "__main__":
    main()