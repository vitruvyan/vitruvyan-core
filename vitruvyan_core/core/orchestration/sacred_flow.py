"""
Vitruvyan Core — Sacred Flow Pipeline
======================================

The Sacred Flow is the domain-agnostic post-routing pipeline that
EVERY domain must pass through:

    output_normalizer → orthodoxy → vault → compose → can → [advisor] → proactive → END

This pipeline ensures:
1. Output is normalized (output_normalizer)
2. Truth & validation (orthodoxy - Sacred Order)
3. Memory & persistence (vault - Sacred Order)
4. Narrative assembly (compose)
5. Conversational enhancement (can)
6. Proactive suggestions (proactive_suggestions)

The advisor node is CONDITIONAL: only activates when user_requests_action=True
or can_mode='urgent'.

This module provides:
- SACRED_FLOW_NODES: Required node names
- SACRED_FLOW_EDGES: Required edges
- build_sacred_flow(): Helper to add Sacred Flow to a graph
- SacredFlowConfig: Configuration for the flow

Author: Vitruvyan Core Team
Created: February 10, 2026
Status: LEVEL 1 — FOUNDATIONAL
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Callable, Dict, Any, Optional


# =============================================================================
# SACRED FLOW CONFIGURATION
# =============================================================================

@dataclass
class SacredFlowConfig:
    """
    Configuration for the Sacred Flow pipeline.
    
    Allows customization of behavior without changing the core flow.
    """
    # Node enablement
    enable_orthodoxy: bool = True
    enable_vault: bool = True
    enable_advisor: bool = True
    enable_proactive: bool = True
    
    # Advisor activation conditions
    advisor_on_urgent: bool = True          # Activate if can_mode='urgent'
    advisor_on_action_request: bool = True  # Activate if user_requests_action=True
    
    # Keywords for domain-aware processing (injected by plugin)
    sensitive_keywords: List[str] = field(default_factory=list)
    action_keywords: List[str] = field(default_factory=list)
    
    # Timeouts (ms)
    orthodoxy_timeout_ms: int = 5000
    vault_timeout_ms: int = 5000


# =============================================================================
# SACRED FLOW NODE NAMES
# =============================================================================

# These are the canonical node names for the Sacred Flow
# graph_flow.py must use these exact names

SACRED_FLOW_NODES = [
    "output_normalizer",    # Normalize raw outputs to standard format
    "orthodoxy",            # Truth & validation (Sacred Order)
    "vault",                # Memory & persistence (Sacred Order)
    "compose",              # Narrative assembly (with slot-filling)
    "can",                  # Conversational Advisor Node
    "advisor",              # Decision-making (conditional)
    "proactive_suggestions" # Proactive suggestions
]


# =============================================================================
# SACRED FLOW EDGES
# =============================================================================

# Standard edges (always present)
SACRED_FLOW_EDGES: List[Tuple[str, str]] = [
    ("output_normalizer", "orthodoxy"),
    ("orthodoxy", "vault"),
    ("vault", "compose"),
    ("compose", "can"),
    # can → advisor OR proactive_suggestions (conditional, see below)
    ("advisor", "proactive_suggestions"),
    # proactive_suggestions → END (handled by graph)
]


# =============================================================================
# CONDITIONAL ROUTING LOGIC
# =============================================================================

def should_activate_advisor(state: Dict[str, Any], config: SacredFlowConfig) -> bool:
    """
    Determine if the advisor node should be activated.
    
    Args:
        state: Current graph state
        config: Sacred Flow configuration
        
    Returns:
        True if advisor should be activated
    """
    if not config.enable_advisor:
        return False
    
    # Urgent mode triggers advisor
    if config.advisor_on_urgent and state.get("can_mode") == "urgent":
        return True
    
    # Explicit action request triggers advisor
    if config.advisor_on_action_request and state.get("user_requests_action", False):
        return True
    
    return False


def create_can_to_advisor_router(config: SacredFlowConfig) -> Callable[[Dict[str, Any]], str]:
    """
    Create the routing function for CAN → Advisor/Proactive conditional edge.
    
    Args:
        config: Sacred Flow configuration
        
    Returns:
        A function that returns "advisor" or "proactive_suggestions"
    """
    def route_from_can(state: Dict[str, Any]) -> str:
        if should_activate_advisor(state, config):
            return "advisor"
        return "proactive_suggestions"
    
    return route_from_can


# =============================================================================
# UX FIELD PRESERVATION
# =============================================================================

# Fields that must be preserved through the Sacred Flow pipeline
# These are snapshotted before the flow and restored after

UX_PRESERVATION_FIELDS = [
    # Emotion fields (from Babel Gardens)
    "emotion_detected",
    "emotion_confidence", 
    "emotion_intensity",
    "emotion_secondary",
    "emotion_reasoning",
    "emotion_sentiment_label",
    "emotion_sentiment_score",
    "emotion_metadata",
    # Language fields
    "cultural_context",
    "language_detected",
    "language_confidence",
]


def snapshot_ux_fields(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Take a snapshot of UX fields before Sacred Flow execution.
    
    Args:
        state: Current graph state
        
    Returns:
        Dict of field_name → value (only non-None values)
    """
    return {
        field: state.get(field)
        for field in UX_PRESERVATION_FIELDS
        if state.get(field) is not None
    }


