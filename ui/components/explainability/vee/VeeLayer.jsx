/**
 * VEE LAYER COMPONENT
 * 
 * Main adapter that prepares VEE explainability for different chart types.
 * Routes VEE data to appropriate visual components (tooltips, badges, annotations).
 * 
 * Props:
 * - explainability: VEE explainability object { simple, technical, detailed }
 * - chartType: 'radar' | 'price' | 'risk' | 'gauge'
 * - children: Chart components to wrap
 */

'use client'

import { createContext, useContext } from 'react'

// VEE Context for child components to access explainability
const VeeContext = createContext(null)

export function useVeeContext() {
  return useContext(VeeContext)
}

export default function VeeLayer({ explainability, chartType, children }) {
  // Guard: If no explainability data, render children without VEE
  if (!explainability) {
    return <>{children}</>
  }

  // Prepare VEE data based on chart type
  const veeData = prepareVeeData(explainability, chartType)

  return (
    <VeeContext.Provider value={veeData}>
      {children}
    </VeeContext.Provider>
  )
}

// Helper: Prepare VEE data structure for each chart type
function prepareVeeData(explainability, chartType) {
  const base = {
    simple: explainability.simple || '',
    technical: explainability.technical || '',
    detailed: explainability.detailed || null,
  }

  switch (chartType) {
    case 'radar':
      return {
        ...base,
        // Factor-specific explanations (if available in detailed)
        factors: extractFactorExplanations(explainability.detailed),
      }

    case 'price':
      return {
        ...base,
        // Annotations for price events
        annotations: extractPriceAnnotations(explainability.technical),
      }

    case 'risk':
      return {
        ...base,
        // Risk component explanations
        riskBreakdown: extractRiskExplanations(explainability.detailed),
      }

    default:
      return base
  }
}

// Extract factor-specific explanations from detailed VEE
function extractFactorExplanations(detailed) {
  if (!detailed?.ranking?.stocks?.[0]?.factors) return {}

  // Map factor names to simple explanations
  // This is a placeholder - real data should come from backend
  return {
    value: 'P/E and P/B ratios indicate valuation level',
    growth: 'Earnings growth shows business expansion',
    quality: 'Profitability metrics measure business health',
    momentum: 'Price momentum indicates trend strength',
    size: 'Market capitalization reflects company scale',
    mtf: 'Multi-timeframe consensus shows technical alignment',
  }
}

// Extract price event annotations from technical VEE
function extractPriceAnnotations(technical) {
  if (!technical) return []

  // Ensure technical is a string
  const technicalText = typeof technical === 'string' 
    ? technical 
    : typeof technical === 'object' 
      ? JSON.stringify(technical) 
      : String(technical)

  // Placeholder: Parse technical text for keywords
  // Real implementation should come from backend pattern detection
  const annotations = []

  if (technicalText.toLowerCase().includes('momentum')) {
    annotations.push({
      type: 'momentum',
      label: 'Momentum Signal',
      description: 'Strong momentum detected',
    })
  }

  return annotations
}

// Extract risk component explanations
function extractRiskExplanations(detailed) {
  if (!detailed?.ranking?.stocks?.[0]?.risk) return {}

  return {
    volatility: 'Price volatility measures uncertainty',
    sector: 'Sector risk reflects industry exposure',
    liquidity: 'Liquidity risk indicates trading ease',
    concentration: 'Concentration risk shows position size',
  }
}
