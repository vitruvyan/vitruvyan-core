'use client'

export function IntentBadge({ intent, horizon }) {
  if (!intent || intent === 'unknown') return null
  
  const intentLabels = {
    trend: 'Trend Analysis',
    momentum: 'Momentum Check',
    sentiment: 'Sentiment Analysis',
    comparison: 'Comparison',
    screening: 'Screening',
    portfolio: 'Portfolio Review',
    allocation: 'Allocation'
  }
  
  return (
    <div className="flex items-center gap-2 mb-2">
      <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded-full font-medium">
        {intentLabels[intent] || intent}
      </span>
      {horizon && (
        <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
          {horizon}
        </span>
      )}
    </div>
  )
}