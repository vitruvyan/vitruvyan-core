"""
Orthodoxy Wardens — SacredRole Abstract Base Class

The foundational contract for all decision engines in the tribunal.
Every consumer in Orthodoxy Wardens implements SacredRole.

Design constraints:
  - process() is PURE: no side effects, no I/O, no network
  - Input is generic (Any) — type enforcement at concrete level
  - Output is generic (Any) — typically a Verdict, but may be Finding or LogDecision
  - No StreamBus, no Redis, no PostgreSQL — those belong to service layer
  - Fully testable in isolation with zero infrastructure

This ABC defines WHAT a Sacred Role does.
The service layer's adapters define HOW it connects to buses and databases.

Sacred Order: Truth & Governance
Layer: Foundational (consumers)
"""

from abc import ABC, abstractmethod
from typing import Any


class SacredRole(ABC):
    """
    Abstract base for all Orthodoxy Wardens decision engines.

    A SacredRole is a JUDGE — it takes input data and renders a judgment.
    It never executes corrections, writes to databases, or calls external APIs.

    Contract:
        role_name:   Unique identifier for this role (e.g., "inquisitor", "confessor")
        description: Short English description of what this role judges
        process():   Pure function: input → judgment (no side effects)
        can_handle(): Whether this role should process a given event

    Usage:
        class Inquisitor(SacredRole):
            @property
            def role_name(self) -> str:
                return "inquisitor"

            @property
            def description(self) -> str:
                return "Classifies confessions by compliance category and severity"

            def can_handle(self, event: Any) -> bool:
                return hasattr(event, 'trigger_type')

            def process(self, event: Any) -> Any:
                # Pure logic: classify, evaluate, return Finding/Verdict
                return Verdict.blessed(confidence=0.95)
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
            event: The input to judge (typically OrthodoxyEvent, Confession, or dict)

        Returns:
            A judgment object (typically Verdict, Finding, or LogDecision)

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

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} role='{self.role_name}'>"
