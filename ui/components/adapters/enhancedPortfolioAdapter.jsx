/**
 * 💼 ENHANCED PORTFOLIO ADAPTER - Shadow Trading Integration
 * ===========================================================
 * Replaces mock data with real shadow trading portfolio data.
 * 
 * Changes from mock version:
 * - Fetches real portfolio from shadow_broker API
 * - Displays actual holdings with cost basis
 * - Shows real-time unrealized P&L
 * - Adds "Buy More" and "Sell" buttons per holding
 * - Integrates with OrderEntryDialog
 * 
 * Created: Jan 3, 2026
 */

import React, { useState, useEffect } from 'react'
import OrderEntryDialog from '../trading/OrderEntryDialog'
import { TrendingUp, TrendingDown, RefreshCw, Plus, Minus } from 'lucide-react'

export default function EnhancedPortfolioAdapter({ userId = 'default_user' }) {
  const [portfolio, setPortfolio] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [orderDialogOpen, setOrderDialogOpen] = useState(false)
  const [orderDetails, setOrderDetails] = useState(null)

  useEffect(() => {
    fetchPortfolio()
  }, [userId])

  const fetchPortfolio = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/shadow/portfolio/${userId}`)
      const data = await response.json()
      setPortfolio(data)
    } catch (err) {
      setError(`Failed to load portfolio: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const openOrderDialog = (ticker, side, currentPrice, currentShares) => {
    setOrderDetails({
      ticker,
      side,
      currentPrice,
      currentPosition: currentShares
    })
    setOrderDialogOpen(true)
  }

  const handleOrderExecuted = (result) => {
    // Refresh portfolio after order execution
    fetchPortfolio()
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-red-600 mb-4">{error}</div>
        <button
          onClick={fetchPortfolio}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!portfolio) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-gray-500">No portfolio data available</div>
      </div>
    )
  }

  const totalPnLPercent = portfolio.total_value > 0
    ? (portfolio.total_pnl / portfolio.total_value) * 100
    : 0

  return (
    <div className="space-y-6">
      {/* Portfolio Summary */}
      <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold">My Shadow Portfolio</h2>
          <button
            onClick={fetchPortfolio}
            className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <div className="text-sm opacity-80 mb-1">Total Value</div>
            <div className="text-3xl font-bold">
              ${portfolio.total_value.toFixed(2)}
            </div>
          </div>

          <div>
            <div className="text-sm opacity-80 mb-1">Cash Balance</div>
            <div className="text-2xl font-semibold">
              ${portfolio.cash_balance.toFixed(2)}
            </div>
          </div>

          <div>
            <div className="text-sm opacity-80 mb-1">Unrealized P&L</div>
            <div className={`text-xl font-semibold flex items-center gap-2 ${
              portfolio.unrealized_pnl >= 0 ? 'text-green-300' : 'text-red-300'
            }`}>
              {portfolio.unrealized_pnl >= 0 ? (
                <TrendingUp className="w-5 h-5" />
              ) : (
                <TrendingDown className="w-5 h-5" />
              )}
              {portfolio.unrealized_pnl >= 0 ? '+' : ''}${portfolio.unrealized_pnl.toFixed(2)}
            </div>
          </div>

          <div>
            <div className="text-sm opacity-80 mb-1">Total Return</div>
            <div className={`text-xl font-semibold ${
              portfolio.total_pnl >= 0 ? 'text-green-300' : 'text-red-300'
            }`}>
              {portfolio.total_pnl >= 0 ? '+' : ''}${portfolio.total_pnl.toFixed(2)}
              <span className="text-sm ml-2">
                ({totalPnLPercent >= 0 ? '+' : ''}{totalPnLPercent.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-bold text-gray-900">
            Holdings ({portfolio.num_positions})
          </h3>
        </div>

        {portfolio.positions.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            No holdings yet. Start trading to build your portfolio.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Ticker
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Shares
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Avg Cost
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Current Price
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Market Value
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Unrealized P&L
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {portfolio.positions.map((position) => {
                const pnlPercent = position.cost_basis > 0
                  ? ((position.current_price - position.cost_basis) / position.cost_basis) * 100
                  : 0

                return (
                  <tr key={position.ticker} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-bold text-gray-900">
                        {position.ticker}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-600">
                      {position.quantity.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      ${position.cost_basis.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      ${position.current_price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                      ${position.market_value.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      <div className={`font-semibold ${
                        position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl.toFixed(2)}
                        <div className="text-xs">
                          ({pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%)
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => openOrderDialog(
                            position.ticker,
                            'buy',
                            position.current_price,
                            position.quantity
                          )}
                          className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                          title="Buy More"
                        >
                          <Plus className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => openOrderDialog(
                            position.ticker,
                            'sell',
                            position.current_price,
                            position.quantity
                          )}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Sell"
                        >
                          <Minus className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Order Entry Dialog */}
      {orderDialogOpen && orderDetails && (
        <OrderEntryDialog
          isOpen={orderDialogOpen}
          onClose={() => setOrderDialogOpen(false)}
          ticker={orderDetails.ticker}
          side={orderDetails.side}
          currentPrice={orderDetails.currentPrice}
          cashBalance={portfolio.cash_balance}
          currentPosition={orderDetails.currentPosition}
          onOrderExecuted={handleOrderExecuted}
        />
      )}
    </div>
  )
}
