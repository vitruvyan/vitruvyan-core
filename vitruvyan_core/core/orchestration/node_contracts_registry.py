"""
Vitruvyan Core — Node Contracts Registry
=========================================
Defines the declared contracts for every LangGraph node in the base graph.

Each entry maps a node name (registry key) to a NodeContractSpec that
declares which state keys the node REQUIRES on entry and PRODUCES on exit.

These specs are consumed by ``graph_flow._wrap()`` via the @enforced
decorator to provide observability-first contract enforcement (Phase 3).

Extending with domain contracts::

    from core.orchestration.node_contracts_registry import (
        merge_domain_contracts,
        NODE_CONTRACTS,
    )
    merge_domain_contracts({
        "my_domain_node": NodeContractSpec(
            requires={"input_text"},
            produces={"domain_result"},
        )
    })

Author: Vitruvyan Core Team
Created: March 2026
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Set


# ---------------------------------------------------------------------------
# Spec dataclass
# ---------------------------------------------------------------------------

@dataclass
class NodeContractSpec:
    """
    Declares the state contract for a single LangGraph node.

    Attributes:
        requires: Keys that MUST be present in `state` when the node is called.
        produces: Keys the node MUST set in the returned state dict.
    """
    requires: Set[str] = field(default_factory=set)
    produces: Set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Base registry — OS-agnostic, domain-neutral
# ---------------------------------------------------------------------------

NODE_CONTRACTS: Dict[str, NodeContractSpec] = {
    "parse": NodeContractSpec(
        requires={"input_text"},
        produces={"input_text", "human_input"},
    ),
    "intent_detection": NodeContractSpec(
        requires={"input_text"},
        produces={"intent", "route"},
    ),
    "entity_resolver": NodeContractSpec(
        requires={"intent"},
        produces={"entity_ids"},
    ),
    "params_extraction": NodeContractSpec(
        requires={"intent", "input_text"},
        produces={"domain_params"},
    ),
    "decide": NodeContractSpec(
        requires={"intent"},
        produces={"route"},
    ),
    "weaver": NodeContractSpec(
        requires={"input_text"},
        produces={},
    ),
    "babel_emotion": NodeContractSpec(
        requires={"input_text"},
        produces={},
    ),
    "semantic_grounding": NodeContractSpec(
        requires={"input_text"},
        produces={},
    ),
    "exec": NodeContractSpec(
        requires={"intent", "entity_ids"},
        produces={"response"},
    ),
    "qdrant": NodeContractSpec(
        requires={"input_text"},
        produces={"response"},
    ),
    "cached_llm": NodeContractSpec(
        requires={"input_text"},
        produces={"response"},
    ),
    "output_normalizer": NodeContractSpec(
        requires={"response"},
        produces={"response"},
    ),
    "compose": NodeContractSpec(
        requires={"response"},
        produces={"narrative"},
    ),
    "orthodoxy": NodeContractSpec(
        requires={},
        produces={"orthodoxy_status", "orthodoxy_verdict"},
    ),
    "vault": NodeContractSpec(
        requires={},
        produces={"vault_blessing"},
    ),
    "advisor": NodeContractSpec(
        requires={"response"},
        produces={},
    ),
    "can": NodeContractSpec(
        requires={},
        produces={},
    ),
    "codex_hunters": NodeContractSpec(
        requires={},
        produces={"codex_success"},
    ),
    "llm_mcp": NodeContractSpec(
        requires={"input_text"},
        produces={"response"},
    ),
    "early_exit": NodeContractSpec(
        requires={"intent"},
        produces={"response"},
    ),
}


# ---------------------------------------------------------------------------
# Domain extension helper
# ---------------------------------------------------------------------------

def merge_domain_contracts(domain_specs: Dict[str, NodeContractSpec]) -> None:
    """
    Merge domain-specific node contracts into the global registry.

    Domain plugins call this at boot to extend or override base contracts.
    Existing entries are updated (set union on requires/produces) rather
    than replaced, so the base invariants are preserved.

    Args:
        domain_specs: Mapping of node name → NodeContractSpec from the domain.
    """
    for node_name, spec in domain_specs.items():
        if node_name in NODE_CONTRACTS:
            NODE_CONTRACTS[node_name].requires.update(spec.requires)
            NODE_CONTRACTS[node_name].produces.update(spec.produces)
        else:
            NODE_CONTRACTS[node_name] = spec
