"""
Inspector Consumer — Usage Example
====================================

Demonstrates pure consistency inspection with no I/O.
The adapter (LIVELLO 2) would normally provide counts/IDs
from PostgreSQL and Qdrant; here we supply them inline.

Run::

    python -m vitruvyan_core.core.governance.codex_hunters.examples.inspector_example
"""

from core.governance.codex_hunters.consumers.inspector import InspectorConsumer


def main():
    inspector = InspectorConsumer()

    # Simulated data that an adapter would fetch from two data stores
    result = inspector.process({
        "collections": [
            {
                "collection_name": "documents",
                "source_a_count": 500,
                "source_b_count": 495,
                "source_a_ids": [f"doc_{i}" for i in range(500)],
                "source_b_ids": [f"doc_{i}" for i in range(495)],
            },
            {
                "collection_name": "embeddings",
                "source_a_count": 1000,
                "source_b_count": 600,
                "source_a_ids": [f"emb_{i}" for i in range(1000)],
                "source_b_ids": [f"emb_{i}" for i in range(600)],
            },
            {
                "collection_name": "metadata",
                "source_a_count": 200,
                "source_b_count": 200,
            },
        ]
    })

    print(f"Success: {result.success}")
    print(f"Warnings: {result.warnings}")
    print()

    report = result.data["report"]
    print(f"Overall score:  {report.overall_score:.2%}")
    print(f"Overall status: {report.overall_status.value}")
    print(f"Needs healing:  {report.needs_healing}")
    print()

    for cc in report.collections:
        print(
            f"  {cc.collection_name}: {cc.consistency_score:.2%} "
            f"({cc.status.value}) "
            f"orphans_a={len(cc.orphans_a)} orphans_b={len(cc.orphans_b)}"
        )

    print()
    for rec in report.recommendations:
        print(f"  → {rec}")

    print()
    print("Inspector stats:", inspector.get_inspection_stats())


if __name__ == "__main__":
    main()
