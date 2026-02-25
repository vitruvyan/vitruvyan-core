# Vitruvyan Design System - Semitransparent Palette

**Philosophy**: Utilizziamo colori semitrasparenti per creare un'interfaccia elegante, ariosa e professionale che mantiene coerenza visiva in tutto il sito.

---

## 🎨 Color Palette (Semitransparent)

### ✅ Success/Positive (Green)
**Usage**: Winner, positive z-scores, upward trends, buy signals
```jsx
// Background
className="bg-[rgba(34,197,94,0.08)]"
// With border
className="bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.20)]"
// Text
className="text-[rgba(22,163,74,1)]"
// Hover
className="hover:bg-[rgba(34,197,94,0.12)]"
```

### ⚠️ Warning/Neutral (Amber/Yellow)
**Usage**: Moderate risk, neutral signals, caution areas
```jsx
// Background
className="bg-[rgba(245,158,11,0.08)]"
// With border
className="bg-[rgba(245,158,11,0.08)] border border-[rgba(245,158,11,0.20)]"
// Text
className="text-[rgba(217,119,6,1)]"
// Hover
className="hover:bg-[rgba(245,158,11,0.12)]"
```

### ❌ Danger/Negative (Red)
**Usage**: Loser, negative z-scores, downward trends, sell signals
```jsx
// Background
className="bg-[rgba(239,68,68,0.08)]"
// With border
className="bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.20)]"
// Text
className="text-[rgba(220,38,38,1)]"
// Hover
className="hover:bg-[rgba(239,68,68,0.12)]"
```

### ℹ️ Info/Neutral (Blue)
**Usage**: Informational cards, technical data, momentum indicators
```jsx
// Background
className="bg-[rgba(59,130,246,0.08)]"
// With border
className="bg-[rgba(59,130,246,0.08)] border border-[rgba(59,130,246,0.20)]"
// Text
className="text-[rgba(37,99,235,1)]"
// Hover
className="hover:bg-[rgba(59,130,246,0.12)]"
```

### 👑 Premium/Featured (Purple)
**Usage**: Premium features, VEE insights, special highlights
```jsx
// Background
className="bg-[rgba(168,85,247,0.08)]"
// With border
className="bg-[rgba(168,85,247,0.08)] border border-[rgba(168,85,247,0.20)]"
// Text
className="text-[rgba(147,51,234,1)]"
// Hover
className="hover:bg-[rgba(168,85,247,0.12)]"
```

### ⚪ Neutral (Gray)
**Usage**: Default cards, secondary information, disabled states
```jsx
// Background
className="bg-[rgba(115,115,115,0.05)]"
// With border
className="bg-[rgba(115,115,115,0.05)] border border-[rgba(115,115,115,0.15)]"
// Text
className="text-[rgba(82,82,82,1)]"
// Hover
className="hover:bg-[rgba(115,115,115,0.08)]"
```

---

## 📐 Component Guidelines

### Comparison Cards (Winner/Loser)
```jsx
// Winner (Green semitransparent)
<div className="bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.20)] rounded-lg p-4">
  <span className="text-[rgba(22,163,74,1)] font-semibold">TSLA - Winner</span>
</div>

// Loser (Red semitransparent)
<div className="bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.20)] rounded-lg p-4">
  <span className="text-[rgba(220,38,38,1)] font-semibold">ABAT - Loser</span>
</div>
```

### Risk Badges
```jsx
// High Risk (Red)
<span className="bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.20)] text-[rgba(220,38,38,1)] px-3 py-1 rounded-full text-sm font-medium">
  High Risk
</span>

// Moderate Risk (Amber)
<span className="bg-[rgba(245,158,11,0.08)] border border-[rgba(245,158,11,0.20)] text-[rgba(217,119,6,1)] px-3 py-1 rounded-full text-sm font-medium">
  Moderate Risk
</span>

// Low Risk (Green)
<span className="bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.20)] text-[rgba(22,163,74,1)] px-3 py-1 rounded-full text-sm font-medium">
  Low Risk
</span>
```

### Z-Score Cards (Factor Analysis)
```jsx
// Positive z-score (Green)
<div className="bg-[rgba(34,197,94,0.08)] border border-[rgba(34,197,94,0.20)] rounded-lg p-3">
  <div className="text-xs text-gray-600">Momentum</div>
  <div className="text-lg font-bold text-[rgba(22,163,74,1)]">+0.12</div>
</div>

// Negative z-score (Red)
<div className="bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.20)] rounded-lg p-3">
  <div className="text-xs text-gray-600">Sentiment</div>
  <div className="text-lg font-bold text-[rgba(220,38,38,1)]">-3.56</div>
</div>

// Neutral z-score (Gray)
<div className="bg-[rgba(115,115,115,0.05)] border border-[rgba(115,115,115,0.15)] rounded-lg p-3">
  <div className="text-xs text-gray-600">Trend</div>
  <div className="text-lg font-bold text-[rgba(82,82,82,1)]">-0.99</div>
</div>
```

### Composite Score Card
```jsx
// Bottom quartile (Red)
<div className="bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.20)] rounded-lg p-4">
  <div className="text-sm text-gray-600">Composite Score</div>
  <div className="text-2xl font-bold text-[rgba(220,38,38,1)]">-2.15</div>
  <div className="text-xs text-[rgba(220,38,38,1)]">Bottom quartile</div>
</div>
```

---

## 🔄 Migration Checklist

### High Priority (User-Facing)
- [x] tailwind.config.js - Added semitransparent palette
- [ ] ComparisonSentimentCard.jsx - Winner/Loser backgrounds
- [ ] ComparisonNodeUI.jsx - Ticker pills
- [ ] RiskComparisonNodeUI.jsx - Risk badges
- [ ] ZScoreCard components - Factor cards
- [ ] ComparisonCompositeScoreCard.jsx - Composite score

### Medium Priority
- [ ] RiskBreakdownChart.jsx - Risk level badges
- [ ] MetricsHeatmap.jsx - Cell backgrounds
- [ ] MiniRadarGrid.jsx - Border colors
- [ ] FactorRadarChart.jsx - Background

### Low Priority
- [ ] Paywall modal - Feature highlights
- [ ] Charts legend colors

---

## 📏 Design Principles

1. **Consistency**: Always use the same color for the same meaning (red=negative, green=positive)
2. **Transparency**: Use 8% for backgrounds, 20% for borders, 100% for text
3. **Hover States**: Increase background opacity to 12% on hover
4. **Accessibility**: Ensure text contrast ratio >4.5:1 for WCAG AA compliance
5. **Layering**: Semitransparent colors allow layering without visual clutter

---

**Last Updated**: Dec 21, 2025
**Status**: ✅ Active - Gradual migration in progress
