"""
Dummy Test Domain — Intent Configuration (Test Vertical)
=========================================================

Absolute minimum viable domain plugin. Tests that the loading
contract works with the smallest possible implementation.

Created: February 15, 2026 (V1.0 Certification S4)
"""

from core.orchestration.intent_registry import (
    IntentDefinition,
    IntentRegistry,
)

CONTEXT_KEYWORDS = {}
AMBIGUOUS_PATTERNS = {}


def create_dummy_test_registry() -> IntentRegistry:
    """Factory function — required contract for domain plugins."""
    registry = IntentRegistry(domain_name="dummy_test")

    registry.register_intent(IntentDefinition(
        name="ping",
        description="Simple health check intent",
        examples=["ping", "are you there?"],
        synonyms=["health", "alive"],
    ))

    return registry
