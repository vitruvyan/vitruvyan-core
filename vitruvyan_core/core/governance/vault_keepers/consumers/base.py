"""
Vault Keepers — VaultRole Abstract Base Class

The foundational contract for all decision engines in the vault.
Every consumer in Vault Keepers implements VaultRole.

Design constraints:
  - process() is PURE: no side effects, no I/O, no network
  - Input is generic (Any) — type enforcement at concrete level
  - Output is generic (Any) — typically a domain object
  - No StreamBus, no Redis, no PostgreSQL — those belong to service layer
  - Fully testable in isolation with zero infrastructure

This ABC defines WHAT a Vault Role does.
The service layer's adapters define HOW it connects to buses and databases.

Sacred Order: Truth (Memory & Archival)
Layer: Foundational (consumers)
"""

from abc import ABC, abstractmethod
from typing import Any


class VaultRole(ABC):
    """
    Abstract base for all Vault Keepers decision engines.

    A VaultRole is a GUARDIAN — it takes input data and renders a judgment
    on vault operations (backup, restore, integrity, archive).
    It never executes I/O, writes to databases, or calls external APIs.

    Contract:
        role_name:   Unique identifier for this role (e.g., "sentinel", "archivist")
        description: Short English description of what this role does
        process():   Pure function: input → judgment (no side effects)
        can_handle(): Whether this role should process a given event

    Usage:
        class Sentinel(VaultRole):
            @property
            def role_name(self) -> str:
                return "sentinel"

            @property
            def description(self) -> str:
                return "Validates data integrity and detects corruption"

            def can_handle(self, event: Any) -> bool:
                return event.get('operation') == 'integrity_check'

            def process(self, event: Any) -> Any:
                # Pure logic: validate, evaluate, return IntegrityReport
                return IntegrityReport(...)
    """

    @property
    @abstractmethod
    def role_name(self) -> str:
        """Unique identifier for this role within the Sacred Order."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Short English description of this role's purpose."""
        ...

    @abstractmethod
    def can_handle(self, event: Any) -> bool:
        """
        Whether this role should process the given event.

        This enables selective routing: not every event goes to every consumer.
        The service layer uses this to decide whether to invoke process().
        """
        ...

    @abstractmethod
    def process(self, event: Any) -> Any:
        """
        Pure judgment function. No side effects.

        Args:
            event: The input to process (typically dict or domain object)

        Returns:
            A domain object (typically IntegrityReport, VaultSnapshot, RecoveryPlan, etc.)

        Raises:
            ValueError: If the input is malformed
            NotImplementedError: If the event type is not supported

        INVARIANTS (enforced by tests, not by this ABC):
            - Must not perform I/O
            - Must not modify external state
            - Must not call network services
            - Same input always produces same output (deterministic)
        """
        ...
