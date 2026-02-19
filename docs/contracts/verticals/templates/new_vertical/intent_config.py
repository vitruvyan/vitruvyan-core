"""Domain intent configuration template."""

from core.orchestration.intent_registry import IntentRegistry


def create_example_registry() -> IntentRegistry:
    registry = IntentRegistry(domain_name="example")
    # register intents here
    return registry

