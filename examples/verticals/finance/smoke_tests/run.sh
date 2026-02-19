#!/bin/bash
# =============================================================================
# Finance Vertical - Smoke Tests
# =============================================================================
# Contract: UPDATE_SYSTEM_CONTRACT_V1 (Section 2)
# Exit codes: 0=pass, 1=fail, 2=error
# Timeout: 180 seconds (manifest.compatibility.smoke_tests_timeout)
# =============================================================================

set -e  # Exit on first error

echo "🧪 Running Finance Vertical Smoke Tests..."
echo ""

# Test 1: Core imports work
echo "Test 1/5: Core imports..."
python3 -c "
from core.agents.postgres_agent import PostgresAgent
from core.agents.qdrant_agent import QdrantAgent
from core.agents.llm_agent import get_llm_agent
print('  ✅ Core agents importable')
" || { echo "  ❌ Core agents import failed"; exit 1; }

# Test 2: Contracts available
echo "Test 2/5: Contracts..."
python3 -c "
from contracts import GraphPlugin, BaseParser
print('  ✅ Contracts importable')
" || { echo "  ❌ Contracts import failed"; exit 1; }

# Test 3: Finance vertical modules
echo "Test 3/5: Finance modules..."
python3 -c "
import sys
sys.path.insert(0, '$(dirname $0)/..')
from config.intent_config import create_finance_registry
print('  ✅ Finance modules importable')
" || { echo "  ❌ Finance modules import failed"; exit 1; }

# Test 4: Database connectivity (if available)
echo "Test 4/5: Database connectivity..."
python3 -c "
from core.agents.postgres_agent import PostgresAgent
try:
    pg = PostgresAgent()
    result = pg.fetch_query('SELECT 1 AS ok')
    if result and result[0]['ok'] == 1:
        print('  ✅ PostgreSQL reachable')
    else:
        print('  ⚠️  PostgreSQL query failed (non-critical)')
except Exception as e:
    print(f'  ⚠️  PostgreSQL unreachable (non-critical): {e}')
" || echo "  ⚠️  Database test skipped (optional)"

# Test 5: LLM agent availability
echo "Test 5/5: LLM agent..."
python3 -c "
from core.agents.llm_agent import get_llm_agent
llm = get_llm_agent()
print(f'  ✅ LLM agent available (model: {llm.default_model})')
" ||{ echo "  ❌ LLM agent import failed"; exit 1; }

echo ""
echo "✅ All smoke tests passed!"
echo "Duration: ${SECONDS}s"
exit 0
