"""
Orthodoxy Wardens — Declarative Workflow Definitions

Workflows are DATA, not execution. They define the SHAPE of a pipeline
(steps, order, conditional edges) without importing any framework.

The service layer (LIVELLO 2) reads these declarations and builds the
actual LangGraph/sequential execution. Core never imports LangGraph.

Extracted from:
  - confessor_agent.py: setup_workflow() — 9-step LangGraph pipeline

Sacred Order: Truth & Governance
Layer: Foundational (governance)
"""

from dataclasses import dataclass
from typing import Optional


# =============================================================================
# WorkflowStep — A single step in the pipeline
# =============================================================================

@dataclass(frozen=True)
class WorkflowStep:
    """
    Declarative step in an audit workflow.

    Each step has a name, a role (which SacredRole processes it),
    and optional conditional routing.

    Attributes:
        name: Unique step identifier
        role: SacredRole name that handles this step (e.g., "classifier")
        description: What this step does
        next_step: Default next step name (None = END)
        conditional: Optional routing rules as tuple of (condition, target)
            - condition is a string the service layer interprets
            - target is the next step name
    """

    name: str
    role: str
    description: str
    next_step: Optional[str] = None
    conditional: Optional[tuple] = None  # Tuple[(condition_str, target_step), ...]


# =============================================================================
# Workflow — Ordered collection of steps
# =============================================================================

