"""
Vitruvyan Core — Node Contracts Registry
==========================================

Declarative requires/produces contracts for ALL LangGraph nodes.

AUDIT SOURCE: Each entry was verified against the actual return statements
and state.get() calls in the node source files (Feb 28, 2026 audit).

This registry is consumed by build_graph() in graph_flow.py via the
_wrap() helper, which applies the @enforced decorator from
contract_enforcement.py.

Design decisions:
  - Only CRITICAL requires are listed (fields that cause failure or garbage
    if missing). Optional reads with safe defaults (.get("x", fallback))
    are NOT listed as requires — they don't violate a contract.
  - Only GUARANTEED produces are listed (fields written in ALL code paths,
    including fallback). Conditional produces are NOT listed — a contract
    violation should mean "something always expected is missing", not
    "an optional branch wasn't taken".
  - Domain-dependent nodes (entity_resolver, exec) have empty produces
    because output varies by domain plugin.

LIVELLO 1 compliance:
  - Pure Python, zero I/O, zero external dependencies.
  - No prometheus_client, no Redis, no Postgres.

Author: Vitruvyan Core Team
Created: February 28, 2026
Status: LIVELLO 1 — FOUNDATIONAL
"""

from core.orchestration.contract_enforcement import NodeContractSpec

# =============================================================================
# NODE_CONTRACTS — Source of truth for pipeline enforcement
# =============================================================================
#
# KEY = node name as registered in build_graph() (g.add_node("name", ...))
# VALUE = NodeContractSpec(requires=[...], produces=[...])
#
# Convention:
#   requires = fields the node MUST have in state (None/missing = violation)
#   produces = fields the node MUST include in its return dict (all paths)
#
# Audit date: Feb 28, 2026. Each entry verified against source.
# =============================================================================

