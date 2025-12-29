"""
Registries for factors and aggregation profiles.

Provides registration and retrieval mechanisms for the Neural Engine Core.
"""

from typing import Dict, Optional, List
from vitruvyan_core.core.cognitive.neural_engine.contracts import (
    AbstractFactor,
    NormalizerStrategy,
    AggregationProfile
)


class FactorRegistry:
    """
    Registry for factor implementations.
    
    Allows verticals to register their domain-specific factors
    and retrieve them by name.
    """
    
    def __init__(self):
        self._factors: Dict[str, AbstractFactor] = {}
    
    def register(self, factor: AbstractFactor) -> None:
        """
        Register a factor implementation.
        
        Args:
            factor: Factor instance to register
        
        Raises:
            ValueError: If factor name already registered
        """
        if factor.name in self._factors:
            raise ValueError(f"Factor '{factor.name}' is already registered")
        self._factors[factor.name] = factor
    
    def get(self, name: str) -> Optional[AbstractFactor]:
        """
        Retrieve a factor by name.
        
        Args:
            name: Factor name
        
        Returns:
            Factor instance or None if not found
        """
        return self._factors.get(name)
    
    def list_names(self) -> List[str]:
        """
        List all registered factor names.
        
        Returns:
            List of factor names
        """
        return list(self._factors.keys())
    
    def clear(self) -> None:
        """Remove all registered factors."""
        self._factors.clear()


class ProfileRegistry:
    """
    Registry for aggregation profile implementations.
    
    Allows verticals to register their scoring profiles
    and retrieve them by name.
    """
    
    def __init__(self):
        self._profiles: Dict[str, AggregationProfile] = {}
    
    def register(self, profile: AggregationProfile) -> None:
        """
        Register an aggregation profile.
        
        Args:
            profile: Profile instance to register
        
        Raises:
            ValueError: If profile name already registered
        """
        if profile.name in self._profiles:
            raise ValueError(f"Profile '{profile.name}' is already registered")
        self._profiles[profile.name] = profile
    
    def get(self, name: str) -> Optional[AggregationProfile]:
        """
        Retrieve a profile by name.
        
        Args:
            name: Profile name
        
        Returns:
            Profile instance or None if not found
        """
        return self._profiles.get(name)
    
    def list_names(self) -> List[str]:
        """
        List all registered profile names.
        
        Returns:
            List of profile names
        """
        return list(self._profiles.keys())
    
    def clear(self) -> None:
        """Remove all registered profiles."""
        self._profiles.clear()


class NormalizerRegistry:
    """
    Registry for normalizer strategy implementations.
    
    Allows registration and retrieval of normalization strategies.
    """
    
    def __init__(self):
        self._normalizers: Dict[str, NormalizerStrategy] = {}
    
    def register(self, normalizer: NormalizerStrategy) -> None:
        """
        Register a normalizer strategy.
        
        Args:
            normalizer: Normalizer instance to register
        
        Raises:
            ValueError: If normalizer name already registered
        """
        if normalizer.name in self._normalizers:
            raise ValueError(f"Normalizer '{normalizer.name}' is already registered")
        self._normalizers[normalizer.name] = normalizer
    
    def get(self, name: str) -> Optional[NormalizerStrategy]:
        """
        Retrieve a normalizer by name.
        
        Args:
            name: Normalizer name
        
        Returns:
            Normalizer instance or None if not found
        """
        return self._normalizers.get(name)
    
    def list_names(self) -> List[str]:
        """
        List all registered normalizer names.
        
        Returns:
            List of normalizer names
        """
        return list(self._normalizers.keys())
    
    def clear(self) -> None:
        """Remove all registered normalizers."""
        self._normalizers.clear()
