/**
 * CHART CARD COMPONENT
 * Standardized container for Recharts components
 * Replaces inline chart card patterns across nodes
 * 
 * @component ChartCard
 * @created Dec 11, 2025
 * @usage Wrap ResponsiveContainer with ChartCard for consistent styling
 */

'use client'
import BaseCard from './BaseCard'

export default function ChartCard({ 
  title,
  subtitle,
  children,
  tooltip,
  headerAction,
  className = ''
}) {
  return (
    <BaseCard variant="elevated" padding="lg" className={className}>
      {(title || subtitle || headerAction) && (
        <div className="flex items-start justify-between mb-4">
          <div>
            {title && (
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {subtitle}
              </p>
            )}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      <div className="w-full">
        {children}
      </div>
    </BaseCard>
  )
}
