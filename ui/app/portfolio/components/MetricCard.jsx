/**
 * MetricCard - Reusable Portfolio Metric Display
 * 
 * Extracted from page.jsx for reusability across adapters
 */

export function MetricCard({ icon, label, value, subtext, colorClass }) {
  return (
    <div className={`${colorClass} border rounded-lg p-4`}>
      <div className="flex items-center gap-3 mb-2">
        {icon}
        <span className="text-sm font-medium text-gray-700">{label}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-600 mt-1">{subtext}</p>
    </div>
  )
}
