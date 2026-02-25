'use client'

import { createContext, useContext, useState, useEffect } from 'react'

const TooltipContext = createContext()

export function TooltipProvider({ children }) {
  const [tooltipsEnabled, setTooltipsEnabled] = useState(true)

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('vitruvyan_tooltips_enabled')
    if (saved !== null) {
      setTooltipsEnabled(saved === 'true')
    }
  }, [])

  // Save to localStorage on change
  const toggleTooltips = () => {
    setTooltipsEnabled(prev => {
      const newValue = !prev
      localStorage.setItem('vitruvyan_tooltips_enabled', String(newValue))
      return newValue
    })
  }

  return (
    <TooltipContext.Provider value={{ tooltipsEnabled, toggleTooltips }}>
      {children}
    </TooltipContext.Provider>
  )
}

export function useTooltips() {
  const context = useContext(TooltipContext)
  if (!context) {
    throw new Error('useTooltips must be used within TooltipProvider')
  }
  return context
}
