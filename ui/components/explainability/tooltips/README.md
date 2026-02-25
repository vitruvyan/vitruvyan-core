# Tooltip Library - Unified Explainability System

## Overview
Centralized tooltip system extracted from production single-ticker UX (NeuralEngineUI.jsx).
Provides consistent VEE-style explanations across all nodes with global enable/disable control.

## 3 Tooltip Styles

### 1. VEE-STYLE (White bg, border, arrow)
**Used for:** Rich factor z-score explanations (momentum, trend, volatility, sentiment)

**Features:**
- White background with gray border
- Bottom-positioned arrow
- VEE structure: context → interpretation → action
- Percentile calculation: `~50 + z * 15`
- Factor-specific intelligence (RSI, MA, ATR)

**Example:**
\`\`\`jsx
import { MomentumTooltip } from '@/components/tooltips/TooltipLibrary'

<MomentumTooltip value={-0.86} ticker="MCD">
  <div className="factor-card">Momentum: -0.86</div>
</MomentumTooltip>
\`\`\`

### 2. DARK-STYLE (Gray-900 bg, simple)
**Used for:** Simple metric info, quick explanations

**Features:**
- Dark gray background
- Compact text
- Bottom-positioned arrow
- Hover-activated

**Example:**
\`\`\`jsx
import { DarkTooltip } from '@/components/tooltips/TooltipLibrary'

<DarkTooltip content="Factor difference between top and bottom ticker" />
\`\`\`

### 3. COMPOSITE-STYLE (Gray-900 bg, verdict badges)
**Used for:** Composite score explanations with Buy/Sell/Hold verdict

**Features:**
- Dark background
- Verdict-specific explanations
- Right-aligned arrow
- Shows composite score value

**Example:**
\`\`\`jsx
import { CompositeScoreTooltip } from '@/components/tooltips/TooltipLibrary'

<CompositeScoreTooltip value={0.45} label="Buy" ticker="AAPL">
  <div className="verdict-badge">BUY</div>
</CompositeScoreTooltip>
\`\`\`

## Global Toggle Control

**Power User Feature:** Disable all tooltips for cleaner UI

\`\`\`jsx
import { TooltipToggle } from '@/components/tooltips/TooltipLibrary'

// In header or neural engine section
<TooltipToggle />
\`\`\`

**State Management:**
- Uses `TooltipContext` (localStorage persistence)
- Key: `vitruvyan_tooltips_enabled`
- Default: `true`

**Manual Control:**
\`\`\`jsx
import { useTooltips } from '@/contexts/TooltipContext'

const { tooltipsEnabled, toggleTooltips } = useTooltips()

// Conditional rendering
{tooltipsEnabled && <MomentumTooltip ... />}
\`\`\`

## Available Components

### Factor Z-Score Tooltips (VEE-Style)
\`\`\`jsx
import {
  MomentumTooltip,    // RSI-based momentum (30-day price change)
  TrendTooltip,       // MA alignment (SMA 20/50/200)
  VolatilityTooltip,  // ATR-based stability
  SentimentTooltip    // News + social aggregation
} from '@/components/tooltips/TooltipLibrary'
\`\`\`

### Comparison Tooltips (Dark-Style)
\`\`\`jsx
import {
  FactorDeltaTooltip,   // Factor gap between tickers
  RankingTooltip,       // Overall ranking explanation
  DispersionTooltip     // Range/variance interpretation
} from '@/components/tooltips/TooltipLibrary'
\`\`\`

### Fundamentals Tooltips (Dark-Style)
\`\`\`jsx
import { FundamentalsTooltip } from '@/components/tooltips/TooltipLibrary'

<FundamentalsTooltip 
  metric="revenue_growth_yoy_z" 
  value={0.82} 
  ticker="AAPL" 
/>
\`\`\`

### Chart Tooltips (Multi-Factor & Risk Analysis)
\`\`\`jsx
import { 
  MultiFactorChartTooltip,   // Radar/Spider chart explanation
  RiskAnalysisTooltip,        // Individual risk metrics
  RiskLevelTooltip            // Overall risk badge
} from '@/components/tooltips/TooltipLibrary'

// Multi-Factor Radar Chart
<div className="chart-header flex items-center gap-2">
  <h3>Multi-Factor Analysis</h3>
  <MultiFactorChartTooltip />
</div>

// Risk Analysis Metrics
<div className="risk-metric">
  <span>Correlation Risk: {correlationScore}/100</span>
  <RiskAnalysisTooltip riskType="correlation" value={60.0} ticker="CINF" />
</div>

// Overall Risk Badge
<RiskLevelTooltip level="MODERATE" score={43} />
\`\`\`

## Implementation Examples

### Multi-Factor Chart (Radar/Spider Chart)
\`\`\`jsx
import { MultiFactorChartTooltip } from '@/components/tooltips/TooltipLibrary'

<div className="bg-white p-6 rounded-lg border">
  {/* Header with tooltip */}
  <div className="flex items-center justify-between mb-4">
    <div className="flex items-center gap-2">
      <h3 className="text-lg font-semibold">Multi-Factor Analysis</h3>
      <MultiFactorChartTooltip />
    </div>
    <div className="flex gap-2">
      <button className="text-sm">Chart</button>
      <button className="text-sm text-gray-500">How to Read</button>
    </div>
  </div>
  
  {/* Radar Chart */}
  <ResponsiveContainer width="100%" height={300}>
    <RadarChart data={factorData}>
      <PolarGrid />
      <PolarAngleAxis dataKey="factor" />
      <PolarRadiusAxis angle={90} domain={[0, 100]} />
      <Radar name={ticker} dataKey="value" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
    </RadarChart>
  </ResponsiveContainer>
  
  {/* Factor values */}
  <div className="grid grid-cols-3 gap-2 mt-4 text-xs">
    <div><strong>Value:</strong> 0.09</div>
    <div><strong>Growth:</strong> 0.37</div>
    <div><strong>Quality:</strong> 0.15</div>
    <div><strong>Momentum:</strong> 0.13</div>
    <div><strong>Size:</strong> 23.9B</div>
    <div><strong>MTF:</strong> 1.00</div>
  </div>
</div>
\`\`\`

### Risk Analysis Section
\`\`\`jsx
import { RiskAnalysisTooltip, RiskLevelTooltip } from '@/components/tooltips/TooltipLibrary'

<div className="bg-white p-6 rounded-lg border">
  {/* Header with overall risk badge */}
  <div className="flex items-center justify-between mb-4">
    <h3 className="text-lg font-semibold">Risk Analysis</h3>
    <div className="flex items-center gap-2">
      <div className="px-3 py-1 bg-yellow-50 border border-yellow-300 rounded-lg text-yellow-700 font-semibold">
        ⚠️ MODERATE (43/100)
      </div>
      <RiskLevelTooltip level="MODERATE" score={43} />
    </div>
  </div>
  
  {/* Risk metrics list */}
  <div className="space-y-3">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 bg-red-500 rounded-full"></div>
        <span className="text-sm">Market Risk</span>
        <RiskAnalysisTooltip riskType="market" value={43.4} ticker="CINF" />
      </div>
      <span className="font-semibold">43.4</span>
    </div>
    
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
        <span className="text-sm">Volatility Risk</span>
        <RiskAnalysisTooltip riskType="volatility" value={35.0} ticker="CINF" />
      </div>
      <span className="font-semibold">35.0</span>
    </div>
    
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
        <span className="text-sm">Liquidity Risk</span>
        <RiskAnalysisTooltip riskType="liquidity" value={42.8} ticker="CINF" />
      </div>
      <span className="font-semibold">42.8</span>
    </div>
    
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
        <span className="text-sm">Correlation Risk</span>
        <RiskAnalysisTooltip riskType="correlation" value={60.0} ticker="CINF" />
      </div>
      <span className="font-semibold text-amber-600">60.0</span>
    </div>
  </div>
  
  {/* Risk summary */}
  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800 italic">
    CINF presenta rischio moderato (punteggio: 43/100). Fattore principale: rischio di correlazione (60).
  </div>
</div>
\`\`\`

### Single-Ticker Node (VEE-Style Cards)
\`\`\`jsx
import { MomentumTooltip, TrendTooltip } from '@/components/tooltips/TooltipLibrary'

// Momentum Card
<MomentumTooltip value={neuralData[0].momentum_z} ticker={ticker}>
  <div className="factor-card bg-blue-50 border-blue-200">
    <div className="text-[10px]">Momentum</div>
    <div className="text-sm font-bold">{neuralData[0].momentum_z.toFixed(2)}</div>
  </div>
</MomentumTooltip>

// Trend Card
<TrendTooltip value={neuralData[0].trend_z} ticker={ticker}>
  <div className="factor-card bg-blue-50 border-blue-200">
    <div className="text-[10px]">Trend</div>
    <div className="text-sm font-bold">{neuralData[0].trend_z.toFixed(2)}</div>
  </div>
</TrendTooltip>
\`\`\`

### Comparison Node (Dark-Style)
\`\`\`jsx
import { FactorDeltaTooltip, DispersionTooltip } from '@/components/tooltips/TooltipLibrary'

// Factor Deltas Accordion
{Object.entries(factorDeltas).map(([factor, delta]) => (
  <div key={factor} className="flex justify-between items-center">
    <span>{formatFactorName(factor)}</span>
    <span className="flex items-center gap-2">
      {formatDelta(delta)}
      <FactorDeltaTooltip 
        factor={factor} 
        delta={delta} 
        winner="MCD" 
        loser="SBUX" 
      />
    </span>
  </div>
))}

// Score Dispersion
<DispersionTooltip range={0.2061} rangePct={20.6} />
\`\`\`

### Composite Score Badge (Composite-Style)
\`\`\`jsx
import { CompositeScoreTooltip } from '@/components/tooltips/TooltipLibrary'

<CompositeScoreTooltip 
  value={finalVerdict.composite_score} 
  label={finalVerdict.label} 
  ticker={ticker}
>
  <div className={`px-3 py-1 rounded-lg ${getVerdictColor(finalVerdict.label)}`}>
    {finalVerdict.label}
  </div>
</CompositeScoreTooltip>
\`\`\`

## Migration from Legacy Components

### Replace InfoTooltip
\`\`\`jsx
// OLD (components/common/InfoTooltip.jsx)
<InfoTooltip content="Simple text explanation" />

// NEW (TooltipLibrary)
import { DarkTooltip } from '@/components/tooltips/TooltipLibrary'
<DarkTooltip content="Simple text explanation" />
\`\`\`

### Replace inline group-hover tooltips
\`\`\`jsx
// OLD (inline in NeuralEngineUI.jsx)
<div className="group relative">
  <div>Factor Card</div>
  <div className="absolute hidden group-hover:block ...">
    Tooltip content
  </div>
</div>

// NEW (TooltipLibrary)
import { MomentumTooltip } from '@/components/tooltips/TooltipLibrary'
<MomentumTooltip value={z_score} ticker={ticker}>
  <div>Factor Card</div>
</MomentumTooltip>
\`\`\`

## Design Rationale

### Why 3 Styles?
1. **VEE-STYLE**: Rich explanations need white background for readability (200+ words)
2. **DARK-STYLE**: Simple info benefits from dark bg contrast (20-40 words)
3. **COMPOSITE-STYLE**: Verdict badges need alignment with existing UX (NeuralEngineUI)

### Why Extract from NeuralEngineUI?
- **Production-tested**: 2 months in production, zero UX complaints
- **VEE-approved**: Percentile interpretation matches VEE Engine methodology
- **Factor-specific**: RSI/MA/ATR intelligence already refined

### Why Global Toggle?
- **Power users**: Experienced traders don't need explainability
- **Mobile UX**: Reduce clutter on small screens
- **Accessibility**: Users can disable hover interactions

## Testing Checklist

- [ ] VEE-style tooltips render on factor cards
- [ ] Dark-style tooltips render on comparison accordions
- [ ] Composite-style tooltips render on verdict badges
- [ ] TooltipToggle persists state in localStorage
- [ ] tooltipsEnabled=false hides all tooltips
- [ ] Percentile calculation matches ~50 + z * 15
- [ ] Arrow positioning correct (bottom/right)
- [ ] z-index prevents tooltip clipping
- [ ] Mobile responsive (tooltip doesn't overflow viewport)

## Future Enhancements

- [ ] Tooltip animation (fade-in/slide-up)
- [ ] Accessibility: ARIA labels, keyboard navigation
- [ ] Multi-language support (IT/EN/ES)
- [ ] Tooltip position auto-detection (flip on viewport edge)
- [ ] Custom tooltip themes (light/dark/vitruvyan-accent)

## Status
✅ **Production Ready** (Dec 10, 2025)
- Extracted from NeuralEngineUI.jsx
- 3 styles unified
- Global toggle integrated
- Context persistence implemented
