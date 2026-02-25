/**
 * ZSCORE CARD COMPONENT TESTS
 * Test suite for Card Library ZScoreCard component
 * 
 * @file ZScoreCard.test.jsx
 * @created Dec 11, 2025
 * @purpose Validate ZScoreCard rendering, color coding, VEE tooltips
 */

import { render, screen } from '@testing-library/react'
import { TrendingUp } from 'lucide-react'
import ZScoreCard from '@/components/cards/ZScoreCard'

describe('ZScoreCard Component', () => {
  test('renders with positive z-score', () => {
    render(
      <ZScoreCard
        label="Revenue Growth"
        value={1.23}
        icon={TrendingUp}
        veeSimple="Strong performance"
        veeTechnical="Revenue growth places stock in top quartile"
      />
    )
    
    expect(screen.getByText('Revenue Growth')).toBeInTheDocument()
    expect(screen.getByText('+1.23')).toBeInTheDocument()
    expect(screen.getByText('✅')).toBeInTheDocument() // z > 1.0
    expect(screen.getByText('Top quartile')).toBeInTheDocument()
  })

  test('renders with negative z-score', () => {
    render(
      <ZScoreCard
        label="EPS Growth"
        value={-1.5}
        icon={TrendingUp}
        veeSimple="Weak performance"
        veeTechnical="EPS decline signals challenges"
      />
    )
    
    expect(screen.getByText('EPS Growth')).toBeInTheDocument()
    expect(screen.getByText('-1.50')).toBeInTheDocument()
    expect(screen.getByText('❌')).toBeInTheDocument() // z < -1.0
    expect(screen.getByText('Bottom quartile')).toBeInTheDocument()
  })

  test('renders with null value', () => {
    render(
      <ZScoreCard
        label="Dividend Yield"
        value={null}
        icon={TrendingUp}
        veeSimple="No data"
        veeTechnical="Data not available"
      />
    )
    
    expect(screen.getByText('Dividend Yield')).toBeInTheDocument()
    expect(screen.getByText('N/A')).toBeInTheDocument()
    expect(screen.getByText('—')).toBeInTheDocument() // null emoji
  })

  test('applies correct color for exceptional z-score', () => {
    const { container } = render(
      <ZScoreCard
        label="Net Margin"
        value={1.8}
        icon={TrendingUp}
        veeSimple="Exceptional"
        veeTechnical="Top 7% performance"
      />
    )
    
    const card = container.firstChild
    expect(card).toHaveClass('text-green-700', 'bg-green-50', 'border-green-200')
    expect(screen.getByText('🚀')).toBeInTheDocument() // z > 1.5
  })

  test('VEE tooltip content is present', () => {
    render(
      <ZScoreCard
        label="FCF"
        value={0.7}
        icon={TrendingUp}
        veeSimple="Above average cash flow"
        veeTechnical="Free cash flow enables capital allocation flexibility"
      />
    )
    
    // VEE tooltip should contain explanations (hidden by default, shown on hover)
    expect(screen.getByText('Above average cash flow')).toBeInTheDocument()
    expect(screen.getByText(/Free cash flow enables/)).toBeInTheDocument()
  })
})
