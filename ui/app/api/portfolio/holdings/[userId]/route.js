/**
 * Portfolio Holdings API - REAL DATABASE VERSION (Feb 4, 2026)
 * GET /api/portfolio/holdings/:userId
 * 
 * Fetches from PostgreSQL shadow_positions table (real portfolio data)
 * Fallback to mock data for demo users (default_user, test_user, etc.)
 */

import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

// Load portfolio_mock.json from backend repo (fallback only)
const MOCK_FILE_PATH = path.join(process.cwd(), '..', 'core', 'data', 'portfolio_mock.json')

// Sector mapping (from portfolio_analysis_node.py)
const SECTOR_MAPPING = {
  "AAPL": "Technology",
  "MSFT": "Technology",
  "GOOGL": "Communication Services",
  "AMZN": "Consumer Cyclical",
  "TSLA": "Consumer Cyclical",
  "NVDA": "Technology",
  "META": "Communication Services",
  "SHOP": "Technology",
  "PLTR": "Technology",
  "COIN": "Financial Services",
  "AMD": "Technology"
}

function calculatePortfolioMetrics(holdings) {
  // Calculate total value and P&L
  let totalValue = 0
  let totalCost = 0
  
  const enrichedHoldings = holdings.map(holding => {
    // Handle both formats: mock (shares, entry_price) and real DB (quantity, cost_basis)
    const shares = holding.quantity || holding.shares
    const costBasis = holding.cost_basis || holding.entry_price
    const currentPrice = holding.current_price || holding.price || 0
    
    const currentValue = shares * currentPrice
    const totalCostBasis = holding.total_cost || (shares * costBasis)
    const pnlAbsolute = currentValue - totalCostBasis
    const pnlPercent = costBasis > 0 ? ((currentPrice - costBasis) / costBasis) * 100 : 0
    
    totalValue += currentValue
    totalCost += totalCostBasis
    
    return {
      ticker: holding.ticker,
      shares: shares,
      cost_basis: costBasis,
      current_price: currentPrice,
      pnlPercent,
      pnlAbsolute,
      currentValue,
      sector: SECTOR_MAPPING[holding.ticker] || 'Other'
    }
  })
  
  // Calculate weights
  enrichedHoldings.forEach(holding => {
    holding.weight = (holding.currentValue / totalValue) * 100
  })
  
  // Sort by weight descending
  enrichedHoldings.sort((a, b) => b.weight - a.weight)
  
  // Calculate portfolio-level metrics
  const totalPnl = totalValue - totalCost
  const totalPnlPercent = ((totalValue - totalCost) / totalCost) * 100
  
  // Simple risk score (concentration risk)
  const topHoldingWeight = enrichedHoldings[0]?.weight || 0
  const riskScore = topHoldingWeight > 40 ? 75 : topHoldingWeight > 30 ? 60 : 45
  
  // Diversification score (number of holdings)
  const diversificationScore = Math.min(enrichedHoldings.length / 10, 1.0)
  
  return {
    total_value: totalValue,
    holdings: enrichedHoldings,
    risk_score: riskScore,
    diversification_score: diversificationScore,
    total_pnl_absolute: totalPnl,
    total_pnl_percent: totalPnlPercent
  }
}

