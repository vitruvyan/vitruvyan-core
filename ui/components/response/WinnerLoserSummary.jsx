// components/response/WinnerLoserSummary.jsx
import React from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

const WinnerLoserSummary = ({ comparisonSummary }) => {
  const { winner, loser, deltaComposite, verdict } = comparisonSummary

  // Verdict badge styling
  const getVerdictBadgeStyle = (orientation) => {
    const styles = {
      "clear-winner": "bg-green-100 border-green-300 text-green-800",
      "moderate-lead": "bg-blue-100 border-blue-300 text-blue-800",
      "tight-race": "bg-yellow-100 border-yellow-300 text-yellow-800"
    }
    return styles[orientation] || styles["tight-race"]
  }

  return (
    <div className="border border-gray-200 rounded-lg p-6 bg-gradient-to-r from-green-50 to-red-50">
      {/* Verdict Badge */}
      <div className="flex justify-center mb-4">
        <div className={`px-4 py-2 rounded-full border-2 font-semibold text-sm ${getVerdictBadgeStyle(verdict.orientation)}`}>
          {verdict.label}
        </div>
      </div>

      {/* Winner vs Loser Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Winner Card */}
        <div className="bg-white border-2 border-green-400 rounded-lg p-4 shadow-md">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-xs text-gray-600 font-medium">WINNER</div>
                <div className="text-lg font-bold text-gray-900">{winner.ticker}</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-green-600">{winner.composite?.toFixed(2)}</div>
              <div className="text-xs text-gray-500">Composite</div>
            </div>
          </div>
          <div className="text-sm text-gray-700">{winner.companyName}</div>
        </div>

        {/* Loser Card */}
        <div className="bg-white border-2 border-red-300 rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 bg-red-400 rounded-full flex items-center justify-center">
                <TrendingDown className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-xs text-gray-600 font-medium">LOSER</div>
                <div className="text-lg font-bold text-gray-900">{loser.ticker}</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-red-600">{loser.composite?.toFixed(2)}</div>
              <div className="text-xs text-gray-500">Composite</div>
            </div>
          </div>
          <div className="text-sm text-gray-700">{loser.companyName}</div>
        </div>
      </div>

      {/* Delta Display */}
      <div className="mt-4 text-center">
        <div className="text-sm text-gray-600">Performance Gap:</div>
        <div className="text-3xl font-bold text-gray-900 mt-1">
          {deltaComposite > 0 ? '+' : ''}{deltaComposite?.toFixed(2)}
        </div>
      </div>

      {/* Verdict Rationale */}
      <div className="mt-4 p-3 bg-white rounded-lg border border-gray-200">
        <p className="text-sm text-gray-700 italic">"{verdict.rationale}"</p>
      </div>
    </div>
  )
}

export default WinnerLoserSummary
