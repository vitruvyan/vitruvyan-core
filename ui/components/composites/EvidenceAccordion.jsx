// composites/EvidenceAccordion.jsx
// UX Constitution compliant - Jan 2, 2026
// Renders evidence sections with micro-badges visible when collapsed

'use client'

import { useState } from 'react'
import { ChevronRight, ChevronDown } from 'lucide-react'
import { EvidenceSectionRenderer } from '../response/EvidenceSectionRenderer'

// Micro-badge color mapping per UX Constitution Art. XV
const BADGE_COLORS = {
  green: 'bg-green-100 text-green-700',
  amber: 'bg-amber-100 text-amber-700',
  red: 'bg-red-100 text-red-700',
  gray: 'bg-gray-100 text-gray-600'
}

export function EvidenceAccordion({ sections }) {
  if (!sections?.length) return null
  
  // Sort by priority, first one expanded by default
  const sortedSections = [...sections].sort((a, b) => a.priority - b.priority)

  const [expandedIds, setExpandedIds] = useState(() => {
    const defaultExpanded = sortedSections.filter(s => s.defaultExpanded)
    return defaultExpanded.map(s => s.id)
  })

  const toggleSection = (id) => {
    setExpandedIds(prev =>
      prev.includes(id)
        ? prev.filter(x => x !== id)
        : [...prev, id]
    )
  }

  return (
    <div className="space-y-2">
      {sortedSections.map(section => {
        const isExpanded = expandedIds.includes(section.id)
        const badge = section.microBadge

        return (
          <div key={section.id} className="border border-gray-200 rounded-lg bg-white">
            <button
              onClick={() => toggleSection(section.id)}
              className="w-full flex items-center gap-2 p-3 text-left hover:bg-gray-50 transition-colors"
            >
              {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              <span className="font-medium text-sm">{section.title}</span>
              
              {/* Micro-badge (visible when collapsed) - UX Constitution Art. XV */}
              {badge && !isExpanded && (
                <span className={`ml-auto text-xs font-medium px-2 py-0.5 rounded-full ${BADGE_COLORS[badge.color] || BADGE_COLORS.gray}`}>
                  {badge.label}
                </span>
              )}
              
              {!badge && (
                <span className="ml-auto" />
              )}
            </button>

            {isExpanded && (
              <div className="px-3 pb-3">
                <EvidenceSectionRenderer section={section} />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}