NODE_CONTRACTS: dict[str, NodeContractSpec] = {

    # ── PHASE 1: Input Processing ────────────────────────────────────────────

    "parse": NodeContractSpec(
        # parse_node.py: reads input_text via .get("", default)
        # All reads have safe defaults — no critical requires
        requires=[],
        produces=[
            "input_text",       # always set = user_input
            "domain_params",    # always set (merged dict)
            "route",            # always set = "dispatcher_exec" default
        ],
    ),

    "intent_detection": NodeContractSpec(
        # intent_detection_node.py: reads user_message/input_text with .get
        requires=[],
        produces=[
            "intent",                   # always set (str)
            "language_detected",        # always set (str)
            "language",                 # always set (= language_detected)
            "language_confidence",      # always set (float)
            "babel_status",             # always set (str)
            "route",                    # always set = "intent_detection"
        ],
    ),

    "early_exit": NodeContractSpec(
        # early_exit_node.py: reads intent with .get(default="greeting")
        requires=[],
        produces=[
            "route",                # always "early_exit"
            "narrative",            # always set (str)
            "orthodoxy_status",     # always "blessed"
            "orthodoxy_verdict",    # always "blessed"
            "orthodoxy_confidence", # always 0.99
            "orthodoxy_findings",   # always 0
            "orthodoxy_timestamp",  # always set (ISO)
            "vault_blessing",       # always True
            "conversation_type",    # always set (= intent)
            "response",             # always set (dict)
        ],
    ),

    # ── PHASE 2: Enrichment ──────────────────────────────────────────────────

    "weaver": NodeContractSpec(
        # pattern_weavers_node.py (v2) or pw_compile_node.py (v3)
        # Both have identical guaranteed produces via fallback paths
        requires=[],
        produces=[
            "weaver_context",       # always set (dict)
            "weave_result",         # always set (dict)
            "matched_concepts",     # always set (list)
            "semantic_context",     # always set (list)
            "weave_confidence",     # always set (float)
            "pattern_metadata",     # always set (dict)
        ],
    ),

    "entity_resolver": NodeContractSpec(
        # entity_resolver_node.py: delegates to domain-specific registry
        # Output is entirely domain-dependent — no guaranteed produces
        requires=[],
        produces=[],
    ),

    "babel_emotion": NodeContractSpec(
        # emotion_detector.py: reads input_text with .get(default="")
        requires=[],
        produces=[
            "emotion_detected",     # always set (str, "neutral" on failure)
            "emotion_confidence",   # always set (float, 0.3-0.5 on failure)
        ],
    ),

    "semantic_grounding": NodeContractSpec(
        # semantic_grounding_node.py: all reads have safe defaults
        requires=[],
        produces=[
            "semantic_matches",     # always set (list)
            "vsgs_status",          # always set (str)
        ],
    ),

    "params_extraction": NodeContractSpec(
        # params_extraction_node.py: all reads have safe defaults
        requires=[],
        produces=[
            "horizon",              # always set (str)
            "top_k",                # always set (int)
            "route",                # always "params_extraction"
        ],
    ),

    # ── PHASE 3: Routing ─────────────────────────────────────────────────────

    "decide": NodeContractSpec(
        # route_node.py: reads intent with .get(default="unknown")
        requires=[],
        produces=[
            "route",                # always set (str)
        ],
    ),

    # ── PHASE 4: Execution Branches ──────────────────────────────────────────

    "exec": NodeContractSpec(
        # exec_node.py: delegates to ExecutionRegistry
        # Output domain-dependent, but raw_output and route always set via stub
        requires=[],
        produces=[
            "raw_output",           # always set (dict via stub fallback)
            "route",                # always set ("exec_valid")
        ],
    ),

    "qdrant": NodeContractSpec(
        # qdrant_node.py: reads input_text with .get(default="")
        requires=[],
        produces=[],
        # NOTE: produces either "result" (success) or "error" (failure)
        # — neither is guaranteed in ALL paths, so we can't enforce either
    ),

    "cached_llm": NodeContractSpec(
        # cached_llm_node.py: referred to as "llm_soft" in graph_flow.py
        requires=[],
        produces=[
            "llm_response",         # always set (str)
            "cache_info",           # always set (dict)
        ],
    ),

    "llm_mcp": NodeContractSpec(
        # llm_mcp_node.py: when USE_MCP=0 returns state unchanged
        # Cannot guarantee any produces since MCP may be off
        requires=[],
        produces=[],
    ),

    # ── PHASE 5: Post-Processing ─────────────────────────────────────────────

    "output_normalizer": NodeContractSpec(
        # output_normalizer_node.py: normalizes result dict in-place
        requires=[],
        produces=[
            "result",               # always set (dict)
        ],
    ),

    # ── PHASE 6: Sacred Orders ───────────────────────────────────────────────

    "orthodoxy": NodeContractSpec(
        # orthodoxy_node.py: reads response/input_text/route etc with .get
        # NOTE: the roadmap doc claimed requires=["narrative"] — WRONG.
        # orthodoxy never reads "narrative". It reads "response".
        requires=[],
        produces=[
            "orthodoxy_status",     # always set (str)
            "orthodoxy_verdict",    # always set (str)
            "orthodoxy_confidence", # always set (float)
            "orthodoxy_findings",   # always set (int)
            "orthodoxy_timestamp",  # always set (ISO str)
            "orthodoxy_blessing",   # always set (str)
            "orthodoxy_message",    # always set (str)
        ],
    ),

    "vault": NodeContractSpec(
        # vault_node.py: reads human_input/input with .get
        requires=[],
        produces=[
            "vault_blessing",       # always set (dict)
            "route",                # always "compose"
        ],
    ),

    "compose": NodeContractSpec(
        # compose_node.py: reads intent/route/input_text etc with .get
        requires=[],
        produces=[
            "narrative",            # always set (str)
            "action",               # always set (str: "conversation"|"synthesis")
        ],
    ),

    "can": NodeContractSpec(
        # can_node.py: when CAN_ENABLED=0 returns state unchanged
        # When enabled: always produces narrative, follow_ups, route
        # NOTE: the roadmap doc claimed requires=["narrative"] — WRONG.
        # can never reads "narrative". It WRITES narrative.
        requires=[],
        produces=[
            # Cannot guarantee these when CAN_ENABLED=0
            # Listed for documentation — enforcement will warn when CAN off
        ],
    ),

    "advisor": NodeContractSpec(
        # advisor_node.py: returns state unchanged unless user_requests_action
        requires=[],
        produces=[],
        # advisor_recommendation only produced conditionally
    ),

    # ── PHASE 7: Maintenance ─────────────────────────────────────────────────

    "codex_hunters": NodeContractSpec(
        # codex_hunters_node.py: always produces these (success/skip/error paths)
        requires=[],
        produces=[
            "status",               # always set ("success"|"skipped"|"error")
            "codex_success",        # always set (bool)
            "response",             # always set (dict with narrative, type)
            "route",                # always set ("codex_complete"|"error_handling")
        ],
    ),
}


# =============================================================================
# Helper for domain plugin integration
# =============================================================================

def merge_domain_contracts(domain_contracts: dict[str, NodeContractSpec]) -> None:
    """
    Merge domain-specific node contracts into the registry.

    Called by graph_flow.py after loading domain graph_nodes extension.
    Domain plugins export contracts via get_<domain>_node_contracts().

    Args:
        domain_contracts: Dict of {node_name: NodeContractSpec}
    """
    for name, spec in domain_contracts.items():
        if name in NODE_CONTRACTS:
            # Domain cannot override core node contracts
            import logging
            logging.getLogger(__name__).warning(
                f"[NODE_REGISTRY] Domain contract for '{name}' ignored — "
                f"core node contracts cannot be overridden."
            )
            continue
        NODE_CONTRACTS[name] = spec
