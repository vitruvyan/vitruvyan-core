"""
BaseContract — Vitruvyan Contract Foundation
=============================================

All data contracts in vitruvyan_core/contracts/ MUST inherit from
``BaseContract``.  Plugin/interface contracts (ABCs) use ``IContractPlugin``.

Provides:
  - Schema versioning (semver ClassVar, immutable per class)
  - Contract identity (unique name, owner Sacred Order)
  - Validation hooks (validate_invariants() override point)
  - Enforcement (enforce() — strict raise or warn mode)
  - Serialization (to_dict / from_dict with version checking)
  - Registry integration (auto-registration on class definition)

LIVELLO 1 compliance: Pure Python + Pydantic. No I/O. No external deps.

> **Last updated**: February 28, 2026 19:30 UTC

Author: Vitruvyan Core Team
"""

from __future__ import annotations

import hashlib
import logging
import warnings
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# ContractMeta — per-instance metadata (lazy)
# ─────────────────────────────────────────────────────────────

class ContractMeta(BaseModel):
    """Immutable metadata snapshot attached to a contract instance."""

    model_config = ConfigDict(extra="forbid")

    contract_name: str = Field(description="e.g. 'ingestion.payload'")
    contract_version: str = Field(description="semver string: '1.0.0'")
    owner: str = Field(default="core", description="Sacred Order or 'core'")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this metadata snapshot was created",
    )
    schema_hash: str = Field(
        default="",
        description="SHA-256 prefix of the Pydantic model JSON schema",
    )


# ─────────────────────────────────────────────────────────────
# ContractRegistry — auto-populated via __init_subclass__
# ─────────────────────────────────────────────────────────────

class ContractRegistry:
    """
    In-memory registry of all known BaseContract subclasses.

    Contracts auto-register on class definition — no manual wiring needed.
    Importing any module that defines a BaseContract subclass is enough.
    """

    _contracts: ClassVar[Dict[str, type]] = {}

    @classmethod
    def register(cls, contract_class: type) -> None:
        """Register a contract class by its contract_id."""
        cid = getattr(contract_class, "CONTRACT_NAME", "base")
        ver = getattr(contract_class, "CONTRACT_VERSION", "0.0.0")
        key = f"{cid}@{ver}"
        if key in cls._contracts and cls._contracts[key] is not contract_class:
            logger.debug("ContractRegistry: overwriting '%s' with %r", key, contract_class)
        cls._contracts[key] = contract_class

    @classmethod
    def get(cls, contract_id: str) -> Optional[type]:
        """Return class for 'name@version', or None."""
        return cls._contracts.get(contract_id)

    @classmethod
    def list_all(cls) -> Dict[str, str]:
        """Return {contract_id: fully-qualified class name}."""
        return {k: f"{v.__module__}.{v.__qualname__}" for k, v in cls._contracts.items()}

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """True if any registration matches the given contract name (any version)."""
        return any(k.startswith(f"{name}@") for k in cls._contracts)

    @classmethod
    def clear(cls) -> None:
        """Empty the registry (test helper only)."""
        cls._contracts.clear()


# ─────────────────────────────────────────────────────────────
# BaseContract — foundation for all data contracts
# ─────────────────────────────────────────────────────────────

