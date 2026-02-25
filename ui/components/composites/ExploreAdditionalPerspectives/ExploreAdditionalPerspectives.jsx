// composites/ExploreAdditionalPerspectives/ExploreAdditionalPerspectives.jsx
// UX Constitution compliant - Jan 2, 2026
//
// ARCHITECTURE DECISION (BINDING):
// - TYPE: Composite UI Template
// - LEVEL: Shared library
// - STATUS: Reusable by ANY adapter (single, comparison, allocation, risk-only)
//
// EPISTEMIC ROLE (DO NOT CHANGE):
// - Shows same asset under DIFFERENT LENSES (without changing the question)
// - Does NOT introduce new signals
// - Does NOT generate conclusions
// - Does NOT precede narrative
// - Is an EXPLORATION TOOL, not a decision tool
//
// DESIGN RULES:
// - AGNOSTIC: Does NOT know context (single, comparison, etc.)
// - PASSIVE: Does NOT assume what to show
// - PURE: Does NOT import data — receives configuration + child components
// - LAZY: Items render only when expanded
//
// USAGE:
// <ExploreAdditionalPerspectives
//   items={[
//     { id: "factor_breakdown", label: "Factor Breakdown", description: "...", component: <FactorRadar /> },
//     { id: "risk_profile", label: "Risk Profile", description: "...", component: <RiskChart /> }
//   ]}
// />

'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Eye, Layers } from 'lucide-react'

/**
 * ExploreAdditionalPerspectives - Cognitive exploration composite
 * 
 * @param {Array} items - Array of perspective items
 * @param {string} items[].id - Unique identifier
 * @param {string} items[].label - Display label
 * @param {string} items[].description - Brief description of what this perspective shows
 * @param {ReactNode} items[].component - The visualization component to render
 * @param {string} items[].icon - Optional lucide icon name
 * @param {number} maxVisible - Maximum perspectives to show (default: 3)
 * @param {string} title - Section title (default: "Explore Additional Perspectives")
 */
export function ExploreAdditionalPerspectives({ 
  items = [], 
  maxVisible = 3,
  title = "Explore Additional Perspectives",
  defaultExpanded = null // id of item to expand by default, or null for all collapsed
}) {
  const [expandedId, setExpandedId] = useState(defaultExpanded)

  // RULE: Do not render if no items
  if (!items || items.length === 0) {
    return null
  }

  // Limit visible items
  const visibleItems = items.slice(0, maxVisible)

  const toggleItem = (id) => {
    setExpandedId(prev => prev === id ? null : id)
  }

  return (
    <div className="mt-4">
      {/* Section header */}
      <div className="flex items-center gap-2 mb-3">
        <Layers size={14} className="text-slate-400" />
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
          {title}
        </span>
        <span className="text-[10px] text-slate-400">
          ({visibleItems.length} available)
        </span>
      </div>

      {/* Perspective items */}
      <div className="space-y-2">
        {visibleItems.map((item) => (
          <PerspectiveItem
            key={item.id}
            item={item}
            isExpanded={expandedId === item.id}
            onToggle={() => toggleItem(item.id)}
          />
        ))}
      </div>

      {/* Show more indicator if items truncated */}
      {items.length > maxVisible && (
        <div className="mt-2 text-center">
          <span className="text-xs text-slate-400">
            +{items.length - maxVisible} more perspectives available
          </span>
        </div>
      )}
    </div>
  )
}

/**
 * PerspectiveItem - Individual expandable perspective
 */
function PerspectiveItem({ item, isExpanded, onToggle }) {
  const { id, label, description, component } = item

  return (
    <div 
      className={`
        border rounded-lg overflow-hidden transition-all duration-200
        ${isExpanded 
          ? 'border-indigo-200 bg-indigo-50/30' 
          : 'border-gray-200 bg-white hover:border-gray-300'
        }
      `}
    >
      {/* Clickable header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 p-3 text-left focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:ring-inset"
        aria-expanded={isExpanded}
        aria-controls={`perspective-${id}`}
      >
        {/* Expand/collapse icon */}
        <div className={`
          flex-shrink-0 w-5 h-5 rounded flex items-center justify-center
          ${isExpanded ? 'bg-indigo-100 text-indigo-600' : 'bg-gray-100 text-gray-500'}
        `}>
          {isExpanded 
            ? <ChevronDown size={14} /> 
            : <ChevronRight size={14} />
          }
        </div>

        {/* Label and description */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <Eye size={12} className="text-slate-400 flex-shrink-0" />
            <span className={`text-sm font-medium truncate ${isExpanded ? 'text-indigo-700' : 'text-gray-700'}`}>
              {label}
            </span>
          </div>
          {description && !isExpanded && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">
              {description}
            </p>
          )}
        </div>
      </button>

      {/* Expandable content */}
      {isExpanded && (
        <div 
          id={`perspective-${id}`}
          className="px-3 pb-3 pt-1 border-t border-indigo-100"
        >
          {/* Description when expanded */}
          {description && (
            <p className="text-xs text-slate-600 mb-3 leading-relaxed">
              {description}
            </p>
          )}
          
          {/* The actual visualization component */}
          <div className="bg-white rounded-lg border border-gray-100 p-3">
            {component}
          </div>
        </div>
      )}
    </div>
  )
}

export default ExploreAdditionalPerspectives
