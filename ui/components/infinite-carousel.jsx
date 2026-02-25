"use client"

import React from "react"

const InfiniteCarousel = React.memo(({ questions, direction = "left", onQuestionClick }) => {
  const animationClass =
    direction === "left" ? "animate-[scroll-left_30s_linear_infinite]" : "animate-[scroll-right_30s_linear_infinite]"
  const content = [...questions, ...questions] // Duplicate for seamless loop

  return (
    <div className="group relative w-full overflow-hidden">
      <div className={`flex w-max gap-4 ${animationClass} group-hover:pause`}>
        {content.map((q, i) => (
          <button
            key={i}
            onClick={() => onQuestionClick(q)}
            className="flex-shrink-0 whitespace-nowrap rounded-full border border-gray-300 bg-white px-4 py-2 text-left text-sm text-gray-600 transition hover:bg-vitruvyan-accent hover:text-white hover:border-vitruvyan-accent focus:bg-vitruvyan-accent focus:text-white focus:border-vitruvyan-accent focus:outline-none focus:ring-2 focus:ring-vitruvyan-accent focus:ring-offset-2"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
})

InfiniteCarousel.displayName = "InfiniteCarousel"

export default InfiniteCarousel
