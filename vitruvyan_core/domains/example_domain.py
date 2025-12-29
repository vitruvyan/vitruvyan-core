"""
Vitruvyan Core — Example Domain (Placeholder)
==============================================

This is a MINIMAL example domain implementation showing how to use
the Domain Contract. It contains NO real logic.

Purpose: Demonstrate extensibility without hardcoding future verticals.

Author: Vitruvyan Core Team
Created: December 28, 2025
Status: PLACEHOLDER ONLY
"""

from vitruvyan_core.domains.base_domain import (
    BaseDomain,
    DomainType,
    EntitySchema,
    SignalSchema,
    ScoringFactor,
    DomainPolicy
)
from typing import List, Dict, Any, Optional


class ExampleDomain(BaseDomain):
    """
    Example domain showing contract implementation.
    Contains no real logic - purely demonstrative.
    """
    
    def get_domain_type(self) -> DomainType:
        return DomainType.EXAMPLE
    
    def get_entity_schema(self) -> EntitySchema:
        return EntitySchema(
            entity_id="example_001",
            entity_type="example_type",
            category="example_category",
            metadata={"note": "This is a placeholder"}
        )
    
    def get_signal_schemas(self) -> List[SignalSchema]:
        return [
            SignalSchema(
                signal_name="example_signal_1",
                signal_type="continuous",
                value=0.5,
                confidence=1.0
            ),
            SignalSchema(
                signal_name="example_signal_2",
                signal_type="discrete",
                value=10,
                confidence=0.8
            )
        ]
    
    def get_scoring_factors(self) -> List[ScoringFactor]:
        return [
            ScoringFactor(
                factor_name="factor_a",
                weight=0.6,
                higher_is_better=True,
                description="Example factor A (higher is better)"
            ),
            ScoringFactor(
                factor_name="factor_b",
                weight=0.4,
                higher_is_better=False,
                description="Example factor B (lower is better)"
            )
        ]
    
    def get_policies(self) -> List[DomainPolicy]:
        return [
            DomainPolicy(
                policy_name="example_threshold",
                rule_type="threshold",
                parameters={"min_value": 0.0, "max_value": 1.0},
                enforcement="soft"
            )
        ]
    
    def compute_signal(self, entity: EntitySchema, signal_name: str) -> SignalSchema:
        # Placeholder logic
        return SignalSchema(
            signal_name=signal_name,
            signal_type="continuous",
            value=0.5,
            confidence=0.5
        )
    
    def explain_score(self, entity: EntitySchema, composite_score: float,
                     factor_contributions: Dict[str, float]) -> str:
        explanation = f"Entity '{entity.entity_id}' scored {composite_score:.2f}.\n"
        explanation += "Factor contributions:\n"
        for factor, contrib in factor_contributions.items():
            explanation += f"  - {factor}: {contrib:.2f}\n"
        return explanation
    
    def validate_entity(self, entity: EntitySchema) -> tuple[bool, Optional[str]]:
        # Placeholder validation - always passes
        return (True, None)
