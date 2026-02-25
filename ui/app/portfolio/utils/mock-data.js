/**
 * Portfolio Mock Data Generators
 * 
 * Temporary mock data for portfolio visualizations.
 * TODO: Replace with real API calls to Shadow Trading backend
 */

export function generatePerformanceData(timeframe) {
  const points = timeframe === "7D" ? 7 : timeframe === "1M" ? 30 : timeframe === "3M" ? 90 : timeframe === "1Y" ? 365 : 365
  const data = []
  let portfolioValue = 38000
  let spyValue = 38000
  let qqqValue = 38000
  
  for (let i = 0; i < points; i++) {
    portfolioValue += (Math.random() - 0.48) * 500
    spyValue += (Math.random() - 0.49) * 300
    qqqValue += (Math.random() - 0.48) * 400
    
    data.push({
      date: timeframe === "7D" ? `Day ${i+1}` : `${i+1}`,
      portfolio: Math.round(portfolioValue),
      spy: Math.round(spyValue),
      qqq: Math.round(qqqValue)
    })
  }
  
  return data
}

export function generateRiskReturnData() {
  return [
    { ticker: "AAPL", risk: 18, return: 12 },
    { ticker: "MSFT", risk: 15, return: 10 },
    { ticker: "TSLA", risk: 35, return: 25 },
    { ticker: "NVDA", risk: 28, return: 22 },
    { ticker: "GOOGL", risk: 16, return: 11 }
  ]
}

export function generateCorrelationMatrix() {
  return [
    [1.00, 0.65, 0.42, 0.71],
    [0.65, 1.00, 0.38, 0.59],
    [0.42, 0.38, 1.00, 0.55],
    [0.71, 0.59, 0.55, 1.00]
  ]
}

export function getCorrelationColor(val) {
  const intensity = Math.abs(val)
  if (intensity > 0.8) return val > 0 ? '#dc2626' : '#2563eb'
  if (intensity > 0.6) return val > 0 ? '#f97316' : '#3b82f6'
  if (intensity > 0.4) return val > 0 ? '#fbbf24' : '#60a5fa'
  return '#e5e7eb'
}

export const SECTOR_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

export function generateSectorData() {
  return [
    { name: "Technology", value: 43.4 },
    { name: "Consumer", value: 38.6 },
    { name: "Industrials", value: 18.1 }
  ]
}

export function renderCustomLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent }) {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5
  const x = cx + radius * Math.cos(-midAngle * Math.PI / 180)
  const y = cy + radius * Math.sin(-midAngle * Math.PI / 180)

  return (
    <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize={12} fontWeight="bold">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  )
}

export function generateGeoData() {
  return [
    { region: "North America", value: 85 },
    { region: "Europe", value: 10 },
    { region: "Asia", value: 5 }
  ]
}

export function generateWeightData() {
  return [
    { ticker: "AAPL", weight: 43.4 },
    { ticker: "MSFT", weight: 38.6 },
    { ticker: "TSLA", weight: 18.1 }
  ]
}

export function generateRiskRadarData() {
  return [
    { dimension: "Market Risk", value: 6 },
    { dimension: "Volatility", value: 5 },
    { dimension: "Liquidity", value: 8 },
    { dimension: "Concentration", value: 7 },
    { dimension: "Correlation", value: 6 },
    { dimension: "Drawdown", value: 4 }
  ]
}