@dataclass(frozen=True)
class Workflow:
    """
    Declarative workflow definition.

    A Workflow is a frozen, ordered sequence of WorkflowSteps
    that describes an audit pipeline. It does NOT execute — the
    service layer reads this definition and builds the execution graph.

    Attributes:
        workflow_id: Unique identifier (e.g., "orthodoxy.full_audit")
        version: Version string
        description: Human-readable description
        entry_step: Name of the first step
        steps: Ordered tuple of WorkflowStep objects
    """

    workflow_id: str
    version: str
    description: str
    entry_step: str
    steps: tuple  # Tuple[WorkflowStep, ...]

    @property
    def step_names(self) -> tuple:
        """All step names in order."""
        return tuple(s.name for s in self.steps)

    def get_step(self, name: str) -> Optional[WorkflowStep]:
        """Lookup step by name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def validate(self) -> tuple:
        """
        Validate workflow internal consistency.

        Returns:
            Tuple of error strings. Empty = valid.
        """
        errors = []
        names = set(s.name for s in self.steps)

        # Entry step must exist
        if self.entry_step not in names:
            errors.append(
                f"Entry step '{self.entry_step}' "
                f"not found in steps: {names}"
            )

        # All next_step references must be valid
        for step in self.steps:
            if step.next_step and step.next_step not in names:
                errors.append(
                    f"Step '{step.name}' references unknown "
                    f"next_step '{step.next_step}'"
                )

            if step.conditional:
                for condition, target in step.conditional:
                    if target not in names and target != "END":
                        errors.append(
                            f"Step '{step.name}' conditional "
                            f"references unknown target '{target}'"
                        )

        return tuple(errors)


# =============================================================================
# DEFAULT WORKFLOWS — Extracted from confessor_agent.setup_workflow()
# =============================================================================

# ─────────────────────────────────────────────────────────────
# 1. Full Audit Workflow (from confessor_agent 9-step pipeline)
# ─────────────────────────────────────────────────────────────
# Original LangGraph pipeline:
#   trigger_analysis → code_analysis → system_monitoring →
#   compliance_check → decision_engine →
#   [auto_correction | system_healing | notification_dispatch] →
#   learning_update → END
#
# Mapped to Sacred Order roles:
#   - trigger_analysis → "intake" (receives Confession)
#   - code_analysis → "classifier" (PatternClassifier + ASTClassifier)
#   - compliance_check → "classifier" (focused on compliance category)
#   - decision_engine → "verdict_engine" (renders Verdict)
#   - auto_correction → "penitent" (service layer executes)
#   - system_healing → "penitent" (service layer executes)
#   - notification_dispatch → "herald" (service layer publishes)
#   - learning_update → "chronicler" (LogDecision)
#   - system_monitoring → REMOVED (was _legacy.chronicler/SystemMonitor)

FULL_AUDIT_WORKFLOW = Workflow(
    workflow_id="orthodoxy.full_audit",
    version="v2.0",
    description=(
        "Complete audit pipeline. Receives a Confession, classifies "
        "content against RuleSet, renders Verdict, decides on corrective "
        "action, and emits events. Extracted from confessor_agent.py "
        "9-step LangGraph pipeline (Feb 2026 refactoring)."
    ),
    entry_step="intake",
    steps=(
        WorkflowStep(
            name="intake",
            role="intake",
            description="Receive and validate incoming Confession",
            next_step="classify",
        ),
        WorkflowStep(
            name="classify",
            role="classifier",
            description=(
                "Run PatternClassifier (regex) + ASTClassifier (if code) "
                "against active RuleSet. Produces tuple[Finding, ...]"
            ),
            next_step="judge",
        ),
        WorkflowStep(
            name="judge",
            role="verdict_engine",
            description=(
                "VerdictEngine renders Verdict from Findings. "
                "Determines status (blessed/purified/heretical/non_liquet)"
            ),
            next_step="decide_action",
        ),
        WorkflowStep(
            name="decide_action",
            role="verdict_engine",
            description=(
                "Route based on verdict status. "
                "Critical → correction. Warning → notification. Clean → log."
            ),
            conditional=(
                ("verdict.status == 'heretical'", "correction"),
                ("verdict.status == 'purified'", "notification"),
                ("verdict.status == 'blessed'", "log"),
                ("verdict.status == 'non_liquet'", "notification"),
            ),
        ),
        WorkflowStep(
            name="correction",
            role="penitent",
            description=(
                "Request corrective action for heretical content. "
                "Service layer handles actual execution."
            ),
            next_step="notification",
        ),
        WorkflowStep(
            name="notification",
            role="herald",
            description=(
                "Emit events to Cognitive Bus. "
                "Service layer publishes via StreamBus."
            ),
            next_step="log",
        ),
        WorkflowStep(
            name="log",
            role="chronicler",
            description=(
                "Decide logging strategy via LogDecision. "
                "Service layer persists to PostgreSQL/Qdrant."
            ),
            next_step=None,  # END
        ),
    ),
)


# ─────────────────────────────────────────────────────────────
# 2. Quick Validation Workflow (lightweight — LLM output check)
# ─────────────────────────────────────────────────────────────
# For CAN node / MCP anti-hallucination validation
# Skips intake ceremony and correction — just classify + judge + log

QUICK_VALIDATION_WORKFLOW = Workflow(
    workflow_id="orthodoxy.quick_validation",
    version="v1.0",
    description=(
        "Lightweight validation for LLM output checking. "
        "Classify → Judge → Log. No correction step. "
        "Used by CAN node and MCP anti-hallucination (Phase 4.1)."
    ),
    entry_step="classify",
    steps=(
        WorkflowStep(
            name="classify",
            role="classifier",
            description="Run PatternClassifier against compliance + hallucination rules",
            next_step="judge",
        ),
        WorkflowStep(
            name="judge",
            role="verdict_engine",
            description="Render Verdict from Findings",
            next_step="log",
        ),
        WorkflowStep(
            name="log",
            role="chronicler",
            description="Decide logging via LogDecision",
            next_step=None,  # END
        ),
    ),
)


# ─────────────────────────────────────────────────────────────
# Registry of all available workflows
# ─────────────────────────────────────────────────────────────

AVAILABLE_WORKFLOWS: dict = {
    "orthodoxy.full_audit": FULL_AUDIT_WORKFLOW,
    "orthodoxy.quick_validation": QUICK_VALIDATION_WORKFLOW,
}
