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

import hashlib
import json
import logging
import warnings
from abc import ABC
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, List, Optional, Type

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ContractMeta (Pydantic model for validation)
# ---------------------------------------------------------------------------

class ContractMeta(BaseModel):
    """Metadata descriptor for a registered contract."""

    model_config = ConfigDict(extra="forbid")

    contract_name: str
    contract_version: str
    owner: str = "core"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_hash: str = ""
    model_cls: Optional[Any] = Field(default=None, exclude=True)

    # Preserve backward-compat access via old field names
    @property
    def name(self) -> str:
        return self.contract_name

    @property
    def version(self) -> str:
        return self.contract_version


# ---------------------------------------------------------------------------
# ContractRegistry
# ---------------------------------------------------------------------------

class ContractRegistry:
    """
    Central registry for contract metadata.

    Supports lookup by name or by full contract_id (name@version).
    """

    _registry: Dict[str, ContractMeta] = {}

    @classmethod
    def register(cls, contract_cls: Type[BaseContract]) -> None:
        """Register a BaseContract subclass by name and name@version."""
        name = contract_cls.CONTRACT_NAME
        version = contract_cls.CONTRACT_VERSION
        contract_id = f"{name}@{version}"
        meta = ContractMeta(
            contract_name=name,
            contract_version=version,
            owner=contract_cls.CONTRACT_OWNER,
            schema_hash=cls._compute_schema_hash(contract_cls),
            model_cls=contract_cls,
        )
        cls._registry[contract_id] = meta
        # Also register by name (latest version wins)
        cls._registry[name] = meta
        logger.debug("[ContractRegistry] Registered %s", contract_id)

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Return registered ContractMeta or model class.

        If key contains '@' (contract_id), returns the model class.
        Otherwise returns ContractMeta.
        """
        if "@" in key:
            meta = cls._registry.get(key)
            return meta.model_cls if meta else None
        return cls._registry.get(key)

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a contract name is registered."""
        return name in cls._registry

    @classmethod
    def list_all(cls) -> Dict[str, Any]:
        """Return all registered contracts (keyed by contract_id)."""
        return {k: v for k, v in cls._registry.items() if "@" in k}

    @classmethod
    def all(cls) -> Dict[str, ContractMeta]:
        """Return a copy of the full registry (backward compat)."""
        return dict(cls._registry)

    @classmethod
    def _compute_schema_hash(cls, contract_cls: Type[BaseContract]) -> str:
        schema_str = json.dumps(contract_cls.model_json_schema(), sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# BaseContract
# ---------------------------------------------------------------------------

class _AutoRegisterMeta(type(BaseModel)):
    """Metaclass that auto-registers BaseContract subclasses."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

    def __init__(cls, name: str, bases: tuple, namespace: dict, **kwargs: Any) -> None:
        super().__init__(name, bases, namespace, **kwargs)
        # Auto-register if the subclass has all three required ClassVars
        if (
            hasattr(cls, "CONTRACT_NAME")
            and hasattr(cls, "CONTRACT_VERSION")
            and hasattr(cls, "CONTRACT_OWNER")
            and "CONTRACT_NAME" in namespace
        ):
            ContractRegistry.register(cls)


class BaseContract(BaseModel, metaclass=_AutoRegisterMeta):
    """
    Base class for all Vitruvyan contract models.

    Subclasses MUST declare the three ClassVar attributes:

        CONTRACT_NAME:    ClassVar[str] = "domain.entity"
        CONTRACT_VERSION: ClassVar[str] = "1.0.0"
        CONTRACT_OWNER:   ClassVar[str] = "sacred_order_name"
    """

    CONTRACT_NAME:    ClassVar[str]
    CONTRACT_VERSION: ClassVar[str]
    CONTRACT_OWNER:   ClassVar[str]

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def contract_id(cls) -> str:
        """Return canonical contract identifier: name@version."""
        return f"{cls.CONTRACT_NAME}@{cls.CONTRACT_VERSION}"

    def validate_invariants(self) -> List[str]:
        """Override in subclasses to return domain-specific violation messages."""
        return []

    def enforce(self, strict: bool = True) -> "BaseContract":
        """Validate invariants. Raises ValueError in strict mode, warns otherwise."""
        violations = self.validate_invariants()
        if violations:
            msg = "; ".join(violations)
            if strict:
                raise ValueError(msg)
            else:
                warnings.warn(msg, stacklevel=2)
        return self

    def get_meta(self) -> ContractMeta:
        """Return ContractMeta for this instance's class."""
        return ContractMeta(
            contract_name=self.CONTRACT_NAME,
            contract_version=self.CONTRACT_VERSION,
            owner=self.CONTRACT_OWNER,
            schema_hash=ContractRegistry._compute_schema_hash(type(self)),
        )

    def to_dict(self, include_meta: bool = False) -> Dict[str, Any]:
        """Serialize to dict, optionally including contract metadata."""
        d = self.model_dump()
        if include_meta:
            d["__contract_meta__"] = {
                "contract_name": self.CONTRACT_NAME,
                "contract_version": self.CONTRACT_VERSION,
                "owner": self.CONTRACT_OWNER,
            }
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any], version_check: bool = False) -> "BaseContract":
        """Deserialize from dict. Optionally warn on version mismatch."""
        data = dict(data)
        meta = data.pop("__contract_meta__", None)
        if version_check and meta:
            stored_version = meta.get("contract_version", "")
            if stored_version != cls.CONTRACT_VERSION:
                warnings.warn(
                    f"Contract version mismatch: stored={stored_version}, "
                    f"current={cls.CONTRACT_VERSION}",
                    stacklevel=2,
                )
        return cls(**data)


# ---------------------------------------------------------------------------
# IContractPlugin
# ---------------------------------------------------------------------------

class IContractPlugin(ABC):
    """
    ABC for all contract plugin interfaces.

    Mirrors BaseContract metadata with the PLUGIN_* prefix so the
    plugin registry can distinguish plugins from data objects.
    """

    PLUGIN_CONTRACT_NAME:    ClassVar[str] = "base_plugin"
    PLUGIN_CONTRACT_VERSION: ClassVar[str] = "0.0.0"
    PLUGIN_CONTRACT_OWNER:   ClassVar[str] = "core"

    @classmethod
    def plugin_contract_id(cls) -> str:
        """Return canonical plugin identifier: name@version."""
        return f"{cls.PLUGIN_CONTRACT_NAME}@{cls.PLUGIN_CONTRACT_VERSION}"
