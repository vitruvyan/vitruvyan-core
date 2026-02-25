/**
 * Test script for buildComparisonStateFromMatrix utility
 * Run with: node test_comparison_state_builder.js
 * 
 * Purpose: Verify frontend can build comparison_state from comparison_matrix + numerical_panel
 */

// Mock data from real "confronta MCD SBUX" response
const comparisonMatrix = {
  "winner": "MCD",
  "loser": "SBUX",
  "range_pct": 20.59,
  "deltas": {
    "momentum_z": 0.5,
    "trend_z": 0.3,
    "sentiment_z": 0.1
  }
}

const numericalPanel = [
  {
    "ticker": "MCD",
    "composite_score": 0.45,
    "momentum_z": 0.6,
    "trend_z": 0.4,
    "sentiment_z": 0.3,
    "vola_z": 0.5
  },
  {
    "ticker": "SBUX",
    "composite_score": 0.24,
    "momentum_z": 0.1,
    "trend_z": 0.1,
    "sentiment_z": 0.2,
    "vola_z": 0.6
  }
]

// 🟣 FASE 2: Build comparison_state from comparison_matrix + numerical_panel when backend doesn't populate it (Dec 10, 2025)
function buildComparisonStateFromMatrix(comparisonMatrix, numericalPanel) {
  if (!comparisonMatrix || !numericalPanel || numericalPanel.length < 2) {
    return null
  }

  // Extract ranking_order (sort by composite_score)
  const ranking_order = [...numericalPanel]
    .sort((a, b) => (b.composite_score || 0) - (a.composite_score || 0))
    .map(item => item.ticker)

  // Extract winner_by_factor (max z-score per factor)
  const winner_by_factor = {}
  const factors = ['momentum_z', 'trend_z', 'sentiment_z', 'vola_z']
  factors.forEach(factor => {
    const winner = numericalPanel.reduce((max, item) => 
      (item[factor] || -999) > (max[factor] || -999) ? item : max
    )
    if (winner && winner.ticker) {
      winner_by_factor[factor] = winner.ticker
    }
  })

  // Extract factor_deltas from comparison_matrix or compute
  const factor_deltas = comparisonMatrix.deltas || {}
  
  // Extract range and range_pct
  const range = comparisonMatrix.range || (comparisonMatrix.range_pct / 100) || 0
  const range_pct = comparisonMatrix.range_pct || 0

  return {
    ranking_order,
    winner_by_factor,
    factor_deltas,
    range,
    range_pct,
    num_tickers: numericalPanel.length,
    timestamp: new Date().toISOString()
  }
}

// Test
console.log('🧪 Testing buildComparisonStateFromMatrix...\n')
console.log('Input:')
console.log('  comparisonMatrix:', JSON.stringify(comparisonMatrix, null, 2))
console.log('  numericalPanel:', JSON.stringify(numericalPanel, null, 2))
console.log('\n')

const result = buildComparisonStateFromMatrix(comparisonMatrix, numericalPanel)

console.log('Output:')
console.log(JSON.stringify(result, null, 2))
console.log('\n')

// Validation
const tests = [
  {
    name: 'ranking_order present',
    pass: result.ranking_order && result.ranking_order.length === 2,
    expected: ['MCD', 'SBUX'],
    actual: result.ranking_order
  },
  {
    name: 'ranking_order correct',
    pass: result.ranking_order[0] === 'MCD' && result.ranking_order[1] === 'SBUX',
    expected: 'MCD first (higher composite_score)',
    actual: result.ranking_order.join(', ')
  },
  {
    name: 'winner_by_factor present',
    pass: result.winner_by_factor && Object.keys(result.winner_by_factor).length === 4,
    expected: '4 factors (momentum_z, trend_z, sentiment_z, vola_z)',
    actual: `${Object.keys(result.winner_by_factor).length} factors`
  },
  {
    name: 'winner_by_factor.momentum_z correct',
    pass: result.winner_by_factor.momentum_z === 'MCD',
    expected: 'MCD (0.6 > 0.1)',
    actual: result.winner_by_factor.momentum_z
  },
  {
    name: 'winner_by_factor.vola_z correct',
    pass: result.winner_by_factor.vola_z === 'SBUX',
    expected: 'SBUX (0.6 > 0.5)',
    actual: result.winner_by_factor.vola_z
  },
  {
    name: 'factor_deltas present',
    pass: result.factor_deltas && Object.keys(result.factor_deltas).length > 0,
    expected: 'at least 1 delta',
    actual: `${Object.keys(result.factor_deltas).length} deltas`
  },
  {
    name: 'range_pct correct',
    pass: result.range_pct === 20.59,
    expected: 20.59,
    actual: result.range_pct
  },
  {
    name: 'num_tickers correct',
    pass: result.num_tickers === 2,
    expected: 2,
    actual: result.num_tickers
  }
]

console.log('Validation Results:')
tests.forEach(test => {
  const status = test.pass ? '✅' : '❌'
  console.log(`${status} ${test.name}`)
  if (!test.pass) {
    console.log(`   Expected: ${test.expected}`)
    console.log(`   Actual: ${test.actual}`)
  }
})

const passed = tests.filter(t => t.pass).length
const total = tests.length
console.log(`\n${passed}/${total} tests passed`)

if (passed === total) {
  console.log('✅ All tests passed! Frontend logic ready.')
  process.exit(0)
} else {
  console.log('❌ Some tests failed. Fix before deployment.')
  process.exit(1)
}
