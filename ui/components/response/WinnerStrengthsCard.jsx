// components/response/WinnerStrengthsCard.jsx
import React from 'react'
import { Trophy, TrendingUp, Target } from 'lucide-react'

const WinnerStrengthsCard = ({ ticker, strengths, keyDifferentiator, keyDelta }) => {
  // Fallback if no strengths
  if (!strengths || strengths.length === 0) {
    return (
      <div className="border border-gray-200 bg-gray-50 rounded-lg p-6 text-center">
        <p className="text-sm text-gray-600">
          No significant competitive advantages detected (all factors within ±0.3 range)
        </p>
      </div>
    )
  }

  return (
    <div className="border border-green-200 bg-green-50 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <Trophy className="w-6 h-6 text-green-600" />
        <h3 className="text-lg font-semibold text-green-900">
          {ticker} Competitive Advantages
        </h3>
      </div>

      {/* Key Differentiator (highlighted) */}
      {keyDifferentiator && (
        <div className="bg-yellow-100 border border-yellow-300 rounded-lg p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-5 h-5 text-yellow-700" />
            <span className="text-sm font-semibold text-yellow-900 uppercase tracking-wide">
              🔑 Key Differentiator
            </span>
          </div>
          <p className="text-base font-medium text-yellow-900">
            {keyDifferentiator}
          </p>
          {keyDelta && (
            <p className="text-sm text-yellow-700 mt-1">
              Delta: <span className="font-mono font-semibold">+{keyDelta.toFixed(2)}</span>
            </p>
          )}
        </div>
      )}

      {/* Strengths List */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="w-5 h-5 text-green-600" />
          <h4 className="text-sm font-semibold text-green-800 uppercase tracking-wide">
            Superior Factors
          </h4>
        </div>
        <ul className="space-y-2">
          {strengths.map((strength, idx) => (
            <li
              key={idx}
              className="flex items-center gap-3 bg-white border border-green-200 rounded-md p-3"
            >
              <div className="w-2 h-2 bg-green-500 rounded-full flex-shrink-0" />
              <span className="text-sm font-medium text-gray-800">
                {strength}
              </span>
              <span className="ml-auto text-xs text-green-600 font-semibold">
                ✓ Superior
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* VEE Tooltip: Competitive Advantage Interpretation */}
      <div className="mt-4 pt-4 border-t border-green-200 space-y-2">
        <p className="text-xs text-green-700">
          💡 <strong>Interpretation:</strong> Factors with delta &gt; +0.3 indicate significant competitive advantage.
        </p>
        <div className="bg-white border border-green-300 rounded-md p-3 text-xs text-gray-700 space-y-1">
          <p className="font-semibold text-green-800">What makes a competitive advantage?</p>
          <p>• <strong>Delta +0.3 to +0.7:</strong> Moderate advantage - noticeable but not decisive</p>
          <p>• <strong>Delta +0.7 to +1.5:</strong> Strong advantage - clear leader in this factor</p>
          <p>• <strong>Delta &gt;+1.5:</strong> Exceptional advantage - dominant positioning</p>
          <p className="mt-2 text-green-700">🔑 Key Differentiator = factor with largest delta</p>
        </div>
      </div>
    </div>
  )
}

export default WinnerStrengthsCard