def restore_ux_fields(final_state: Dict[str, Any], snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Restore UX fields that were lost during Sacred Flow execution.
    
    Args:
        final_state: State after Sacred Flow execution
        snapshot: Snapshot taken before execution
        
    Returns:
        Updated state with restored fields
    """
    for field, value in snapshot.items():
        if value is not None and (field not in final_state or final_state.get(field) is None):
            final_state[field] = value
    
    return final_state


# =============================================================================
# INVOKE WRAPPER
# =============================================================================

def create_invoke_with_preservation(
    original_invoke: Callable[[Dict[str, Any]], Dict[str, Any]]
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create a wrapped invoke function that preserves UX fields.
    
    This is used to wrap the compiled graph's invoke method.
    
    Args:
        original_invoke: The original graph.invoke method
        
    Returns:
        Wrapped invoke that preserves UX fields
    """
    def invoke_with_propagation(state: Dict[str, Any]) -> Dict[str, Any]:
        # Snapshot UX fields BEFORE execution
        ux_snapshot = snapshot_ux_fields(state)
        
        # Execute the graph
        final_state = original_invoke(state)
        
        # Restore any lost fields
        final_state = restore_ux_fields(final_state, ux_snapshot)
        
        # Also restore legacy fields for backward compatibility
        if "sentiment" in state and "sentiment" not in final_state:
            final_state["sentiment"] = state["sentiment"]
        
        return final_state
    
    return invoke_with_propagation


# =============================================================================
# GRAPH BUILDER HELPER
# =============================================================================

def get_sacred_flow_spec(config: Optional[SacredFlowConfig] = None) -> Dict[str, Any]:
    """
    Get the specification for building Sacred Flow in a graph.
    
    This returns everything graph_flow.py needs to add Sacred Flow:
    - nodes: List of node names to add
    - edges: List of (source, target) edges
    - conditional_edges: List of conditional edge specs
    - can_router: The routing function for CAN
    
    Args:
        config: Optional configuration (uses defaults if None)
        
    Returns:
        Dict with specification for graph building
    """
    if config is None:
        config = SacredFlowConfig()
    
    nodes = list(SACRED_FLOW_NODES)
    edges = list(SACRED_FLOW_EDGES)
    
    # Remove disabled nodes
    if not config.enable_orthodoxy:
        nodes.remove("orthodoxy")
        edges = [(s, t) for s, t in edges if s != "orthodoxy" and t != "orthodoxy"]
        # Update edge: normalizer → vault
        edges.append(("output_normalizer", "vault"))
    
    if not config.enable_vault:
        nodes.remove("vault")
        edges = [(s, t) for s, t in edges if s != "vault" and t != "vault"]
        # Update edge: orthodoxy → compose
        if config.enable_orthodoxy:
            edges.append(("orthodoxy", "compose"))
        else:
            edges.append(("output_normalizer", "compose"))
    
    if not config.enable_advisor:
        nodes.remove("advisor")
        edges = [(s, t) for s, t in edges if s != "advisor" and t != "advisor"]
    
    if not config.enable_proactive:
        nodes.remove("proactive_suggestions")
        edges = [(s, t) for s, t in edges if s != "proactive_suggestions" and t != "proactive_suggestions"]
    
    return {
        "nodes": nodes,
        "edges": edges,
        "can_router": create_can_to_advisor_router(config),
        "can_routes": {
            "advisor": "advisor",
            "proactive_suggestions": "proactive_suggestions",
        },
        "config": config,
    }


# =============================================================================
# VALIDATION
# =============================================================================

def validate_sacred_flow_state(state: Dict[str, Any]) -> List[str]:
    """
    Validate that state is ready for Sacred Flow.
    
    Returns list of warnings (empty if valid).
    """
    warnings = []
    
    # Check required fields
    if "route" not in state:
        warnings.append("Missing 'route' field - Sacred Flow needs routing context")
    
    if "input_text" not in state:
        warnings.append("Missing 'input_text' field - compose needs user input")
    
    return warnings
