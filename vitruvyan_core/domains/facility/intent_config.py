"""
Facility Domain — Intent Configuration (Test Vertical)
=======================================================

Minimal domain plugin for V1.0 multi-vertical certification.
Covers facility/building management use case.

Created: February 15, 2026 (V1.0 Certification S4)
"""

from core.orchestration.intent_registry import (
    IntentDefinition,
    IntentRegistry,
    ScreeningFilter,
)

CONTEXT_KEYWORDS = {
    "hvac": ["heating", "ventilation", "air conditioning", "climate"],
    "maintenance": ["repair", "inspection", "work order", "ticket"],
    "occupancy": ["capacity", "utilization", "headcount"],
}

AMBIGUOUS_PATTERNS = {
    "floor": "Could refer to building floor or floor price",
    "space": "Could refer to physical space or disk space",
}


def create_facility_registry() -> IntentRegistry:
    """Factory function — required contract for domain plugins."""
    registry = IntentRegistry(domain_name="facility")

    registry.register_intent(IntentDefinition(
        name="building_status",
        description="Check building systems status (HVAC, lighting, security)",
        examples=["Building A status", "HVAC report for floor 3"],
        synonyms=["status", "building_check", "systems_check"],
        requires_entities=True,
        route_type="exec",
    ))

    registry.register_intent(IntentDefinition(
        name="maintenance_request",
        description="Create or check maintenance work orders",
        examples=["Create work order for elevator repair", "Pending maintenance tickets"],
        synonyms=["maintenance", "work_order", "repair_request"],
        requires_entities=False,
        route_type="exec",
    ))

    registry.register_intent(IntentDefinition(
        name="occupancy_report",
        description="Report on space utilization and occupancy",
        examples=["Floor 2 occupancy", "Conference room utilization this week"],
        synonyms=["occupancy", "utilization", "headcount"],
        requires_entities=True,
        route_type="exec",
    ))

    registry.register_filter(ScreeningFilter(
        name="building_zone",
        description="Filter by building zone or floor",
        value_type="string",
        keywords=["zone", "floor", "wing", "sector"],
    ))

    return registry
