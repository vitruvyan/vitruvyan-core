// components/chat/AllocationStrategySelector.jsx
'use client'

import { useState } from 'react'
import { Target, Shield, TrendingUp, BarChart3, Zap } from 'lucide-react'

const ALLOCATION_STRATEGIES = [
  {
    id: 'equal_weight',
    name: 'Equal Weight',
    description: 'Equal allocation across all holdings',
    icon: BarChart3,
    color: 'bg-blue-500'
  },
  {
    id: 'risk_parity',
    name: 'Risk Parity',
    description: 'Weight inversely to volatility',
    icon: Shield,
    color: 'bg-green-500'
  },
  {
    id: 'max_sharpe',
    name: 'Maximum Sharpe',
    description: 'Optimize for risk-adjusted returns',
    icon: TrendingUp,
    color: 'bg-purple-500'
  },
  {
    id: 'sector_focused',
    name: 'Sector Focused',
    description: 'Prioritize sectors from your query',
    icon: Target,
    color: 'bg-orange-500'
  },
  {
    id: 'risk_adjusted',
    name: 'Risk Adjusted',
    description: 'Balance risk and semantic preferences',
    icon: Zap,
    color: 'bg-red-500'
  }
]

export function AllocationStrategySelector({ onStrategySelect, onCancel, selectedStrategy }) {
  const [hoveredStrategy, setHoveredStrategy] = useState(null)

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-lg">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Choose Allocation Strategy
        </h3>
        <p className="text-sm text-gray-600">
          Select how you want to distribute your investment across the selected holdings.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 mb-4">
        {ALLOCATION_STRATEGIES.map((strategy) => {
          const Icon = strategy.icon
          const isSelected = selectedStrategy === strategy.id
          const isHovered = hoveredStrategy === strategy.id

          return (
            <button
              key={strategy.id}
              onClick={() => onStrategySelect(strategy.id)}
              onMouseEnter={() => setHoveredStrategy(strategy.id)}
              onMouseLeave={() => setHoveredStrategy(null)}
              className={`w-full p-3 rounded-lg border-2 transition-all duration-200 text-left ${
                isSelected
                  ? 'border-emerald-500 bg-emerald-50 shadow-md'
                  : isHovered
                  ? 'border-gray-300 bg-gray-50 shadow-sm'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${strategy.color} text-white`}>
                  <Icon size={20} />
                </div>
                <div className="flex-1">
                  <div className="font-medium text-gray-900">
                    {strategy.name}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {strategy.description}
                  </div>
                </div>
                {isSelected && (
                  <div className="text-emerald-600">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
            </button>
          )
        })}
      </div>

      <div className="flex gap-2">
        <button
          onClick={onCancel}
          className="flex-1 px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={() => onStrategySelect(selectedStrategy)}
          disabled={!selectedStrategy}
          className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Allocate
        </button>
      </div>
    </div>
  )
}