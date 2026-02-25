# Card Library - Usage Guide

## 📚 Overview

Unified card component library for Vitruvyan UI. Replaces 33+ inline card patterns with standardized, reusable components.

**Created**: December 11, 2025  
**Migration**: Replaces `components/common/MetricCard.jsx` + inline patterns

---

## 🎯 Components

### 1. **BaseCard** (Foundation)

Foundation component that all other cards extend.

\`\`\`jsx
import { BaseCard } from '@/components/cards/CardLibrary'

<BaseCard 
  variant="elevated"  // default | elevated | bordered | flat
  padding="lg"        // none | sm | md | lg | xl
  hover={true}        // Enable hover shadow
>
  <h3>Content</h3>
</BaseCard>
\`\`\`

**Props**:
- `variant`: Style variant (default: `'default'`)
- `padding`: Padding size (default: `'md'`)
- `hover`: Enable hover effects (default: `false`)
- `className`: Additional CSS classes
- `onClick`: Click handler
- `...props`: All other div props

---

### 2. **MetricCard** (Colored Metrics)

Display metrics with color-coded backgrounds.

\`\`\`jsx
import { MetricCard } from '@/components/cards/CardLibrary'
import { TrendingUp } from 'lucide-react'

<MetricCard 
  label="Revenue Growth"
  value="+12.5%"
  color="green"  // blue | purple | green | orange | red | gray | yellow | indigo
  icon={TrendingUp}
  tooltip="Year-over-year revenue growth"
  subtitle="vs last quarter"
/>
\`\`\`

**Props**:
- `label`: Metric label (string)
- `value`: Metric value (string | number)
- `color`: Color variant (8 options, default: `'blue'`)
- `icon`: Lucide icon component
- `tooltip`: Tooltip content (uses DarkTooltip)
- `subtitle`: Optional subtitle
- `className`: Additional CSS classes

**Color Variants**:
- `blue`: Default
- `purple`: Premium metrics
- `green`: Positive metrics
- `orange`: Warning metrics
- `red`: Negative metrics
- `gray`: Neutral metrics
- `yellow`: Attention metrics
- `indigo`: Special metrics

---

### 3. **ZScoreCard** (Fundamentals)

Display z-score metrics with automatic color coding + VEE tooltips.

\`\`\`jsx
import { ZScoreCard } from '@/components/cards/CardLibrary'
import { TrendingUp } from 'lucide-react'

<ZScoreCard 
  label="Revenue Growth YoY"
  value={1.23}  // z-score number
  icon={TrendingUp}
  veeSimple="Strong performance (top quartile)"
  veeTechnical="Revenue growth of 15.2% places this stock in the top 25% of its sector..."
/>
\`\`\`

**Props**:
- `label`: Metric label (string)
- `value`: Z-score number (null/undefined supported)
- `icon`: Lucide icon component
- `veeSimple`: VEE simple explanation (1 sentence)
- `veeTechnical`: VEE technical explanation (3-4 sentences)
- `className`: Additional CSS classes

**Color Coding** (automatic):
| Z-Score | Color | Emoji | Tier |
|---------|-------|-------|------|
| z > 1.5 | Green | 🚀 | Exceptional |
| z > 1.0 | Green | ✅ | Top quartile |
| z > 0.5 | Yellow | 👍 | Above average |
| z > -0.5 | Blue | 😐 | Average |
| z > -1.0 | Orange | ⚠️ | Below average |
| z < -1.0 | Red | ❌ | Bottom quartile |
| null | Gray | — | N/A |

**Replaces**: `FundamentalCard` from `FundamentalsPanel.jsx` (lines 82-130)

---

### 4. **ChartCard** (Chart Container)

Standardized container for Recharts components.

\`\`\`jsx
import { ChartCard } from '@/components/cards/CardLibrary'
import { ResponsiveContainer, LineChart } from 'recharts'

<ChartCard 
  title="Multi-Factor Analysis"
  subtitle="Last 90 days"
  headerAction={<button>Export</button>}
>
  <ResponsiveContainer width="100%" height={300}>
    <LineChart data={data}>
      {/* chart config */}
    </LineChart>
  </ResponsiveContainer>
</ChartCard>
\`\`\`

**Props**:
- `title`: Chart title (string)
- `subtitle`: Chart subtitle (string)
- `headerAction`: Action button/component
- `children`: Chart content (ResponsiveContainer)
- `className`: Additional CSS classes

**Replaces**: Inline chart containers in `NeuralEngineUI.jsx`, `ComparisonNodeUI.jsx`

---

### 5. **AccordionCard** (Collapsible Sections)

Collapsible card for sections.

\`\`\`jsx
import { AccordionCard } from '@/components/cards/CardLibrary'

<AccordionCard 
  title="Advanced Metrics"
  subtitle="7 additional factors"
  defaultOpen={false}
>
  <div>Collapsible content</div>
</AccordionCard>
\`\`\`

**Props**:
- `title`: Section title (string)
- `subtitle`: Section subtitle (string)
- `defaultOpen`: Initial state (boolean, default: `false`)
- `children`: Collapsible content
- `className`: Additional CSS classes

**Features**:
- ✅ Keyboard accessible (Enter/Space to toggle)
- ✅ Dark mode support
- ✅ Smooth transitions
- ✅ ARIA labels

---

## 🎨 Design Tokens

Centralized design system in `cardTokens.js`:

\`\`\`javascript
import { CARD_TOKENS } from '@/components/cards/CardLibrary'

// Use in custom components
const myCard = `${CARD_TOKENS.base} ${CARD_TOKENS.variants.elevated} ${CARD_TOKENS.padding.lg}`
\`\`\`

**Available Tokens**:
- `CARD_TOKENS.base`: Base styles (rounded, transitions)
- `CARD_TOKENS.variants`: Style variants (default, elevated, bordered, flat)
- `CARD_TOKENS.padding`: Padding sizes (none, sm, md, lg, xl)
- `CARD_TOKENS.zScoreColors`: Z-score color classes
- `CARD_TOKENS.metricColors`: Metric color classes
- `CARD_TOKENS.dark`: Dark mode variants

---

## 🔄 Migration Guide

### **Before** (Inline Card):
\`\`\`jsx
<div className="bg-white border border-gray-200 rounded-lg p-4">
  <h3>Section Title</h3>
  {content}
</div>
\`\`\`

### **After** (BaseCard):
\`\`\`jsx
import { BaseCard } from '@/components/cards/CardLibrary'

<BaseCard variant="elevated" padding="lg">
  <h3>Section Title</h3>
  {content}
</BaseCard>
\`\`\`

---

### **Before** (Inline Chart Container):
\`\`\`jsx
<div className="bg-white border border-gray-200 rounded-lg p-4">
  <h3>Multi-Factor Analysis</h3>
  <ResponsiveContainer>...</ResponsiveContainer>
</div>
\`\`\`

### **After** (ChartCard):
\`\`\`jsx
import { ChartCard } from '@/components/cards/CardLibrary'

<ChartCard title="Multi-Factor Analysis">
  <ResponsiveContainer>...</ResponsiveContainer>
</ChartCard>
\`\`\`

---

### **Before** (FundamentalCard Inline):
\`\`\`jsx
const FundamentalCard = ({ label, value, icon: Icon, veeSimple, veeTechnical }) => {
  // 48 lines of inline code
  return <div className={...}>...</div>
}

// Usage:
<FundamentalCard label="Revenue Growth" value={1.23} ... />
\`\`\`

### **After** (ZScoreCard):
\`\`\`jsx
import { ZScoreCard } from '@/components/cards/CardLibrary'

<ZScoreCard 
  label="Revenue Growth YoY"
  value={stock.factors?.revenue_growth_yoy_z}
  icon={TrendingUp}
  veeSimple={explainability?.revenue_growth_yoy_z?.simple}
  veeTechnical={explainability?.revenue_growth_yoy_z?.technical}
/>
\`\`\`

---

## 🌙 Dark Mode

All cards automatically support dark mode via Tailwind classes:

\`\`\`jsx
// Automatically adapts to dark mode
<BaseCard variant="elevated">
  {/* White background in light mode, gray-800 in dark mode */}
</BaseCard>
\`\`\`

**Dark Mode Classes** (automatic):
- `dark:bg-gray-800` - Background
- `dark:border-gray-700` - Border
- `dark:text-gray-300` - Text

---

## ♿ Accessibility

### **Keyboard Navigation**:
- AccordionCard: Enter/Space to toggle
- All cards: Proper focus states

### **ARIA Labels**:
- AccordionCard: `aria-expanded`, `aria-controls`
- Tooltips: Via TooltipLibrary

### **Screen Reader Support**:
- Semantic HTML (button, div with proper roles)
- Descriptive labels

---

## 📊 Migration Checklist

### **Phase 1: FundamentalsPanel** (30 min)
- [ ] Replace inline FundamentalCard with ZScoreCard
- [ ] Verify VEE tooltips working
- [ ] Test z-score color coding
- [ ] Test dark mode

### **Phase 2: ComparisonNodeUI** (1h)
- [ ] Replace inline cards with BaseCard
- [ ] Replace chart containers with ChartCard
- [ ] Test comparison table

### **Phase 3: ScreeningNodeUI** (1h)
- [ ] Replace inline cards with BaseCard
- [ ] Replace accordion sections with AccordionCard
- [ ] Test screening results display

### **Phase 4: AllocationUI** (30 min)
- [ ] Replace inline cards with BaseCard
- [ ] Test allocation weights display

### **Phase 5: Testing** (1h)
- [ ] Visual regression tests
- [ ] Dark mode verification
- [ ] Accessibility audit
- [ ] Mobile responsive tests

---

## 🎯 Benefits

✅ **Consistency**: Single source of truth for card styles  
✅ **Maintainability**: Update 1 file vs 33+ inline patterns  
✅ **Dark Mode**: Automatic support across all cards  
✅ **Accessibility**: Keyboard nav + ARIA labels built-in  
✅ **Performance**: Component reuse (smaller bundle)  
✅ **Developer Experience**: Simple API, TypeScript-ready  

---

## 📚 References

**Internal Files**:
- `CARD_COMPONENTS_AUDIT_DEC11.md` - Full audit report
- `components/common/MetricCard.jsx` - Original MetricCard (deprecated)
- `components/FundamentalsPanel.jsx` - FundamentalCard pattern (lines 82-130)

**Similar Libraries**:
- shadcn/ui Card component
- Ant Design Card
- Tailwind UI Card patterns
