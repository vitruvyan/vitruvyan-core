"""
Vitruvyan Core — Explainability Contract
=========================================

Abstract interface for domain-specific explainability providers.

This contract allows ANY domain to provide:
1. Explanation Templates — Narrative structures for different explanation levels
2. Metric Definitions — What each metric means in domain context
3. Entity Referencing — How to refer to entities in natural language

Domains implement ExplainabilityProvider to customize VEE Engine narratives
without changing core explainability logic.

Author: Vitruvyan Core Team
Created: December 30, 2025
Status: ABSTRACT CONTRACT
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class ExplanationTemplate:
    """
    Domain-specific narrative templates for multi-level explanations.

    Templates use {placeholders} that get filled with analysis data.
    Domains can provide multiple variants for linguistic variety.
    """
    summary_template: str        # Concise explanation for general users
    technical_template: str      # Detailed analysis for analysts
    detailed_template: str       # Comprehensive breakdown for experts
    contextual_template: str     # Historical/contextual enrichment

    # Optional: Multiple variants for natural language variety
    summary_variants: List[str] = None
    technical_variants: List[str] = None
    detailed_variants: List[str] = None


@dataclass
class MetricDefinition:
    """
    Defines what a metric means in domain-specific terms.

    Provides semantic context for explainability generation.
    """
    name: str                    # Metric identifier (e.g., "momentum_z")
    description: str             # Human-readable explanation
    unit: str                    # Unit of measurement (e.g., "z-score", "percentage")
    interpretation: str          # How to interpret values ("higher is better", "lower indicates risk")
    normal_range: tuple[float, float]  # Expected range (min, max)
    display_name: str = None     # Pretty name for UI (defaults to name)


class ExplainabilityProvider(ABC):
    """
    Interface that domains implement to provide explainability context.

    VEE Engine calls these methods to generate domain-appropriate narratives.
    """

    @abstractmethod
    def get_explanation_templates(self) -> ExplanationTemplate:
        """
        Return domain-specific narrative templates.

        Templates should use placeholders like:
        - {entity_id}: The entity being explained
        - {signals_text}: Summary of identified signals
        - {dominant_factor}: Primary driver of the analysis
        - {intensity}: Signal strength (0.0-1.0)
        - {sentiment_direction}: Overall orientation
        """
        pass

    @abstractmethod
    def get_metric_definitions(self) -> Dict[str, MetricDefinition]:
        """
        Define what each metric means in this domain.

        Returns mapping of metric_name -> MetricDefinition.
        VEE uses this to understand metric semantics for explanation generation.
        """
        pass

    @abstractmethod
    def format_entity_reference(self, entity_id: str) -> str:
        """
        How to refer to entities in natural language narratives.

        Examples:
        - Finance: "AAPL entity" or "Apple Inc."
        - Logistics: "NYC-LAX route" or "New York to Los Angeles flight"
        - Healthcare: "Patient P12345" or "Cardiology case #12345"
        """
        pass

    @abstractmethod
    def get_signal_descriptions(self) -> Dict[str, str]:
        """
        Domain-specific descriptions for signal types.

        Maps signal categories to natural language descriptions.
        Used by VEE Analyzer to generate semantic signal text.

        Examples:
        - "momentum": "price momentum indicators"
        - "risk": "risk profile metrics"
        - "sentiment": "market sentiment signals"
        """
        pass

    @abstractmethod
    def get_factor_categories(self) -> Dict[str, str]:
        """
        Map factor names to semantic categories.

        Used by VEE to group and describe factors in explanations.

        Examples:
        - "momentum_z": "momentum"
        - "trend_z": "trend analysis"
        - "vola_z": "volatility"
        """
        pass