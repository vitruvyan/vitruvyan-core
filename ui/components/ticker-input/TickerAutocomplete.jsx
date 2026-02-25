"use client"

import { useState, useEffect, useRef } from "react"
import { TrendingUp } from "lucide-react"

// Autocomplete dropdown - EXPLICIT CONFIRMATION ONLY
export default function TickerAutocomplete({
  inputValue,
  onTickerConfirmed,
  searchTickers,
  inputRef
}) {
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [focusedSuggestion, setFocusedSuggestion] = useState(-1)
  const [apiSuggestions, setApiSuggestions] = useState([])
  const [justSelected, setJustSelected] = useState(false)  // Prevent dropdown reopen after selection

  const suggestionsRef = useRef(null)

  useEffect(() => {
    // ✅ Don't reopen dropdown if user just selected a ticker
    if (justSelected) {
      setJustSelected(false)
      return
    }

    const lastWord = inputValue.trim().split(" ").pop()

    // ✅ Support 1-letter tickers (T, F, X, etc.)
    if (lastWord.length >= 1) {
      const timer = setTimeout(async () => {
        const results = await searchTickers(lastWord)
        setApiSuggestions(results)
        setShowSuggestions(results.length > 0)
      }, 300)  // 300ms debounce

      return () => clearTimeout(timer)
    } else {
      setShowSuggestions(false)
      setApiSuggestions([])
    }
  }, [inputValue, justSelected, searchTickers])

  const getSuggestions = () => {
    return apiSuggestions.slice(0, 5)  // Top 5 from backend
  }

  // 🎯 EXPLICIT CONFIRMATION: Only when user clicks/TABs/Enters
  const selectSuggestion = (result) => {
    const words = inputValue.trim().split(" ")
    // Replace last word with company name (e.g., "KeyCorp" instead of just "KEY")
    words[words.length - 1] = result.name

    // ✅ IMMEDIATE CLOSE: Close dropdown instantly on selection
    setShowSuggestions(false)
    setFocusedSuggestion(-1)
    setJustSelected(true)  // Prevent useEffect from reopening dropdown

    // 🎯 CRITICAL: Only call parent callback with updated text
    onTickerConfirmed(result.ticker, words.join(" "))

    // Refocus input for continued typing
    setTimeout(() => inputRef.current?.focus(), 0)
  }

  const handleKeyDown = (e) => {
    if (showSuggestions) {
      const suggestions = getSuggestions()

      if (e.key === "ArrowDown") {
        e.preventDefault()
        setFocusedSuggestion((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0))
      } else if (e.key === "ArrowUp") {
        e.preventDefault()
        setFocusedSuggestion((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1))
      } else if (e.key === "Tab") {
        // ✅ TAB AUTOCOMPLETE: Complete with focused (or first) suggestion
        e.preventDefault()
        const targetIdx = focusedSuggestion >= 0 ? focusedSuggestion : 0
        if (suggestions[targetIdx]) {
          selectSuggestion(suggestions[targetIdx])
        }
        return
      } else if (e.key === "Enter" && focusedSuggestion >= 0) {
        e.preventDefault()
        selectSuggestion(suggestions[focusedSuggestion])
        return
      } else if (e.key === "Escape") {
        setShowSuggestions(false)
        setFocusedSuggestion(-1)
        return
      }
    }
  }

  // Attach keydown handler to input (passed via props)
  useEffect(() => {
    const input = inputRef.current
    if (input) {
      input.addEventListener('keydown', handleKeyDown)
      return () => input.removeEventListener('keydown', handleKeyDown)
    }
  }, [inputRef, showSuggestions, focusedSuggestion, apiSuggestions])

  // Handle input focus/blur for dropdown
  const handleFocus = () => {
    setShowSuggestions(getSuggestions().length > 0)
  }

  const handleBlur = () => {
    setTimeout(() => setShowSuggestions(false), 100)
  }

  // Attach focus/blur handlers
  useEffect(() => {
    const input = inputRef.current
    if (input) {
      input.addEventListener('focus', handleFocus)
      input.addEventListener('blur', handleBlur)
      return () => {
        input.removeEventListener('focus', handleFocus)
        input.removeEventListener('blur', handleBlur)
      }
    }
  }, [inputRef, apiSuggestions])

  if (!showSuggestions) return null

  return (
    <div
      ref={suggestionsRef}
      className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-y-auto z-50 text-left"
    >
      {getSuggestions().map((result, idx) => {
        const isFocused = idx === focusedSuggestion
        const isFirst = idx === 0
        return (
          <button
            key={result.ticker}
            type="button"
            onMouseDown={(e) => {
              // ✅ USE onMouseDown instead of onClick
              // onMouseDown fires BEFORE onBlur, preventing dropdown flicker
              e.preventDefault()
              selectSuggestion(result)
            }}
            onMouseEnter={() => setFocusedSuggestion(idx)}
            className={`
              w-full px-3 py-2.5 text-left transition-all duration-150
              border-b last:border-b-0 flex items-center justify-between
              cursor-pointer group relative
              ${isFocused
                ? "bg-vitruvyan-accent text-white shadow-sm"
                : "hover:bg-gray-50"
              }
            `}
          >
            <div className="flex items-center gap-2.5">
              <TrendingUp
                size={16}
                className={`transition-colors ${
                  isFocused ? "text-white" : "text-green-600 group-hover:text-green-700"
                }`}
              />
              <div>
                <div className={`font-mono font-semibold text-sm transition-colors ${
                  isFocused ? "text-white" : "text-gray-900"
                }`}>
                  {result.ticker}
                </div>
                <div className={`text-xs transition-colors ${
                  isFocused ? "text-white/90" : "text-gray-500"
                }`}>
                  {result.name}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs transition-colors ${
                isFocused ? "text-white/80" : "text-gray-400"
              }`}>
                {result.sector}
              </span>
              {/* TAB hint - show only on first/focused item */}
              {(isFirst && focusedSuggestion === -1) || isFocused ? (
                <kbd className={`
                  ml-2 px-1.5 py-0.5 text-[10px] font-mono rounded border
                  transition-colors
                  ${isFocused
                    ? "bg-white/20 text-white border-white/30"
                    : "bg-gray-100 text-gray-500 border-gray-300"
                  }
                `}>
                  TAB
                </kbd>
              ) : null}
            </div>
          </button>
        )
      })}
    </div>
  )
}