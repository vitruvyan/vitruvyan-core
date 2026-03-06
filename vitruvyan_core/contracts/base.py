"""
Vitruvyan Contracts — Base Layer
=================================
Foundational types for the contracts system.

Contract classes extend BaseContract (a Pydantic BaseModel) and declare
three class-level metadata attributes:

    CONTRACT_NAME     — dot-notation identifier  (e.g. "comprehension.result")
    CONTRACT_VERSION  — semver string             (e.g. "1.0.0")
    CONTRACT_OWNER    — Sacred Order name         (e.g. "babel_gardens")

Plugin interfaces extend IContractPlugin (ABC) and mirror those attributes
with the PLUGIN_* prefix.

Author: Vitruvyan Core Team
Created: March 2026
"""

from __future__ import annotations

import logging
from abc import ABC
from dataclasses import dataclass, field
from typing import ClassVar, Dict, Optional, Type

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BaseContract
# ---------------------------------------------------------------------------

class BaseContract(BaseModel):
    """
    Base class for all Vitruvyan contract models.

    Subclasses MUST declare the three ClassVar attributes:

        CONTRACT_NAME:    ClassVar[str] = "domain.entity"
        CONTRACT_VERSION: ClassVar[str] = "1.0.0"
        CONTRACT_OWNER:   ClassVar[str] = "sacred_order_name"
    """

    # Subclasses declare these — no default values here so that
    # forgetting them causes a clear AttributeError at import time.
    CONTRACT_NAME:    ClassVar[str]
    CONTRACT_VERSION: ClassVar[str]
    CONTRACT_OWNER:   ClassVar[str]

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# IContractPlugin
# ---------------------------------------------------------------------------

class IContractPlugin(ABC):
    """
    ABC for all contract plugin interfaces.

    Mirrors BaseContract metadata with the PLUGIN_* prefix so the
    plugin registry can distinguish plugins from data objects.
    """

    PLUGIN_CONTRACT_NAME:    ClassVar[str]
    PLUGIN_CONTRACT_VERSION: ClassVar[str]
    PLUGIN_CONTRACT_OWNER:   ClassVar[str]


# ---------------------------------------------------------------------------
# ContractMeta  (lightweight descriptor, not a Pydantic model)
# ---------------------------------------------------------------------------

@dataclass
class ContractMeta:
    """Lightweight descriptor for a registered contract."""

    name: str
    version: str
    owner: str
    model_cls: Optional[Type[BaseContract]] = None
    description: str = ""
    tags: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# ContractRegistry
# ---------------------------------------------------------------------------

class ContractRegistry:
    """
    Central registry for contract metadata.

    Usage::

        from contracts.base import ContractRegistry
        ContractRegistry.register(MyContract)
        meta = ContractRegistry.get("comprehension.result")
    """

    _registry: Dict[str, ContractMeta] = {}

    @classmethod
    def register(cls, contract_cls: Type[BaseContract]) -> None:
        """Register a BaseContract subclass."""
        name = contract_cls.CONTRACT_NAME
        if name in cls._registry:
            logger.debug("[ContractRegistry] Re-registering %s", name)
        cls._registry[name] = ContractMeta(
            name=name,
            version=contract_cls.CONTRACT_VERSION,
            owner=contract_cls.CONTRACT_OWNER,
            model_cls=contract_cls,
        )

    @classmethod
    def get(cls, name: str) -> Optional[ContractMeta]:
        """Return registered ContractMeta or None."""
        return cls._registry.get(name)

    @classmethod
    def all(cls) -> Dict[str, ContractMeta]:
        """Return a copy of the full registry."""
        return dict(cls._registry)
