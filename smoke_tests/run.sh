#!/bin/bash
# Mercator Finance Vertical — Smoke Tests
# Contract: docs/contracts/platform/UPDATE_SYSTEM_CONTRACT_V1.md
# Exit codes: 0=pass, 1=fail, 2=cannot run
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/vitruvyan_core:${REPO_ROOT}:${PYTHONPATH}"

PASS=0
FAIL=0

run_test() {
    local name="$1"
    shift
    if "$@" 2>&1; then
        echo "  ✅ $name"
        ((PASS++)) || true
    else
        echo "  ❌ $name"
        ((FAIL++)) || true
    fi
}

echo "🔍 Mercator Finance — Smoke Tests"
echo "   Repo: ${REPO_ROOT}"
echo ""

# ── 1. Core imports ──
echo "📦 Core imports:"
run_test "PostgresAgent" python3 -c "from core.agents.postgres_agent import PostgresAgent"
run_test "QdrantAgent" python3 -c "from core.agents.qdrant_agent import QdrantAgent"
run_test "StreamBus" python3 -c "from core.synaptic_conclave.transport.streams import StreamBus"
run_test "LLMAgent" python3 -c "from core.agents.llm_agent import get_llm_agent"

# ── 2. Contracts namespace ──
echo ""
echo "📋 Contracts:"
run_test "contracts package" python3 -c "import vitruvyan_core.contracts"

# ── 3. Finance domain ──
echo ""
echo "💰 Finance domain:"
run_test "intent_config" python3 -c "from vitruvyan_core.domains.finance.intent_config import create_finance_registry"
run_test "graph_plugin" python3 -c "from vitruvyan_core.domains.finance.graph_plugin import FinanceGraphPlugin"

# ── 4. Synaptic Conclave (bus) ──
echo ""
echo "🧠 Synaptic Conclave:"
run_test "EventEnvelope" python3 -c "from core.synaptic_conclave.events.event_envelope import TransportEvent, CognitiveEvent"
run_test "BaseConsumer" python3 -c "from core.synaptic_conclave.consumers.base_consumer import BaseConsumer"

# ── Summary ──
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$FAIL" -gt 0 ]; then
    echo "❌ Smoke tests FAILED"
    exit 1
fi

echo "✅ All smoke tests passed"
exit 0
