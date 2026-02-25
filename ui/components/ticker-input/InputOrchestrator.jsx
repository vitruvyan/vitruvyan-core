"use client"

import { useState, useRef } from "react"
import { Upload, Mic } from "lucide-react"
import ConversationalInput from "./ConversationalInput"
import TickerAutocomplete from "./TickerAutocomplete"
import TickerPills from "./TickerPills"
import SubmitHandler from "./SubmitHandler"

// 🎯 Backend API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || ""

// 🔍 Search tickers via backend API (validates against PostgreSQL 519 tickers)
async function searchTickers(query) {
  // ✅ Support 1-letter tickers (T, F, X, etc.) - changed from < 2 to < 1
  if (!query || query.length < 1) return []

  try {
    const response = await fetch(`${API_BASE_URL}/api/tickers/search?q=${encodeURIComponent(query)}`)
    const data = await response.json()

    if (data.status === "success") {
      return data.results  // [{ticker, name, sector, match_score}]
    }
    return []
  } catch (error) {
    console.error("[InputOrchestrator] Ticker search error:", error)
    return []
  }
}

export default function InputOrchestrator({ onQuestionSubmit, isTransitioning = false }) {
  // 🎯 SINGLE SOURCE OF TRUTH: confirmedTickers (NOT detectedTickers)
  const [inputValue, setInputValue] = useState("")
  const [confirmedTickers, setConfirmedTickers] = useState([])  // Only user-confirmed tickers

  const inputRef = useRef(null)

  // Handle explicit ticker confirmation from autocomplete
  const handleTickerConfirmed = (ticker, updatedText) => {
    if (!confirmedTickers.includes(ticker)) {
      setConfirmedTickers([...confirmedTickers, ticker])
    }
    // Update input text with company name (e.g., "analizza KeyCorp")
    if (updatedText) {
      setInputValue(updatedText)
    }
  }

  // Handle ticker removal from pills
  const handleRemoveTicker = (ticker) => {
    setConfirmedTickers(confirmedTickers.filter(t => t !== ticker))
  }

  // Handle form submission
  const handleSubmit = (inputText, tickers) => {
    // ✅ Frontend-Backend Contract: Empty array = conversational, populated = analysis
    onQuestionSubmit(inputText, tickers)
  }

  return (
    <>
      {/* Input group container */}
      <div className="group relative flex-grow">
        {/* Confirmed tickers pills - shown above input */}
        <TickerPills
          confirmedTickers={confirmedTickers}
          onRemoveTicker={handleRemoveTicker}
        />

        {/* Pure text input - no ticker logic */}
        <ConversationalInput
          ref={inputRef}
          inputValue={inputValue}
          onInputChange={setInputValue}
          confirmedTickers={confirmedTickers}
        />

        {/* Upload button - inside input, bottom left */}
        <div className="absolute bottom-2 sm:bottom-3 left-2 sm:left-3">
          <button type="button" className="group/tooltip relative" aria-label="Upload portfolio">
            <Upload
              size={18}
              className="text-gray-400 transition group-hover/tooltip:text-gray-600 sm:w-5 sm:h-5"
            />
            <span className="pointer-events-none absolute -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-gray-800 px-2 py-1 text-xs text-white opacity-0 transition-opacity group-hover/tooltip:opacity-100">
              Upload portfolio CSV or Excel
            </span>
          </button>
        </div>

        {/* Voice button - inside input, bottom right */}
        <div className="absolute bottom-2 sm:bottom-3 right-2 sm:right-3">
          <button type="button" className="group/tooltip relative" aria-label="Use voice assistant">
            <Mic
              size={18}
              className="text-gray-400 transition group-hover/tooltip:text-gray-600 sm:w-5 sm:h-5"
            />
            <span className="pointer-events-none absolute -top-8 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-gray-800 px-2 py-1 text-xs text-white opacity-0 transition-opacity group-hover/tooltip:opacity-100">
              Use voice assistant
            </span>
          </button>
        </div>

        {/* Autocomplete dropdown - explicit confirmation only */}
        <TickerAutocomplete
          inputValue={inputValue}
          onTickerConfirmed={handleTickerConfirmed}
          searchTickers={searchTickers}
          inputRef={inputRef}
        />
      </div>

      {/* Submit button - OUTSIDE input group, sibling element */}
      <SubmitHandler
        inputValue={inputValue}
        confirmedTickers={confirmedTickers}
        onSubmit={handleSubmit}
        isTransitioning={isTransitioning}
      />
    </>
  )
}