/**
 * PortfolioHeader - Top Stats Summary
 * 
 * Displays total value, daily P&L, and quick stats
 */

export function PortfolioHeader({ portfolioStats }) {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Portfolio Dashboard</h1>
            <p className="text-sm text-gray-600 mt-1">Real-time analytics and insights</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm text-gray-600">Total Value</p>
              <p className="text-2xl font-bold text-gray-900">
                ${portfolioStats.totalValue.toLocaleString()}
              </p>
              <p className={`text-sm font-medium ${portfolioStats.pnlPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {portfolioStats.pnlPercent >= 0 ? '+' : ''}{portfolioStats.pnlPercent.toFixed(2)}% today
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
