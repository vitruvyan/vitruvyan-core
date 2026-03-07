"""
Tests for causal_query.py — Pure domain logic (F3.2)
=====================================================

No I/O, no database. Tests the tree building and traversal functions.
"""

import pytest
from core.synaptic_conclave.events.causal_query import (
    CausalNode,
    build_causal_tree,
    get_roots,
    causal_chain,
    descendants,
)


def _row(event_id, trace_id, causation_id=None, event_type="test", source="test"):
    return {
        "event_id": event_id,
        "trace_id": trace_id,
        "causation_id": causation_id,
        "event_type": event_type,
        "source": source,
        "channel": "test.channel",
        "created_at": "2026-03-01T00:00:00",
    }


class TestBuildCausalTree:
    def test_single_root(self):
        rows = [_row("e1", "t1")]
        tree = build_causal_tree(rows)
        assert len(tree) == 1
        assert tree["e1"].causation_id is None
        assert tree["e1"].children == []

    def test_parent_child(self):
        rows = [
            _row("e1", "t1"),
            _row("e2", "t1", causation_id="e1"),
        ]
        tree = build_causal_tree(rows)
        assert len(tree["e1"].children) == 1
        assert tree["e1"].children[0].event_id == "e2"

    def test_three_levels(self):
        rows = [
            _row("root", "t1"),
            _row("mid", "t1", causation_id="root"),
            _row("leaf", "t1", causation_id="mid"),
        ]
        tree = build_causal_tree(rows)
        assert len(tree["root"].children) == 1
        assert tree["root"].children[0].event_id == "mid"
        assert len(tree["mid"].children) == 1
        assert tree["mid"].children[0].event_id == "leaf"
        assert tree["leaf"].children == []

    def test_branching(self):
        rows = [
            _row("root", "t1"),
            _row("a", "t1", causation_id="root"),
            _row("b", "t1", causation_id="root"),
        ]
        tree = build_causal_tree(rows)
        assert len(tree["root"].children) == 2
        child_ids = {c.event_id for c in tree["root"].children}
        assert child_ids == {"a", "b"}

    def test_empty_rows(self):
        tree = build_causal_tree([])
        assert tree == {}


class TestGetRoots:
    def test_single_root(self):
        rows = [_row("e1", "t1"), _row("e2", "t1", causation_id="e1")]
        tree = build_causal_tree(rows)
        roots = get_roots(tree)
        assert len(roots) == 1
        assert roots[0].event_id == "e1"

    def test_orphaned_parent(self):
        """If causation_id references a missing event, that node is also a root."""
        rows = [_row("e1", "t1", causation_id="missing")]
        tree = build_causal_tree(rows)
        roots = get_roots(tree)
        assert len(roots) == 1
        assert roots[0].event_id == "e1"


class TestCausalChain:
    def test_chain_root_to_leaf(self):
        rows = [
            _row("root", "t1"),
            _row("mid", "t1", causation_id="root"),
            _row("leaf", "t1", causation_id="mid"),
        ]
        tree = build_causal_tree(rows)
        chain = causal_chain(tree, "leaf")
        assert [n.event_id for n in chain] == ["root", "mid", "leaf"]

    def test_chain_root_is_self(self):
        rows = [_row("root", "t1")]
        tree = build_causal_tree(rows)
        chain = causal_chain(tree, "root")
        assert [n.event_id for n in chain] == ["root"]

    def test_chain_not_found(self):
        tree = build_causal_tree([_row("e1", "t1")])
        assert causal_chain(tree, "missing") == []


class TestDescendants:
    def test_descendants_bfs(self):
        rows = [
            _row("root", "t1"),
            _row("a", "t1", causation_id="root"),
            _row("b", "t1", causation_id="root"),
            _row("a1", "t1", causation_id="a"),
        ]
        tree = build_causal_tree(rows)
        desc = descendants(tree, "root")
        desc_ids = {d.event_id for d in desc}
        assert desc_ids == {"a", "b", "a1"}

    def test_descendants_leaf(self):
        rows = [_row("root", "t1"), _row("leaf", "t1", causation_id="root")]
        tree = build_causal_tree(rows)
        assert descendants(tree, "leaf") == []

    def test_descendants_not_found(self):
        tree = build_causal_tree([_row("e1", "t1")])
        assert descendants(tree, "missing") == []
