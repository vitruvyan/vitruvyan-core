#!/usr/bin/env python3
"""
RAG Collection Audit — Qdrant vs Contract Registry
====================================================

Compares live Qdrant collections against the canonical registry
defined in contracts.rag (RAG Governance Contract V1, Section 9).

Reports:
  - ORPHAN:   Live in Qdrant but NOT declared in contract registry
  - MISSING:  Declared in registry but NOT present in Qdrant
  - MISMATCH: Declared AND live but vector_size or distance differ
  - OK:       Declared AND live, metadata matches

Exit codes:
  0  All declared collections present and healthy
  1  At least one MISSING or MISMATCH (action required)
  2  Connection error

Usage:
    python scripts/audit_rag_collections.py
    python scripts/audit_rag_collections.py --json
    python scripts/audit_rag_collections.py --strict   # also fail on orphans

Environment Variables:
    QDRANT_HOST, QDRANT_PORT, QDRANT_URL
"""

import argparse
import json
import sys
from pathlib import Path

# Add vitruvyan_core to path
sys.path.insert(0, str(Path(__file__).parent.parent / "vitruvyan_core"))

from core.agents.qdrant_agent import QdrantAgent
from contracts.rag import ALL_DECLARED_COLLECTIONS, CollectionDeclaration


def _get_live_collections(agent: QdrantAgent) -> dict:
    """Fetch all live collections with metadata from Qdrant."""
    live = {}
    health = agent.health()
    if health["status"] != "ok":
        return live

    for name in health["collections"]:
        try:
            info = agent.client.get_collection(name)
            vec_cfg = info.config.params.vectors
            # vec_cfg can be a VectorParams or a dict of named vectors
            if hasattr(vec_cfg, "size"):
                size = vec_cfg.size
                distance = vec_cfg.distance.name if hasattr(vec_cfg.distance, "name") else str(vec_cfg.distance)
            else:
                # named vectors — take the first
                first = next(iter(vec_cfg.values())) if isinstance(vec_cfg, dict) else vec_cfg
                size = getattr(first, "size", 0)
                distance = str(getattr(first, "distance", "?"))

            live[name] = {
                "points": info.points_count,
                "vector_size": size,
                "distance": distance.upper(),
            }
        except Exception as e:
            live[name] = {"points": 0, "vector_size": 0, "distance": "?", "error": str(e)}

    return live


def _normalize_distance(d: str) -> str:
    """Normalize distance name for comparison."""
    return d.upper().replace("COSINE", "COSINE").replace("DOT", "DOT").replace("EUCLID", "EUCLID")


def audit(agent: QdrantAgent) -> dict:
    """Run full audit, return structured report."""
    live = _get_live_collections(agent)
    declared = {d.name: d for d in ALL_DECLARED_COLLECTIONS}

    report = {"ok": [], "missing": [], "mismatch": [], "orphan": []}

    # Check declared vs live
    for name, decl in declared.items():
        if name not in live:
            report["missing"].append({
                "name": name,
                "tier": decl.tier.value,
                "owner": decl.owner,
            })
            continue

        info = live[name]
        problems = []
        if info["vector_size"] != decl.vector_size:
            problems.append(f"vector_size: live={info['vector_size']} contract={decl.vector_size}")
        if _normalize_distance(info["distance"]) != _normalize_distance(decl.distance.value):
            problems.append(f"distance: live={info['distance']} contract={decl.distance.value}")

        if problems:
            report["mismatch"].append({
                "name": name,
                "tier": decl.tier.value,
                "points": info["points"],
                "problems": problems,
            })
        else:
            report["ok"].append({
                "name": name,
                "tier": decl.tier.value,
                "points": info["points"],
            })

    # Orphans (live but not declared)
    for name, info in live.items():
        if name not in declared:
            report["orphan"].append({
                "name": name,
                "points": info["points"],
                "vector_size": info["vector_size"],
            })

    return report


def print_report(report: dict, as_json: bool = False) -> None:
    """Print human-readable or JSON report."""
    if as_json:
        print(json.dumps(report, indent=2))
        return

    total = sum(len(v) for v in report.values())
    print(f"\n{'=' * 60}")
    print(f"  RAG Collection Audit Report")
    print(f"  Contract: RAG_GOVERNANCE_CONTRACT_V1")
    print(f"  Collections scanned: {total}")
    print(f"{'=' * 60}\n")

    if report["ok"]:
        print(f"  ✅ OK ({len(report['ok'])})")
        for item in report["ok"]:
            print(f"     {item['name']:30s}  {item['tier']:6s}  {item['points']:>8,} pts")
        print()

    if report["missing"]:
        print(f"  ❌ MISSING ({len(report['missing'])})")
        for item in report["missing"]:
            print(f"     {item['name']:30s}  {item['tier']:6s}  owner={item['owner']}")
        print()

    if report["mismatch"]:
        print(f"  ⚠️  MISMATCH ({len(report['mismatch'])})")
        for item in report["mismatch"]:
            print(f"     {item['name']:30s}  {item['tier']:6s}  {item['points']:>8,} pts")
            for p in item["problems"]:
                print(f"       → {p}")
        print()

    if report["orphan"]:
        print(f"  👻 ORPHAN ({len(report['orphan'])})")
        for item in sorted(report["orphan"], key=lambda x: -x["points"]):
            print(f"     {item['name']:30s}  {item['points']:>10,} pts  dim={item['vector_size']}")
        print()

    # Summary line
    issues = len(report["missing"]) + len(report["mismatch"])
    if issues == 0 and not report["orphan"]:
        print("  🎯 All declared collections present and healthy.\n")
    elif issues == 0:
        print(f"  🎯 Declared collections healthy. {len(report['orphan'])} orphan(s) detected.\n")
    else:
        print(f"  🚨 {issues} issue(s) require action. Run init_qdrant_collections.py to fix MISSING.\n")


def main():
    parser = argparse.ArgumentParser(description="Audit Qdrant collections against RAG contract")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if orphans exist")
    args = parser.parse_args()

    try:
        agent = QdrantAgent()
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}", file=sys.stderr)
        sys.exit(2)

    report = audit(agent)
    print_report(report, as_json=args.json)

    issues = len(report["missing"]) + len(report["mismatch"])
    if args.strict:
        issues += len(report["orphan"])

    sys.exit(1 if issues > 0 else 0)


if __name__ == "__main__":
    main()
