/**
 * ACCORDION CARD COMPONENT
 * Collapsible card for sections
 * Replaces inline accordion patterns in ComparisonNodeUI, ScreeningNodeUI
 * 
 * @component AccordionCard
 * @created Dec 11, 2025
 * @features
 *   - Collapsible content with smooth transitions
 *   - Dark mode support
 *   - Keyboard accessible (Enter/Space to toggle)
 */

'use client'
import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import BaseCard from './BaseCard'

export default function AccordionCard({ 
  title,
  subtitle,
  children,
  defaultOpen = false,
  className = ''
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  const handleToggle = () => {
    setIsOpen(!isOpen)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleToggle()
    }
  }

  return (
    <BaseCard variant="elevated" padding="none" className={className}>
      <button
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors text-left"
        aria-expanded={isOpen}
        aria-controls={`accordion-content-${title}`}
      >
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            {title}
          </h3>
          {subtitle && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {subtitle}
            </p>
          )}
        </div>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0 ml-2" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0 ml-2" />
        )}
      </button>
      
      {isOpen && (
        <div 
          id={`accordion-content-${title}`}
          className="p-4 border-t border-gray-200 dark:border-gray-700"
        >
          {children}
        </div>
      )}
    </BaseCard>
  )
}
