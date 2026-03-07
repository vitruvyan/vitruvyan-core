"""
Causal Query — Pure Domain Logic (F3.2)
========================================

Pure functions for building and querying causal event trees.
NO I/O. Works on in-memory data structures returned by persistence layer.

Usage:
    rows = persistence.fetch_trace("trace-abc-123")
    tree = build_causal_tree(rows)
    chain = causal_chain(tree, "event-xyz-789")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CausalNode:
    """A single node in a causal tree."""
    event_id: str
    trace_id: str
    causation_id: Optional[str]
    event_type: str
    source: str
    channel: Optional[str]
    created_at: str  # ISO timestamp as string (no datetime dep needed)
    children: List[CausalNode] = field(default_factory=list, hash=False, compare=False)


def build_causal_tree(rows: List[Dict]) -> Dict[str, CausalNode]:
    """
    Build a causal tree from flat database rows.

    Args:
        rows: List of dicts with keys: event_id, trace_id, causation_id,
              event_type, source, channel, created_at

    Returns:
        Dict mapping event_id → CausalNode (with children populated).
        Root nodes have causation_id=None.
    """
    nodes: Dict[str, CausalNode] = {}
    for row in rows:
        node = CausalNode(
            event_id=row["event_id"],
            trace_id=row["trace_id"],
            causation_id=row.get("causation_id"),
            event_type=row["event_type"],
            source=row["source"],
            channel=row.get("channel"),
            created_at=str(row.get("created_at", "")),
        )
        nodes[node.event_id] = node

    # Wire parent→child relationships
    for node in nodes.values():
        if node.causation_id and node.causation_id in nodes:
            nodes[node.causation_id].children.append(node)

    return nodes


def get_roots(tree: Dict[str, CausalNode]) -> List[CausalNode]:
    """Return root nodes (events with no causation_id or orphaned parents)."""
    return [n for n in tree.values() if n.causation_id is None or n.causation_id not in tree]


def causal_chain(tree: Dict[str, CausalNode], event_id: str) -> List[CausalNode]:
    """
    Walk UP from event_id to root, returning the ancestor chain.

    Returns:
        List from root → ... → event_id (chronological order).
        Empty list if event_id not found.
    """
    if event_id not in tree:
        return []

    chain = []
    current = tree[event_id]
    visited = set()
    while current:
        if current.event_id in visited:
            break  # cycle guard
        visited.add(current.event_id)
        chain.append(current)
        if current.causation_id and current.causation_id in tree:
            current = tree[current.causation_id]
        else:
            break

    chain.reverse()
    return chain


def descendants(tree: Dict[str, CausalNode], event_id: str) -> List[CausalNode]:
    """Return all descendants of event_id (BFS order)."""
    if event_id not in tree:
        return []

    result = []
    queue = list(tree[event_id].children)
    visited = {event_id}
    while queue:
        node = queue.pop(0)
        if node.event_id in visited:
            continue
        visited.add(node.event_id)
        result.append(node)
        queue.extend(node.children)

    return result
