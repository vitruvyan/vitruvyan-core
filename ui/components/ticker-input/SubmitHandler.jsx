"use client"

import { ArrowRight } from "lucide-react"

// Submit button component - separate from input group
export default function SubmitHandler({
  inputValue,
  confirmedTickers,
  onSubmit,
  isTransitioning = false
}) {
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (inputValue.trim()) {
      // ✅ GOLDEN RULE: NO AUTO-EXTRACTION FROM TEXT!
      // ONLY send tickers that user EXPLICITLY confirmed via autocomplete pills.
      // This prevents false positives like "can I have" → ["CAN"] ticker extraction.
      //
      // The Frontend-Backend Contract:
      // - Frontend MUST validate tickers via PostgreSQL (user clicks pills)
      // - validated_tickers=[] = conversational query → CAN node response
      // - validated_tickers=['AAPL'] = analysis query → Neural Engine response
      //
      // ✅ CORRECT: Only use explicitly confirmed tickers
      onSubmit(inputValue, confirmedTickers)
    }
  }

  return (
    <button
      type="submit"
      onClick={handleSubmit}
      className={`flex items-center justify-center rounded-md bg-gray-800 text-white transition-all hover:bg-gray-700 focus:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 ${
        isTransitioning
          ? 'gap-0 px-3 py-3'
          : 'gap-2 px-4 sm:px-6 py-3 sm:py-4'
      }`}
    >
      {!isTransitioning && <span className="font-medium">Submit</span>}
      <ArrowRight size={18} className="sm:w-5 sm:h-5" />
    </button>
  )
}