'use client'

import { HelpCircle, X } from 'lucide-react'
import { useTooltips } from '@/contexts/TooltipContext'

/**
 * TOOLTIP TOGGLE BUTTON
 * 
 * Global toggle for enabling/disabling explainability tooltips.
 * State persists in localStorage.
 * 
 * Placement: Top-right of chat interface or neural engine section.
 */

export default function TooltipToggle() {
  const { tooltipsEnabled, toggleTooltips } = useTooltips()

  return (
    <button
      onClick={toggleTooltips}
      className={`
        inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium
        transition-all duration-200 border-2
        ${tooltipsEnabled 
          ? 'bg-vitruvyan-primary text-white border-vitruvyan-primary hover:bg-vitruvyan-primary-dark' 
          : 'bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200'
        }
      `}
      title={tooltipsEnabled ? 'Disable explainability tooltips' : 'Enable explainability tooltips'}
    >
      {tooltipsEnabled ? (
        <>
          <HelpCircle className="w-3.5 h-3.5" />
          <span>Tooltips ON</span>
        </>
      ) : (
        <>
          <X className="w-3.5 h-3.5" />
          <span>Tooltips OFF</span>
        </>
      )}
    </button>
  )
}
