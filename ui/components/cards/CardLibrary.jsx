/**
 * CARD LIBRARY - Unified Export
 * Central import point for all card components
 * 
 * @file CardLibrary.jsx
 * @created Dec 11, 2025
 * @updated Dec 14, 2025 - Added ZScoreCardMulti for comparison views
 * @purpose Standardize card components across Vitruvyan UI
 * 
 * @usage
 *   import { MetricCard, ZScoreCard, ZScoreCardMulti } from '@/components/cards/CardLibrary'
 * 
 * @components
 *   - BaseCard: Foundation component (all cards extend this)
 *   - MetricCard: Color-coded metric display (8 color variants)
 *   - ZScoreCard: Z-score display with VEE tooltips (SINGLE ticker)
 *   - ZScoreCardMulti: Z-score display for MULTI-ticker comparison (NEW Dec 14)
 *   - ChartCard: Standardized chart container
 *   - AccordionCard: Collapsible sections
 * 
 * @migration
 *   - Replaces: components/common/MetricCard.jsx
 *   - Replaces: FundamentalsPanel.jsx inline FundamentalCard
 *   - Replaces: ComparisonNeuralEngineCard → ZScoreCardMulti
 *   - Replaces: 33+ inline card patterns across nodes
 */

export { default as BaseCard } from './BaseCard'
export { default as MetricCard } from './MetricCard'
export { default as ZScoreCard } from './ZScoreCard'
export { default as ZScoreCardMulti } from './ZScoreCardMulti'
export { default as ChartCard } from './ChartCard'
export { default as AccordionCard } from './AccordionCard'
