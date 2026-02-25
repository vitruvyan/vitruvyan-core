"use client"

import { useState } from "react"
import HeroLanding from "@/components/hero-landing"
import Chat from "@/components/chat/Chat"

export default function LandingPage() {
  const [transitionPhase, setTransitionPhase] = useState("hero") // "hero" | "report"
  const [initialQuestion, setInitialQuestion] = useState("")
  const [initialTickers, setInitialTickers] = useState([]) // 🎯 Store user-selected tickers
  const [analysisResults, setAnalysisResults] = useState(null)

  const handleQuestionSubmit = (question, detectedTickers = []) => {
    console.log("[LandingPage] Question submitted:", question, "Tickers:", detectedTickers)
    setInitialQuestion(question)
    setInitialTickers(detectedTickers) // Store tickers for Chat component
    setTransitionPhase("report")
  }

  const handleAnalysisComplete = (results) => {
    console.log("[LandingPage] Analysis complete:", results)
    setAnalysisResults(results)
  }

  if (transitionPhase === "hero") {
    return (
      <div className="flex flex-1 relative overflow-hidden bg-gray-50">
        <main className="flex flex-grow items-center justify-center animate-fadeIn">
          <HeroLanding onQuestionSubmit={handleQuestionSubmit} />
        </main>
      </div>
    )
  }

  if (transitionPhase === "report") {
    return (
      <div className="flex flex-col flex-1 overflow-hidden bg-gray-50">
        {/* Chat - Full Screen with generous spacing */}
        <div className="flex-1 flex items-center justify-center py-12 px-20">
          <div className="w-full max-w-4xl">
            <Chat
              isVisible={true}
              initialQuestion={initialQuestion}
              initialTickers={initialTickers}
              isSidebar={false}
              onAnalysisComplete={handleAnalysisComplete}
            />
          </div>
        </div>
      </div>
    )
  }

  return null
}
