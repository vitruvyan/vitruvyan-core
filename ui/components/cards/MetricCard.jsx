/**
 * METRIC CARD COMPONENT
 * Display metrics with color-coded backgrounds
 * Enhanced version of components/common/MetricCard.jsx
 * 
 * @component MetricCard
 * @created Dec 11, 2025
 * @migration Replaces components/common/MetricCard.jsx
 * @changes Uses DarkTooltip from TooltipLibrary (not InfoTooltip)
 */

'use client'
import { DarkTooltip } from '@/components/explainability/tooltips/TooltipLibrary'
import { tokens } from '../theme/tokens'

export default function MetricCard({ 
  label, 
  value, 
  color = 'blue',  // blue | purple | green | orange | red | gray | yellow | indigo
  tooltip,
  subtitle,
  icon: Icon,
  className = '' 
}) {
  const colorClass = tokens.colors.metricColors[color] || tokens.colors.metricColors.blue
  
  return (
    <div className={`${colorClass} border rounded-lg p-3 transition-all hover:shadow-md ${className}`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="w-4 h-4" />}
          <div className="text-xs font-medium">{label}</div>
        </div>
        {tooltip && <DarkTooltip content={tooltip} />}
      </div>
      <div className="text-lg font-bold">{value}</div>
      {subtitle && (
        <div className="text-xs opacity-75 mt-1">{subtitle}</div>
      )}
    </div>
  )
}
