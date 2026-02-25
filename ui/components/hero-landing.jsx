"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import InfiniteCarousel from "@/components/infinite-carousel"
import InputOrchestrator from "@/components/ticker-input/InputOrchestrator"

const DynamicGreeting = () => {
  const [greeting, setGreeting] = useState("")

  useEffect(() => {
    // Get user from localStorage
    const storedUser = localStorage.getItem("keycloak_user")
    const userName = storedUser ? JSON.parse(storedUser).name : null

    const greetings = [
      `Hi${userName ? ` ${userName.split(" ")[0]}` : ""}! Ready to make smart investment decisions today?`,
      `Hello${userName ? ` ${userName.split(" ")[0]}` : ""}! How can I help you grow your portfolio?`,
      `Welcome back${userName ? ` ${userName.split(" ")[0]}` : ""}! Let's explore the stock market together.`,
      `Hi${userName ? ` ${userName.split(" ")[0]}` : ""}! What investment opportunities should we analyze today?`,
      `Good day${userName ? ` ${userName.split(" ")[0]}` : ""}! Ready to dive into market insights?`,
      `Hello${userName ? ` ${userName.split(" ")[0]}` : ""}! Let's find your next winning investment.`,
      `Hi there${userName ? ` ${userName.split(" ")[0]}` : ""}! Time to optimize your trading strategy?`,
      `Welcome${userName ? ` ${userName.split(" ")[0]}` : ""}! What stocks are catching your attention?`,
      `Hey${userName ? ` ${userName.split(" ")[0]}` : ""}! Ready to unlock market opportunities?`,
      `Hello${userName ? ` ${userName.split(" ")[0]}` : ""}! Let's make your money work smarter today.`,
    ]

    const randomGreeting = greetings[Math.floor(Math.random() * greetings.length)]
    setGreeting(randomGreeting)
  }, [])

  return (
    <>
      {greeting.split(" ").map((word, index) => {
        if (
          word.includes("investment") ||
          word.includes("portfolio") ||
          word.includes("stock") ||
          word.includes("market") ||
          word.includes("trading") ||
          word.includes("money")
        ) {
          return (
            <span key={index} className="text-vitruvyan-accent">
              {word}{" "}
            </span>
          )
        }
        return <span key={index}>{word} </span>
      })}
    </>
  )
}

export default function HeroLanding({ onQuestionSubmit, isTransitioning = false }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const router = useRouter()

  useEffect(() => {
    // Check if user is logged in
    const storedUser = localStorage.getItem("keycloak_user")
    setIsLoggedIn(!!storedUser)
  }, [])

  const handleQuestionClick = (question) => {
    // This would need to be passed down to InputOrchestrator
    // For now, we'll handle it here or move to parent
    console.log("Question clicked:", question)
  }

  // Suggested questions for carousel
  const suggestedQuestions = [
    "What are the best tech stocks to buy now?",
    "Show me dividend stocks with high yield",
    "Compare AAPL vs MSFT performance",
    "What are the top performing ETFs?",
    "Analyze Tesla's financial health",
    "Which stocks are undervalued right now?",
    "What are the latest market trends?",
    "Show me stocks with strong growth potential",
  ]

  return (
    <div className="container mx-auto flex h-full flex-col justify-center p-4 text-center">
      <div className="mx-auto max-w-3xl py-8 sm:py-16">
        {/* Greeting - Fades out during transition */}
        <h2 className={`font-ibm-plex-sans text-2xl sm:text-3xl md:text-4xl font-semibold text-gray-900 transition-opacity duration-300 ${
          isTransitioning ? 'opacity-0' : 'opacity-100'
        }`}>
          <DynamicGreeting />
        </h2>

        <form onSubmit={(e) => e.preventDefault()} className="mt-16 sm:mt-24 flex flex-col gap-4 md:flex-row relative z-20">
          {/* Modular Input Orchestrator */}
          <InputOrchestrator
            onQuestionSubmit={onQuestionSubmit}
            isTransitioning={isTransitioning}
          />
        </form>

        {/* Carousel - positioned after the form */}
        <div className={`mt-16 sm:mt-24 space-y-3 transition-opacity duration-300 ${
          isTransitioning ? 'opacity-0' : 'opacity-100'
        }`}>
          <InfiniteCarousel
            questions={suggestedQuestions.slice(0, 4)}
            direction="left"
            onQuestionClick={handleQuestionClick}
          />
          <InfiniteCarousel
            questions={suggestedQuestions.slice(4, 8)}
            direction="right"
            onQuestionClick={handleQuestionClick}
          />
        </div>
      </div>
    </div>
  )
}
