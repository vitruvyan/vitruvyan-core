"""
Energy Domain — Intent Configuration (Test Vertical)
=====================================================

Minimal domain plugin for V1.0 multi-vertical certification.
Demonstrates that the core OS loads domain plugins dynamically
without hardcoded dependencies.

Created: February 15, 2026 (V1.0 Certification S4)
"""

from core.orchestration.intent_registry import (
    IntentDefinition,
    IntentRegistry,
    ScreeningFilter,
)

# Domain-specific context keywords (optional)
CONTEXT_KEYWORDS = {
    "grid": ["power grid", "electrical grid", "smart grid"],
    "renewable": ["solar", "wind", "hydroelectric", "geothermal"],
    "consumption": ["kWh", "megawatt", "energy usage", "demand"],
}

# Ambiguous patterns (optional)
AMBIGUOUS_PATTERNS = {
    "load": "Could refer to electrical load or data loading",
    "plant": "Could refer to power plant or manufacturing plant",
}


def create_energy_registry() -> IntentRegistry:
    """Factory function — required contract for domain plugins."""
    registry = IntentRegistry(domain_name="energy")

    registry.register_intent(IntentDefinition(
        name="grid_status",
        description="Check power grid status and load distribution",
        examples=["Show grid status", "Current load on grid sector A"],
        synonyms=["grid", "load_status", "power_status"],
        requires_entities=True,
        route_type="exec",
    ))

    registry.register_intent(IntentDefinition(
        name="forecast_demand",
        description="Forecast energy demand for a region or time period",
        examples=["Forecast demand for next week", "Predict consumption Q2"],
        synonyms=["forecast", "predict_demand", "demand_forecast"],
        requires_entities=False,
        route_type="exec",
    ))

    registry.register_intent(IntentDefinition(
        name="renewable_analysis",
        description="Analyze renewable energy source performance",
        examples=["Solar panel efficiency report", "Wind farm output analysis"],
        synonyms=["renewable", "green_energy", "clean_energy"],
        requires_entities=True,
        route_type="exec",
    ))

    registry.register_filter(ScreeningFilter(
        name="energy_source",
        description="Filter by energy source type",
        value_type="enum",
        enum_values=["solar", "wind", "hydro", "nuclear", "gas", "coal"],
        keywords=["source", "type", "fuel"],
    ))

    return registry
