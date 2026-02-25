'use client'

import { useState } from 'react'

/**
 * Reusable Tab Panel Component
 * Used for chart explanations and educational content
 */
export default function TabPanel({ tabs, defaultTab = 0 }) {
  const [activeTab, setActiveTab] = useState(defaultTab)

  return (
    <div className="w-full">
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-4">
        {tabs.map((tab, idx) => (
          <button
            key={idx}
            onClick={() => setActiveTab(idx)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === idx
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700 hover:border-b-2 hover:border-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="w-full">
        {tabs[activeTab].content}
      </div>
    </div>
  )
}
