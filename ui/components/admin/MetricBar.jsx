"use client"

/**
 * Metric Bar Component
 * 
 * Horizontal bar for visualizing metric progress (0.0-1.0).
 * Used in health dashboard for stability, success rate, coverage metrics.
 * 
 * Phase 2: Admin UI Shell (Jan 27, 2026)
 */
export default function MetricBar({ 
  label, 
  value, 
  maxValue = 1.0,
  showPercentage = true,
  colorScheme = "cyan" // cyan | green | yellow | red
}) {
  // Normalize value to 0-1 range
  const normalizedValue = Math.max(0, Math.min(1, value / maxValue))
  const percentage = Math.round(normalizedValue * 100)
  
  // Color schemes
  const colors = {
    cyan: "bg-cyan-500",
    green: "bg-emerald-500",
    yellow: "bg-yellow-500",
    red: "bg-red-500"
  }
  
  const bgColor = colors[colorScheme] || colors.cyan
  
  return (
    <div className="space-y-2">
      {/* Label and percentage */}
      <div className="flex items-center justify-between">
        <span className="font-mono text-sm text-slate-400">{label}</span>
        {showPercentage && (
          <span className="font-mono text-sm font-semibold text-slate-300">
            {percentage}%
          </span>
        )}
      </div>
      
      {/* Progress bar */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full transition-all duration-500 ${bgColor}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
