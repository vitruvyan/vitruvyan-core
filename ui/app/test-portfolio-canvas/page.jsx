"use client"

import { useState } from 'react'
import { GuardianTimeline } from '@/components/portfolio-canvas'

/**
 * Standalone Test Page for Portfolio Canvas Components
 * 
 * Purpose: Test GuardianTimeline and InsightCard WITHOUT WebSocket dependency
 * URL: http://localhost:3000/test-portfolio-canvas
 * 
 * Created: Jan 26, 2026
 * Reason: WebSocket backend (Task 26.1) not yet implemented
 */

export default function TestPortfolioCanvas() {
  const [mockInsights] = useState([
    {
      insight_id: 1,
      category: 'PROTECT',
      insight_type: 'risk_alert',
      severity: 'critical',
      title: 'High Concentration Risk Detected',
      description: 'AAPL represents 43.4% of portfolio value. Consider rebalancing to reduce single-ticker exposure.',
      recommendations: [
        'Reduce AAPL concentration to 30% (currently 43.4%)',
        'Diversify into 2-3 additional quality positions',
        'Consider sector rotation to reduce tech exposure',
        'Implement gradual reduction over 7-14 days'
      ],
      affected_tickers: ['AAPL'],
      vee_explanation: 'Portfolio concentration analysis reveals AAPL single-ticker dominance at 43.4%, exceeding prudent 30% threshold. This creates systemic risk if AAPL experiences negative events. Neural Engine Function G (concentration risk) computed z-score of +2.3 (top 1% concentration). Strategic recommendation: gradual reduction to 28-32% range over 2-week period to minimize market impact costs while restoring diversification benefits.',
      created_at: new Date().toISOString(),
      confidence: 0.92
    },
    {
      insight_id: 2,
      category: 'IMPROVE',
      insight_type: 'opportunity',
      severity: 'medium',
      title: 'Underweight in AI Semiconductor Space',
      description: 'Portfolio has 0% allocation to AI infrastructure leaders. Strategic opportunity detected.',
      recommendations: [
        'Consider NVDA position (currently 0% weight)',
        'Target 10-15% allocation to AI semiconductor sector',
        'Entry timing: wait for pullback to $850-880 range',
        'Alternative: AVGO or AMD for diversification'
      ],
      affected_tickers: ['NVDA', 'AVGO', 'AMD'],
      vee_explanation: 'Sector analysis reveals complete absence of AI semiconductor exposure. Given current market dynamics (AI infrastructure spending +40% YoY) and Nvidia\'s technical momentum (RSI: 68, MACD bullish crossover), strategic underweight creates opportunity cost. Historical correlation with existing portfolio: 0.42 (low), offering genuine diversification benefits. Risk-adjusted return projection: +18-25% over 12 months with 15% vol.',
      created_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
      confidence: 0.78
    },
    {
      insight_id: 3,
      category: 'UNDERSTAND',
      insight_type: 'correlation',
      severity: 'low',
      title: 'Rising Correlation: AAPL-MSFT',
      description: 'Correlation between AAPL and MSFT increased to 0.87 (30-day rolling). Diversification benefits erosion detected.',
      recommendations: [
        'Monitor correlation trend (current: 0.87, threshold: 0.70)',
        'Consider uncorrelated asset classes (REITs, commodities, utilities)',
        'Review portfolio construction for systemic risk',
        'No immediate action required (informational only)'
      ],
      affected_tickers: ['AAPL', 'MSFT'],
      vee_explanation: 'Recent 30-day rolling correlation between AAPL and MSFT reached 0.87, significantly above historical average of 0.65. This correlation spike reduces diversification benefits and increases portfolio beta to market-wide shocks. Causes: both stocks exposed to similar macro factors (interest rates, tech sentiment, institutional flows). While not critical (threshold: 0.90), trend monitoring recommended. Consider adding low-correlation assets (utilities sector correlation to tech: 0.23).',
      created_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
      confidence: 0.85
    },
    {
      insight_id: 4,
      category: 'PROTECT',
      insight_type: 'concentration',
      severity: 'high',
      title: 'Sector Concentration: Technology 78%',
      description: 'Technology sector represents 78% of total portfolio value. Sector diversification below recommended levels.',
      recommendations: [
        'Reduce tech sector from 78% to 60-65%',
        'Add positions in Healthcare (target: 15-20%)',
        'Consider defensive sectors (Consumer Staples, Utilities)',
        'Maintain growth orientation but reduce concentration risk'
      ],
      affected_tickers: ['AAPL', 'MSFT', 'GOOGL'],
      vee_explanation: 'Sector analysis reveals severe Technology concentration at 78% of portfolio value. While Tech sector offers superior growth (historical +22% annual), concentration at this level exposes portfolio to sector-specific shocks (regulatory risks, interest rate sensitivity, competition dynamics). Recommended target: 60-65% Tech + 15-20% Healthcare + 10-15% Financials + 5-10% Defensive. This maintains growth orientation while adding resilience.',
      created_at: new Date(Date.now() - 10800000).toISOString(), // 3 hours ago
      confidence: 0.88
    },
    {
      insight_id: 5,
      category: 'IMPROVE',
      insight_type: 'opportunity',
      severity: 'low',
      title: 'Dividend Growth Opportunity',
      description: 'Portfolio dividend yield: 0.8%. Missing income generation opportunities.',
      recommendations: [
        'Consider dividend aristocrats (JNJ, PG, KO)',
        'Target blended yield: 1.5-2.0% (currently 0.8%)',
        'Focus on dividend growth stocks (not high yield)',
        'Maintain total return orientation (growth + income)'
      ],
      affected_tickers: ['JNJ', 'PG', 'KO', 'V'],
      vee_explanation: 'Portfolio currently generates 0.8% dividend yield, below diversified portfolio baseline of 1.5-2.0%. While growth stocks (AAPL, MSFT, GOOGL) offer capital appreciation, adding selective dividend growers provides: 1) income diversification, 2) downside protection (dividend stocks -30% less volatile in corrections), 3) total return enhancement. Target allocation: 15-20% to quality dividend growers with 10-year dividend CAGR >8%.',
      created_at: new Date(Date.now() - 14400000).toISOString(), // 4 hours ago
      confidence: 0.72
    }
  ])

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Portfolio Canvas Component Test
          </h1>
          <p className="text-gray-600">
            Testing GuardianTimeline and InsightCard components with mock data (Task 26.3)
          </p>
          <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              ⚠️ <strong>Note</strong>: WebSocket backend (Task 26.1) not yet implemented. 
              Using static mock data for component testing.
            </p>
          </div>
        </div>

        {/* Mock Data Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white border rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Total Insights</div>
            <div className="text-2xl font-bold text-gray-900">{mockInsights.length}</div>
          </div>
          <div className="bg-white border rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">PROTECT Category</div>
            <div className="text-2xl font-bold text-red-600">
              {mockInsights.filter(i => i.category === 'PROTECT').length}
            </div>
          </div>
          <div className="bg-white border rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">IMPROVE Category</div>
            <div className="text-2xl font-bold text-green-600">
              {mockInsights.filter(i => i.category === 'IMPROVE').length}
            </div>
          </div>
        </div>

        {/* GuardianTimeline Component */}
        <div className="bg-white border rounded-lg p-6">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Guardian Timeline Component</h2>
            <p className="text-sm text-gray-600 mt-1">
              Real-time insights with category filtering and severity-based visual hierarchy
            </p>
          </div>
          
          <GuardianTimeline insights={mockInsights} />
        </div>

        {/* Testing Checklist */}
        <div className="mt-8 bg-white border rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Testing Checklist</h3>
          
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check1" />
              <label htmlFor="check1" className="text-sm text-gray-700">
                <strong>Category Tabs</strong>: ALL, PROTECT, IMPROVE, UNDERSTAND tabs visible with correct counts
              </label>
            </div>
            
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check2" />
              <label htmlFor="check2" className="text-sm text-gray-700">
                <strong>Category Filtering</strong>: Click each tab → only relevant insights displayed
              </label>
            </div>
            
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check3" />
              <label htmlFor="check3" className="text-sm text-gray-700">
                <strong>Severity Badges</strong>: Critical=red, High=orange, Medium=blue, Low=gray color coding
              </label>
            </div>
            
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check4" />
              <label htmlFor="check4" className="text-sm text-gray-700">
                <strong>VEE Explanation</strong>: Click "Show VEE Explanation" → collapsible content expands
              </label>
            </div>
            
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check5" />
              <label htmlFor="check5" className="text-sm text-gray-700">
                <strong>Recommendations</strong>: Strategic recommendations displayed as bulleted list with checkmarks
              </label>
            </div>
            
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check6" />
              <label htmlFor="check6" className="text-sm text-gray-700">
                <strong>Affected Tickers</strong>: Ticker badges (AAPL, NVDA, etc.) displayed as pills
              </label>
            </div>
            
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check7" />
              <label htmlFor="check7" className="text-sm text-gray-700">
                <strong>Timestamps</strong>: Relative timestamps ("1 hour ago", "2 hours ago") formatted correctly
              </label>
            </div>
            
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check8" />
              <label htmlFor="check8" className="text-sm text-gray-700">
                <strong>Responsive Grid</strong>: Desktop shows 2-column grid, mobile shows single column
              </label>
            </div>
            
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check9" />
              <label htmlFor="check9" className="text-sm text-gray-700">
                <strong>Empty State</strong>: Click "UNDERSTAND" tab → shows "No insights in this category" message
              </label>
            </div>
            
            <div className="flex items-start gap-3">
              <input type="checkbox" className="mt-1" id="check10" />
              <label htmlFor="check10" className="text-sm text-gray-700">
                <strong>Action Buttons</strong>: "View Details" and "Dismiss" buttons render with hover effects
              </label>
            </div>
          </div>
        </div>

        {/* Browser Console Instructions */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">
            📋 Browser Console Testing
          </h3>
          
          <p className="text-sm text-blue-800 mb-3">
            Open DevTools (F12) → Console tab and verify:
          </p>
          
          <ul className="space-y-2 text-sm text-blue-700">
            <li className="flex items-start gap-2">
              <span>✅</span>
              <span>No JavaScript errors displayed</span>
            </li>
            <li className="flex items-start gap-2">
              <span>✅</span>
              <span>No React hydration warnings</span>
            </li>
            <li className="flex items-start gap-2">
              <span>✅</span>
              <span>No TypeScript type errors</span>
            </li>
            <li className="flex items-start gap-2">
              <span>✅</span>
              <span>Components render without crashes</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
