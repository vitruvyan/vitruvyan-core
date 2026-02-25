/**
 * @deprecated This component is deprecated.
 * Use the replacement indicated below.
 * Will be removed in v2.0
 *
 * FundamentalsDisplay → analytics/panels/FundamentalsPanel
 * MetricDisplay → cards/MetricCard
 * RiskDisplay → analytics/panels/RiskPanel
 */

// composites/MetricDisplay.jsx
'use client'

export function MetricDisplay({ label, value, format = 'zscore' }) {
  const formattedValue = format === 'zscore'
    ? (value?.toFixed(2) || '-')
    : value

  const colorClass = getZScoreColor(value)

  return (
    <div className={`p-2 rounded-lg border ${colorClass}`}>
      <div className="text-xs text-gray-500">{label}</div>
      <div className="font-mono font-medium">{formattedValue}</div>
    </div>
  )
}

function getZScoreColor(z) {
  if (z === null || z === undefined) return 'bg-gray-50 border-gray-200'
  if (z > 1.0) return 'bg-green-50 border-green-200 text-green-900'
  if (z > 0.5) return 'bg-emerald-50 border-emerald-200 text-emerald-900'
  if (z > -0.5) return 'bg-blue-50 border-blue-200 text-blue-900'
  if (z > -1.0) return 'bg-orange-50 border-orange-200 text-orange-900'
  return 'bg-red-50 border-red-200 text-red-900'
}