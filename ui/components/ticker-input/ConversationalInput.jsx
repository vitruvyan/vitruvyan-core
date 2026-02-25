"use client"

import { forwardRef } from "react"

// Pure text input component - NO ticker logic
const ConversationalInput = forwardRef(({
  inputValue,
  onInputChange,
  confirmedTickers,
  ...props
}, ref) => {
  // Get CSS class for input based on confirmed tickers
  const getInputClassName = () => {
    const baseClass = "w-full rounded-md border bg-gray-50 p-3 sm:p-4 pl-10 sm:pl-12 pr-10 sm:pr-12 focus:outline-none focus:ring-2 transition-all"
    if (confirmedTickers.length > 0) {
      return baseClass + " border-vitruvyan-accent ring-1 ring-vitruvyan-accent/30 focus:border-vitruvyan-accent focus:ring-vitruvyan-accent"
    }
    return baseClass + " border-gray-300 focus:border-vitruvyan-accent focus:ring-vitruvyan-accent"
  }

  return (
    <input
      ref={ref}
      type="text"
      value={inputValue}
      onChange={(e) => onInputChange(e.target.value)}
      placeholder="Insert a ticker or start a conversation"
      className={getInputClassName()}
      {...props}
    />
  )
})

ConversationalInput.displayName = "ConversationalInput"

export default ConversationalInput