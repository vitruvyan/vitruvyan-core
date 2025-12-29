"""
Additional normalizer implementations (OPTIONAL PATTERNS).

These are not part of the core substrate. They demonstrate alternative
normalization strategies but are not required or preferred.
"""

from vitruvyan_core.patterns.neural_engine.normalizers.minmax import MinMaxNormalizer
from vitruvyan_core.patterns.neural_engine.normalizers.rank import RankNormalizer

__all__ = [
    "MinMaxNormalizer",
    "RankNormalizer",
]
