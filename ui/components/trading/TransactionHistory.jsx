/**
 * 📜 TRANSACTION HISTORY - Shadow Trading History
 * ================================================
 * Display user's shadow trading transaction history with P&L tracking.
 * 
 * Features:
 * - Buy/sell transaction list
 * - Realized P&L display
 * - Filter by ticker
 * - Sort by date
 * - Export to CSV (future)
 * 
 * Props:
 * - userId: string
 * - limit: number (default 50)
 * 
 * Created: Jan 3, 2026
 */

import React, { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, DollarSign, Filter, Download } from 'lucide-react'

export default function TransactionHistory({ userId, limit = 50 }) {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterTicker, setFilterTicker] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchHistory()
  }, [userId, filterTicker])

  const fetchHistory = async () => {
    setLoading(true)
    setError(null)

    try {
      const url = filterTicker
        ? `/api/shadow/history/${userId}?ticker=${filterTicker}&limit=${limit}`
        : `/api/shadow/history/${userId}?limit=${limit}`

      const response = await fetch(url)
      const data = await response.json()

      setTransactions(data.transactions || [])
    } catch (err) {
      setError(`Failed to load history: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-red-600">{error}</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">
            Transaction History
          </h2>
          <button
            onClick={() => {/* TODO: Export to CSV */}}
            className="flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Filter by ticker (e.g., AAPL)"
            value={filterTicker}
            onChange={(e) => setFilterTicker(e.target.value.toUpperCase())}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          {filterTicker && (
            <button
              onClick={() => setFilterTicker('')}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Transactions List */}
      <div className="overflow-x-auto">
        {transactions.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            No transactions yet. Start trading to see your history.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Ticker
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Quantity
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Price
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Total
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Realized P&L
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {transactions.map((tx) => {
                const isBuy = tx.type === 'buy'
                const hasProfit = tx.realized_pnl && tx.realized_pnl > 0

                return (
                  <tr key={tx.transaction_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {new Date(tx.date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`flex items-center gap-2 ${
                        isBuy ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {isBuy ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : (
                          <TrendingDown className="w-4 h-4" />
                        )}
                        <span className="text-sm font-medium uppercase">
                          {tx.type}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-semibold text-gray-900">
                        {tx.ticker}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-600">
                      {tx.quantity.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900">
                      ${tx.price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                      ${tx.total_value.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      {tx.realized_pnl !== null ? (
                        <span className={`font-semibold ${
                          hasProfit ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {hasProfit ? '+' : ''}${tx.realized_pnl.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer Summary */}
      {transactions.length > 0 && (
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Showing {transactions.length} of {limit} transactions
            </div>
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">
                Total Realized P&L:
              </span>
              <span className={`text-lg font-bold ${
                transactions.reduce((sum, tx) => sum + (tx.realized_pnl || 0), 0) > 0
                  ? 'text-green-600'
                  : 'text-red-600'
              }`}>
                ${transactions.reduce((sum, tx) => sum + (tx.realized_pnl || 0), 0).toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
