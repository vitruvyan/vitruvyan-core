/**
 * VEE BADGE COMPONENT
 * 
 * Mini-badge displaying VEE simple explanation for chart axes/labels.
 * Used in Radar chart for factor explanations.
 * 
 * Props:
 * - text: VEE simple explanation text
 * - className: Additional CSS classes
 */

'use client'

export default function VeeBadge({ text, className = '' }) {
  if (!text) return null

  // Truncate if too long (max 60 chars)
  const displayText = text.length > 60 ? `${text.substring(0, 57)}...` : text

  return (
    <div className={`inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 border border-blue-200 rounded text-[10px] text-blue-700 font-medium ${className}`}>
      <span className="text-blue-500">ℹ️</span>
      <span>{displayText}</span>
    </div>
  )
}
