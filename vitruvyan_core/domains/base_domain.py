"""
Vitruvyan Core — Domain Contract
=================================

This module defines the abstract interface that ANY domain must implement
to integrate with Vitruvyan's cognitive architecture.

A domain provides:
1. Entity Schema — What are the "things" this domain reasons about?
2. Signal Schema — What measurable attributes do entities have?
3. Scoring Factors — What dimensions contribute to decision-making?
4. Policies/Rules — Domain-specific constraints and validation rules
5. Explanation Templates — How to translate scores into human language

Examples of domains:
- Trade: entities=stocks, signals=momentum/volatility, factors=RSI/MACD
- Logistics: entities=routes, signals=traffic/weather, factors=cost/time
- Healthcare: entities=patients, signals=vitals, factors=risk_scores

This contract ensures Vitruvyan-Core remains domain-agnostic while
providing structured extension points for vertical specialization.

Author: Vitruvyan Core Team
Created: December 28, 2025
Status: ABSTRACT INTERFACE ONLY
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class DomainType(Enum):
    """Registered domain types"""
    GENERIC = "generic"
    EXAMPLE = "example"
    # Future domains will register here
    # TRADE = "trade"
    # LOGISTICS = "logistics"
    # HEALTHCARE = "healthcare"


@dataclass
class EntitySchema:
    """
    Defines the structure of domain entities.
    
    Examples:
    - Trade: ticker="AAPL", type="stock", sector="Technology"
    - Logistics: route_id="NYC-LAX", type="air", carrier="DHL"
    - Healthcare: patient_id="P12345", type="inpatient", ward="ICU"
    """
    entity_id: str                    # Unique identifier
    entity_type: str                  # Classification (stock, route, patient, etc.)
    category: Optional[str] = None    # Higher-level grouping (sector, region, specialty)
    metadata: Dict[str, Any] = None   # Domain-specific attributes


@dataclass
class SignalSchema:
    """
    Defines measurable attributes of entities.
    
    Examples:
    - Trade: momentum (RSI), trend (SMA), volatility (ATR)
    - Logistics: traffic_index, weather_severity, fuel_cost
    - Healthcare: heart_rate, blood_pressure, oxygen_saturation
    """
    signal_name: str                  # Human-readable name
    signal_type: str                  # continuous, discrete, categorical
    value: Any                        # Current measurement
    timestamp: Optional[str] = None   # When signal was captured
    confidence: Optional[float] = None # Signal quality (0.0-1.0)


@dataclass
class ScoringFactor:
    """
    Defines a dimension that contributes to composite scoring.
    
    Examples:
    - Trade: factor="momentum", weight=0.3, higher_is_better=True
    - Logistics: factor="cost", weight=0.4, higher_is_better=False
    - Healthcare: factor="risk_score", weight=0.5, higher_is_better=False
    """
    factor_name: str                  # Identifier
    weight: float                     # Contribution to composite (0.0-1.0)
    higher_is_better: bool            # Scoring direction
    description: str                  # Human explanation


@dataclass
class DomainPolicy:
    """
    Domain-specific constraints and validation rules.
    
    Examples:
    - Trade: min_liquidity=1M USD, max_volatility=50%
    - Logistics: max_route_distance=5000km, min_carrier_rating=4.0
    - Healthcare: emergency_response_time=15min, min_staff_ratio=1:4
    """
    policy_name: str
    rule_type: str                    # threshold, constraint, validation
    parameters: Dict[str, Any]
    enforcement: str                  # hard, soft, advisory


class BaseDomain(ABC):
    """
    Abstract base class for all Vitruvyan domains.
    
    Every domain plugin must implement these methods to integrate
    with the core agentic architecture.
    """
    
    @abstractmethod
    def get_domain_type(self) -> DomainType:
        """Return the domain identifier"""
        pass
    
    @abstractmethod
    def get_entity_schema(self) -> EntitySchema:
        """Define what entities look like in this domain"""
        pass
    
    @abstractmethod
    def get_signal_schemas(self) -> List[SignalSchema]:
        """Define what signals are tracked"""
        pass
    
    @abstractmethod
    def get_scoring_factors(self) -> List[ScoringFactor]:
        """Define how entities are scored"""
        pass
    
    @abstractmethod
    def get_policies(self) -> List[DomainPolicy]:
        """Define domain-specific rules"""
        pass
    
    @abstractmethod
    def compute_signal(self, entity: EntitySchema, signal_name: str) -> SignalSchema:
        """
        Compute a specific signal for an entity.
        
        This is where domain-specific logic lives.
        Example: For trade domain, computing RSI from price history.
        """
        pass
    
    @abstractmethod
    def explain_score(self, entity: EntitySchema, composite_score: float, 
                     factor_contributions: Dict[str, float]) -> str:
        """
        Generate human-readable explanation of why an entity scored as it did.
        
        This is the VEE integration point - domain provides narrative templates.
        """
        pass
    
    @abstractmethod
    def validate_entity(self, entity: EntitySchema) -> tuple[bool, Optional[str]]:
        """
        Check if an entity meets domain policies.
        
        Returns (is_valid, error_message)
        """
        pass


class GenericDomain(BaseDomain):
    """
    Minimal generic domain implementation.
    Used as fallback when no specific domain is loaded.
    """
    
    def get_domain_type(self) -> DomainType:
        return DomainType.GENERIC
    
    def get_entity_schema(self) -> EntitySchema:
        return EntitySchema(
            entity_id="generic_entity",
            entity_type="unknown",
            category=None,
            metadata={}
        )
    
    def get_signal_schemas(self) -> List[SignalSchema]:
        return [
            SignalSchema(
                signal_name="generic_signal",
                signal_type="continuous",
                value=0.0
            )
        ]
    
    def get_scoring_factors(self) -> List[ScoringFactor]:
        return [
            ScoringFactor(
                factor_name="identity",
                weight=1.0,
                higher_is_better=True,
                description="Identity factor (pass-through)"
            )
        ]
    
    def get_policies(self) -> List[DomainPolicy]:
        return []
    
    def compute_signal(self, entity: EntitySchema, signal_name: str) -> SignalSchema:
        return SignalSchema(
            signal_name=signal_name,
            signal_type="continuous",
            value=0.0,
            confidence=0.0
        )
    
    def explain_score(self, entity: EntitySchema, composite_score: float,
                     factor_contributions: Dict[str, float]) -> str:
        return f"Entity '{entity.entity_id}' has composite score: {composite_score:.2f}"
    
    def validate_entity(self, entity: EntitySchema) -> tuple[bool, Optional[str]]:
        return (True, None)


# Global registry for domain plugins
_DOMAIN_REGISTRY: Dict[str, BaseDomain] = {
    "generic": GenericDomain()
}


def register_domain(domain: BaseDomain) -> None:
    """Register a domain plugin with the core"""
    domain_type = domain.get_domain_type()
    _DOMAIN_REGISTRY[domain_type.value] = domain


def get_domain(domain_name: str = "generic") -> BaseDomain:
    """Retrieve a registered domain (defaults to generic)"""
    return _DOMAIN_REGISTRY.get(domain_name, _DOMAIN_REGISTRY["generic"])
