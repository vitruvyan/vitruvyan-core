"use client"

/**
 * Health Gauge Component
 * 
 * Circular gauge for visualizing health scores (0.0-1.0).
 * Color-coded based on health level:
 * - Green (healthy): >= 0.8
 * - Yellow (degraded): 0.5-0.8
 * - Red (critical): < 0.5
 * 
 * Phase 2: Admin UI Shell (Jan 27, 2026)
 */
export default function HealthGauge({ 
  score, 
  label, 
  size = 120,
  showPercentage = true 
}) {
  // Normalize score to 0-1 range
  const normalizedScore = Math.max(0, Math.min(1, score))
  const percentage = Math.round(normalizedScore * 100)
  
  // Determine health level and color
  const getHealthLevel = (score) => {
    if (score >= 0.8) return { level: "HEALTHY", color: "text-emerald-400", stroke: "#34d399" }
    if (score >= 0.5) return { level: "DEGRADED", color: "text-yellow-400", stroke: "#fbbf24" }
    return { level: "CRITICAL", color: "text-red-400", stroke: "#f87171" }
  }
  
  const { level, color, stroke } = getHealthLevel(normalizedScore)
  
  // SVG circle calculations
  const radius = (size - 16) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (normalizedScore * circumference)
  
  return (
    <div className="flex flex-col items-center">
      {/* Circular gauge */}
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="rotate-[-90deg]">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#1e293b"
            strokeWidth="8"
            fill="none"
          />
          
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={stroke}
            strokeWidth="8"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {showPercentage && (
            <span className={`font-mono text-2xl font-bold ${color}`}>
              {percentage}%
            </span>
          )}
        </div>
      </div>
      
      {/* Label */}
      <div className="mt-3 text-center">
        <p className="font-mono text-xs font-semibold uppercase tracking-wider text-slate-500">
          {label}
        </p>
        <p className={`mt-1 font-mono text-sm font-bold ${color}`}>
          {level}
        </p>
      </div>
    </div>
  )
}