class BaseContract(BaseModel):
    """
    Foundation for ALL data contracts in Vitruvyan Core.

    Subclasses MUST set:
      - CONTRACT_NAME:    ClassVar[str]  — e.g. "ingestion.payload"
      - CONTRACT_VERSION: ClassVar[str]  — semver, e.g. "1.0.0"
      - CONTRACT_OWNER:   ClassVar[str]  — Sacred Order, e.g. "perception"

    Subclasses MAY override:
      - validate_invariants() — domain-specific invariants beyond Pydantic
      - on_violation()        — custom violation handler (default: log/raise)
    """

    model_config = ConfigDict(extra="forbid")

    # --- Class-level identity (subclasses MUST override) ---
    CONTRACT_NAME: ClassVar[str] = "base"
    CONTRACT_VERSION: ClassVar[str] = "0.0.0"
    CONTRACT_OWNER: ClassVar[str] = "core"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Skip auto-registration for the base class itself
        if cls is not BaseContract:
            ContractRegistry.register(cls)

    # ── Contract identity ──────────────────────────────────

    @classmethod
    def contract_id(cls) -> str:
        """Unique identifier: '{CONTRACT_NAME}@{CONTRACT_VERSION}'."""
        return f"{cls.CONTRACT_NAME}@{cls.CONTRACT_VERSION}"

    # ── Invariant hooks ────────────────────────────────────

    def validate_invariants(self) -> List[str]:
        """
        Override to add domain-specific invariants beyond Pydantic validation.

        Returns:
            List of violation messages. Empty list = all invariants satisfied.
        """
        return []

    def on_violation(self, violations: List[str], *, strict: bool) -> None:
        """
        Handle invariant violations.

        Default behaviour:
          - strict=True  → raise ValueError with all violations joined
          - strict=False → log a warning for each violation
        """
        if not violations:
            return
        messages = "; ".join(violations)
        if strict:
            raise ValueError(
                f"[{self.contract_id()}] invariant violations: {messages}"
            )
        for msg in violations:
            logger.warning("[%s] violation: %s", self.contract_id(), msg)

    def enforce(self, *, strict: bool = False) -> "BaseContract":
        """
        Run validate_invariants() and handle any violations.

        Args:
            strict: If True, raise ValueError on first violation set.
                    If False, emit warnings and continue.

        Returns:
            self — allows chaining: ``payload = MyContract(**data).enforce(strict=True)``
        """
        violations = self.validate_invariants()
        if violations:
            self.on_violation(violations, strict=strict)
        return self

    # ── Metadata ───────────────────────────────────────────

    def get_meta(self) -> ContractMeta:
        """Return metadata for this contract instance (computed on demand)."""
        schema_str = self.__class__.model_json_schema().__repr__()
        schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()[:16]
        return ContractMeta(
            contract_name=self.CONTRACT_NAME,
            contract_version=self.CONTRACT_VERSION,
            owner=self.CONTRACT_OWNER,
            schema_hash=schema_hash,
        )

    # ── Serialization ──────────────────────────────────────

    def to_dict(self, *, include_meta: bool = False) -> Dict[str, Any]:
        """
        Serialize to dict.

        Args:
            include_meta: If True, attaches a ``__contract_meta__`` key.
        """
        data: Dict[str, Any] = self.model_dump()
        if include_meta:
            data["__contract_meta__"] = self.get_meta().model_dump()
        return data

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        *,
        version_check: bool = True,
    ) -> "BaseContract":
        """
        Deserialize from dict.

        Args:
            data:          Source dictionary (may contain ``__contract_meta__``).
            version_check: If True, emit a warning when the stored version
                           differs from the current CONTRACT_VERSION.
        """
        payload = {k: v for k, v in data.items() if k != "__contract_meta__"}
        if version_check and "__contract_meta__" in data:
            stored_version = data["__contract_meta__"].get("contract_version", "")
            if stored_version and stored_version != cls.CONTRACT_VERSION:
                warnings.warn(
                    f"[{cls.contract_id()}] deserializing data produced by version "
                    f"'{stored_version}' into current version '{cls.CONTRACT_VERSION}'",
                    UserWarning,
                    stacklevel=2,
                )
        return cls(**payload)


# ─────────────────────────────────────────────────────────────
# IContractPlugin — base for ABC/Protocol contracts
# ─────────────────────────────────────────────────────────────

class IContractPlugin(ABC):
    """
    Base for plugin/interface contracts (ISemanticPlugin, IComprehensionPlugin, …).

    Adds contract identity metadata to ABC interfaces.
    Uses ABC instead of BaseModel because plugins define method contracts,
    not data schemas — they cannot inherit from BaseModel.
    """

    PLUGIN_CONTRACT_NAME: ClassVar[str] = "base_plugin"
    PLUGIN_CONTRACT_VERSION: ClassVar[str] = "0.0.0"
    PLUGIN_CONTRACT_OWNER: ClassVar[str] = "core"

    @classmethod
    def plugin_contract_id(cls) -> str:
        """Unique identifier: '{PLUGIN_CONTRACT_NAME}@{PLUGIN_CONTRACT_VERSION}'."""
        return f"{cls.PLUGIN_CONTRACT_NAME}@{cls.PLUGIN_CONTRACT_VERSION}"


# ─────────────────────────────────────────────────────────────
# Exports
# ─────────────────────────────────────────────────────────────

__all__ = [
    "BaseContract",
    "ContractMeta",
    "ContractRegistry",
    "IContractPlugin",
]
