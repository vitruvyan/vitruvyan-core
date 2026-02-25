/**
 * Portfolio Banner Data Adapter
 * 
 * Transforms raw portfolio API response into optimized format for banner display.
 * 
 * Input: Raw API response from /api/portfolio/holdings/{userId}
 * Output: Lightweight banner-optimized data structure
 * 
 * Created: January 20, 2026
 */

export function adaptPortfolioBanner(rawData) {
  if (!rawData || !rawData.holdings) {
    return {
      totalValue: 0,
      pnlPercent: 0,
      pnlAbsolute: 0,
      holdings: [],
      alertsCount: 0,
      riskScore: 0,
      diversificationScore: 0,
      sectorsCount: 0
    }
  }

  const { holdings, total_value, metadata } = rawData

  // Calculate P&L
  const pnlAbsolute = metadata?.total_pnl || 0
  const pnlPercent = total_value > 0 ? (pnlAbsolute / total_value) * 100 : 0

  // Transform holdings for banner display
  const bannerHoldings = holdings
    .map(holding => ({
      ticker: holding.ticker,
      companyName: holding.company_name || holding.ticker,
      weight: holding.weight || 0,
      pnl: holding.pnl || 0,
      pnlPercent: holding.pnl_percent || 0,
      value: holding.value || 0,
      shares: holding.shares || 0,
      isHighlighted: false // Will be set by component based on currentTicker
    }))
    .sort((a, b) => b.weight - a.weight) // Sort by weight descending
    .slice(0, 8) // Top 8 holdings for banner

  // Extract metrics
  const riskScore = metadata?.risk_score || 0
  const diversificationScore = metadata?.diversification_score || 0
  const alertsCount = metadata?.alerts_count || 0
  
  // Count unique sectors
  const sectors = new Set(holdings.map(h => h.sector).filter(Boolean))
  const sectorsCount = sectors.size

  return {
    totalValue: total_value || 0,
    pnlPercent: parseFloat(pnlPercent.toFixed(2)),
    pnlAbsolute: parseFloat(pnlAbsolute.toFixed(2)),
    holdings: bannerHoldings,
    alertsCount,
    riskScore: parseFloat(riskScore.toFixed(1)),
    diversificationScore: parseFloat(diversificationScore.toFixed(1)),
    sectorsCount
  }
}

/**
 * Highlight specific ticker in holdings array
 */
export function highlightTicker(bannerData, tickerToHighlight) {
  if (!bannerData || !tickerToHighlight) return bannerData

  return {
    ...bannerData,
    holdings: bannerData.holdings.map(h => ({
      ...h,
      isHighlighted: h.ticker === tickerToHighlight
    }))
  }
}
