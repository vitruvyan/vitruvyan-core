"""
Tenancy Contract — Multi-Tenant Scope & Isolation
===================================================

Governs how tenant identity propagates through the Vitruvyan epistemic
kernel and how data isolation is enforced across services.

This contract is **domain-agnostic**: it defines the interface for tenant
scope resolution and enforcement.  Verticals (e.g. AiComSec, finance)
implement concrete resolvers backed by their own identity stores.

Sacred Order: Truth (Orthodoxy Wardens)

Contract guarantees:
  1. Tenant identity  — every tenant has a unique, stable ``tenant_id``
  2. Scope isolation   — services can resolve allowed tenants per request
  3. Mode awareness    — bootstrap (audit-only) vs enforced (hard 403)
  4. Propagation       — tenant_id flows through ingestion, graph state,
                         evidence packs, and Qdrant collection naming
  5. Internal tenants  — system/internal tenants (e.g. shared corpora)
                         are marked ``is_internal=True`` and excluded
                         from user-facing lists by default

LIVELLO 1: Pure Python + Pydantic. No I/O, no external dependencies.

> **Last updated**: March 3, 2026 18:00 UTC

Author: Vitruvyan Core Team
Contract Version: 1.0.0
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Set

from pydantic import ConfigDict, Field

from .base import BaseContract, IContractPlugin

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Stream channel constants (Synaptic Conclave — tenancy events)
# ─────────────────────────────────────────────────────────────

CHANNEL_TENANT_CREATED      = "truth.tenancy.tenant_created"
CHANNEL_TENANT_DEACTIVATED  = "truth.tenancy.tenant_deactivated"
CHANNEL_TENANT_SCOPE_DENIED = "truth.tenancy.scope_denied"


# ─────────────────────────────────────────────────────────────
# TenancyMode — operational mode enum
# ─────────────────────────────────────────────────────────────

class TenancyMode(str, Enum):
    """
    Operational mode for tenant scope enforcement.

    bootstrap — All tenants visible.  Violations are logged (audit trail)
                but never blocked.  Designed for pre-identity-provider setups.
    enforced  — Hard 403 on scope violations.  Requires an identity provider
                (e.g. Keycloak) to resolve per-request allowed tenants.
    """

    BOOTSTRAP = "bootstrap"
    ENFORCED  = "enforced"


# ─────────────────────────────────────────────────────────────
# TenantDescriptor — immutable tenant identity
# ─────────────────────────────────────────────────────────────

class TenantDescriptor(BaseContract):
    """
    Immutable descriptor for a registered tenant.

    Every tenant in the system MUST have a TenantDescriptor.
    The ``tenant_id`` is the primary isolation key across all subsystems:
    database rows, Qdrant collections, evidence packs, graph state.
    """

    CONTRACT_NAME: ClassVar[str]    = "tenancy.tenant"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER: ClassVar[str]   = "truth"

    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(
        description="Unique tenant identifier — primary isolation key",
    )
    name: str = Field(
        description="Short human-readable tenant name",
    )
    display_name: str = Field(
        default="",
        description="UI-friendly display name (falls back to name if empty)",
    )
    status: str = Field(
        default="active",
        description="Tenant lifecycle status: active, suspended, archived",
    )
    is_internal: bool = Field(
        default=False,
        description="True for system/shared tenants (e.g. normative corpora). "
                    "Internal tenants are excluded from user-facing lists by default.",
    )

    def validate_invariants(self) -> List[str]:
        violations: List[str] = []
        if not self.tenant_id or not self.tenant_id.strip():
            violations.append("tenant_id must not be empty or whitespace")
        if not self.name or not self.name.strip():
            violations.append("name must not be empty or whitespace")
        if self.status not in ("active", "suspended", "archived"):
            violations.append(
                f"status must be 'active', 'suspended', or 'archived', got '{self.status}'"
            )
        return violations

    @property
    def effective_display_name(self) -> str:
        """Display name for UI — falls back to name if display_name is empty."""
        return self.display_name.strip() or self.name


# ─────────────────────────────────────────────────────────────
# ScopeVerdict — result of a scope check
# ─────────────────────────────────────────────────────────────

class ScopeVerdict(BaseContract):
    """
    Result of a tenant scope check.

    Returned by ``ITenancyPlugin.check_scope()`` to indicate whether
    access is allowed, and to carry audit metadata.
    """

    CONTRACT_NAME: ClassVar[str]    = "tenancy.scope_verdict"
    CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    CONTRACT_OWNER: ClassVar[str]   = "truth"

    model_config = ConfigDict(extra="forbid")

    allowed: bool = Field(description="Whether access is permitted")
    mode: TenancyMode = Field(description="Active tenancy mode when check was performed")
    tenant_id: str = Field(description="Tenant being accessed")
    resource_type: str = Field(
        default="",
        description="Type of resource being accessed (e.g. 'assessment', 'evidence')",
    )
    resource_id: str = Field(
        default="",
        description="ID of the specific resource being accessed",
    )
    reason: str = Field(
        default="",
        description="Human-readable reason (especially for denials)",
    )
    audit_only: bool = Field(
        default=False,
        description="True when in bootstrap mode — violation was logged but not blocked",
    )

    def validate_invariants(self) -> List[str]:
        violations: List[str] = []
        if not self.tenant_id:
            violations.append("tenant_id must not be empty")
        if self.audit_only and self.mode != TenancyMode.BOOTSTRAP:
            violations.append("audit_only=True is only valid in bootstrap mode")
        return violations


# ─────────────────────────────────────────────────────────────
# ITenancyPlugin — interface contract for tenant resolution
# ─────────────────────────────────────────────────────────────

class ITenancyPlugin(IContractPlugin):
    """
    Interface contract for tenant scope resolution and enforcement.

    Verticals implement this to provide:
    - Tenant registry access (list/get/create tenants)
    - Per-request scope resolution (who can see what)
    - Scope enforcement (bootstrap=audit vs enforced=403)

    The plugin is an ABC — concrete implementations live in verticals
    or service adapters, not in core.
    """

    PLUGIN_CONTRACT_NAME: ClassVar[str]    = "tenancy.resolver"
    PLUGIN_CONTRACT_VERSION: ClassVar[str] = "1.0.0"
    PLUGIN_CONTRACT_OWNER: ClassVar[str]   = "truth"

    # ── Registry operations ───────────────────────────────

    @abstractmethod
    def list_tenants(
        self,
        *,
        include_internal: bool = False,
        active_only: bool = True,
    ) -> List[TenantDescriptor]:
        """
        List registered tenants.

        Args:
            include_internal: Include system/internal tenants.
            active_only: Only return tenants with status='active'.
        """
        ...

    @abstractmethod
    def get_tenant(self, tenant_id: str) -> Optional[TenantDescriptor]:
        """Return a single tenant by ID, or None if not found."""
        ...

    # ── Scope resolution ──────────────────────────────────

    @abstractmethod
    def resolve_allowed_tenants(
        self,
        *,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> Set[str]:
        """
        Resolve the set of tenant_ids the current caller is allowed to access.

        In bootstrap mode: returns ALL active tenant_ids (no restriction).
        In enforced mode: extracts identity from request_context (e.g. JWT
        claims) and returns only the caller's authorized tenant_ids.

        Args:
            request_context: Opaque dict carrying request metadata
                             (headers, JWT claims, API key, etc.).
                             Verticals define what goes in here.
        """
        ...

    # ── Scope enforcement ─────────────────────────────────

    @abstractmethod
    def check_scope(
        self,
        tenant_id: str,
        allowed_tenants: Set[str],
        *,
        resource_type: str = "",
        resource_id: str = "",
    ) -> ScopeVerdict:
        """
        Check whether accessing ``tenant_id`` is within scope.

        In bootstrap mode: always returns ``allowed=True`` with
        ``audit_only=True`` if the tenant is out of scope (log, don't block).

        In enforced mode: returns ``allowed=False`` if ``tenant_id``
        is not in ``allowed_tenants``.

        Args:
            tenant_id:       The tenant being accessed.
            allowed_tenants: Set from resolve_allowed_tenants().
            resource_type:   Optional label for audit (e.g. 'assessment').
            resource_id:     Optional ID for audit trail.
        """
        ...

    @abstractmethod
    def filter_by_scope(
        self,
        tenant_ids: List[str],
        allowed_tenants: Set[str],
    ) -> List[str]:
        """
        Filter a list of tenant_ids to only those in scope.

        In bootstrap mode: returns all (no filtering).
        In enforced mode: returns intersection.
        """
        ...

    # ── Mode query ────────────────────────────────────────

    @abstractmethod
    def get_mode(self) -> TenancyMode:
        """Return the current tenancy enforcement mode."""
        ...


# ─────────────────────────────────────────────────────────────
# Exports
# ─────────────────────────────────────────────────────────────

__all__ = [
    # Channel constants
    "CHANNEL_TENANT_CREATED",
    "CHANNEL_TENANT_DEACTIVATED",
    "CHANNEL_TENANT_SCOPE_DENIED",
    # Enums
    "TenancyMode",
    # Data contracts
    "TenantDescriptor",
    "ScopeVerdict",
    # Plugin interface
    "ITenancyPlugin",
]