export async function GET(request, { params }) {
  try {
    // Next.js 15 requires await params (Feb 4, 2026)
    const resolvedParams = await params
    const { userId } = resolvedParams
    
    console.log('[Portfolio API] GET request for userId:', userId)
    
    // Extract Authorization token from request headers (Feb 4, 2026)
    const authHeader = request.headers.get('authorization')
    
    // Check if UUID format (real user) vs demo username
    const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(userId)
    
    if (isUUID) {
      // ✅ REAL USER - Query Shadow Trading API (GET /portfolio/{user_id})
      console.log('[Portfolio API] Querying Shadow Trading API for UUID:', userId)
      
      if (!authHeader) {
        console.warn('[Portfolio API] Missing Authorization header')
        // Return empty portfolio instead of error (user may not be logged in)
        return NextResponse.json({
          status: 'success',
          data: {
            user_id: userId,
            total_value: 0,
            holdings: [],
            risk_score: 0,
            diversification_score: 0,
            total_pnl_absolute: 0,
            total_pnl_percent: 0,
            created_at: new Date().toISOString()
          }
        })
      }
      
      try {
        const pgResponse = await fetch(`http://161.97.140.157:8025/portfolio/${userId}`, {
          method: 'GET',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': authHeader // Pass JWT token
          }
        })
        
        if (!pgResponse.ok) {
          throw new Error(`Shadow Trading API error: ${pgResponse.status}`)
        }
        
        const pgData = await pgResponse.json()
        
        // Check if empty portfolio
        if (!pgData.positions || pgData.positions.length === 0) {
          console.log('[Portfolio API] Empty portfolio for user:', userId)
          return NextResponse.json({
            status: 'success',
            data: {
              user_id: userId,
              total_value: pgData.cash_balance || 0,
              holdings: [],
              cash: pgData.cash_balance || 0,
              risk_score: 0,
              diversification_score: 0,
              total_pnl_absolute: pgData.total_pnl || 0,
              total_pnl_percent: 0,
              created_at: new Date().toISOString()
            }
          })
        }
        
        // Adapt Shadow Trading API format (positions) to frontend format (holdings)
        // Shadow Trading: { ticker, quantity, cost_basis, current_price, ... }
        // Frontend needs: { ticker, shares, cost_basis, current_price, ... }
        const adaptedPositions = pgData.positions.map(pos => ({
          ticker: pos.ticker,
          quantity: pos.quantity || pos.shares,  // quantity from DB
          cost_basis: pos.cost_basis || pos.entry_price,
          current_price: pos.current_price || pos.price || 0,
          total_cost: pos.total_cost || (pos.quantity * pos.cost_basis)
        }))
        
        // Enrich with metrics
        const metrics = calculatePortfolioMetrics(adaptedPositions)
        
        console.log('[Portfolio API] Shadow Trading portfolio loaded:', metrics.holdings.length, 'holdings')
        
        return NextResponse.json({
          status: 'success',
          data: {
            user_id: userId,
            ...metrics,
            cash: pgData.cash_balance || 0,
            unrealized_pnl: pgData.unrealized_pnl || 0,
            created_at: new Date().toISOString()
          }
        })
        
      } catch (dbError) {
        console.error('[Portfolio API] PostgreSQL query failed:', dbError)
        // Return empty portfolio instead of error (user may not have portfolio yet)
        return NextResponse.json({
          status: 'success',
          data: {
            user_id: userId,
            total_value: 0,
            holdings: [],
            risk_score: 0,
            diversification_score: 0,
            total_pnl_absolute: 0,
            total_pnl_percent: 0,
            created_at: new Date().toISOString()
          }
        })
      }
    }
    
    // ⚠️ DEMO USER - Use mock data (legacy support)
    console.log('[Portfolio API] Using mock data for demo user:', userId)
    const mappedUserId = userId === 'beta_user_01' ? 'default_user' : userId
    
    // Load portfolio_mock.json
    let portfolioData
    try {
      const fileContent = fs.readFileSync(MOCK_FILE_PATH, 'utf-8')
      portfolioData = JSON.parse(fileContent)
    } catch (error) {
      console.error('[Portfolio API] Error loading portfolio_mock.json:', error)
      return NextResponse.json({
        status: 'error',
        message: 'Portfolio data not available'
      }, { status: 500 })
    }
    
    // Check if user exists
    if (!portfolioData[mappedUserId]) {
      console.log('[Portfolio API] User not found:', mappedUserId)
      return NextResponse.json({
        status: 'error',
        message: `User ${mappedUserId} not found. Available: ${Object.keys(portfolioData).join(', ')}`
      }, { status: 404 })
    }
    
    const userHoldings = portfolioData[mappedUserId].holdings
    
    // Calculate metrics
    const metrics = calculatePortfolioMetrics(userHoldings)
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300))

    console.log('[Portfolio API] Returning portfolio for user:', mappedUserId, 'Holdings:', metrics.holdings.length)

    // Return enriched data
    return NextResponse.json({
      status: 'success',
      data: {
        user_id: userId,
        ...metrics,
        created_at: new Date().toISOString()
      }
    })
  } catch (error) {
    return NextResponse.json(
      { status: 'error', message: error.message },
      { status: 500 }
    )
  }
}
