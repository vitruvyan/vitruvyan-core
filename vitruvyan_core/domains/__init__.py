"""
Vitruvyan Core — Domains Package
=================================

Domain extension system for Vitruvyan's cognitive architecture.

This package provides:
- base_domain.py: Abstract contract that ALL domains must implement
- example_domain.py: Minimal placeholder showing extensibility

Future domains (trade, logistics, healthcare, etc.) will be added
as separate packages/plugins that implement the BaseDomain contract.

Author: Vitruvyan Core Team
Created: December 28, 2025
"""

from domains.base_domain import (
    BaseDomain,
    GenericDomain,
    DomainType,
    EntitySchema,
    SignalSchema,
    ScoringFactor,
    DomainPolicy,
    register_domain,
    get_domain
)

__all__ = [
    "BaseDomain",
    "GenericDomain",
    "DomainType",
    "EntitySchema",
    "SignalSchema",
    "ScoringFactor",
    "DomainPolicy",
    "register_domain",
    "get_domain"
]
