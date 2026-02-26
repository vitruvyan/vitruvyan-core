"""
DSE Redis Stream Channel Constants
====================================

Naming convention: <service>.<domain>.<action>
All constants are strings — no infrastructure imports.

Channels DSE PRODUCES:
  dse.sampling.completed       — design points generated, strategy decided
  dse.governance.requested     — request Conclave approval before run
  dse.strategy.decided         — ML/heuristic decision logged
  dse.run.completed            — full RunArtifact ready
  vault.archive.requested      — ask Vault to persist artifact (downstream)

Channels DSE CONSUMES (via streams_listener):
  pattern_weavers.weave.completed    — trigger prepare_dse
  conclave.governance.approved       — trigger run_dse
  conclave.governance.rejected       — log rejection, no run
  orthodoxy.policy.validated         — Phase 2+ policy enforcement
  vault.restore.completed            — re-run with restored design points

Last updated: Feb 26, 2026
"""


class DSEChannels:
    """Canonical Redis Stream channel names for the DSE service."""

    # --- Produced by DSE ---
    SAMPLING_COMPLETED = "dse.sampling.completed"
    GOVERNANCE_REQUESTED = "dse.governance.requested"
    STRATEGY_DECIDED = "dse.strategy.decided"
    RUN_COMPLETED = "dse.run.completed"
    VAULT_ARCHIVE_REQUESTED = "vault.archive.requested"

    # --- Consumed from upstream Sacred Orders ---
    WEAVE_COMPLETED = "pattern_weavers.weave.completed"
    GOVERNANCE_APPROVED = "conclave.governance.approved"
    GOVERNANCE_REJECTED = "conclave.governance.rejected"
    POLICY_VALIDATED = "orthodoxy.policy.validated"
    RESTORE_COMPLETED = "vault.restore.completed"

    # --- All subscribed channels (for listener bootstrap) ---
    SUBSCRIBED: tuple = (
        WEAVE_COMPLETED,
        GOVERNANCE_APPROVED,
        GOVERNANCE_REJECTED,
        POLICY_VALIDATED,
        RESTORE_COMPLETED,
    )
