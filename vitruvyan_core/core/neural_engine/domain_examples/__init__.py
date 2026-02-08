"""
Domain implementation examples for Neural Engine.

This package contains stub implementations showing how to create
domain-specific providers and strategies.

Use these as templates when implementing your own domain:
- Finance: TickerDataProvider, FinancialScoringStrategy
- Healthcare: PatientDataProvider, ClinicalScoringStrategy
- Logistics: ShipmentDataProvider, DeliveryScoringStrategy
"""

from .mock_data_provider import MockDataProvider
from .mock_scoring_strategy import MockScoringStrategy

__all__ = [
    'MockDataProvider',
    'MockScoringStrategy',
]
