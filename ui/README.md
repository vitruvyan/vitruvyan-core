# 🏛️ Vitruvyan UI — Domain-Agnostic Cognitive Interface

> **Last updated**: Feb 20, 2026

Domain-agnostic React UI framework for Vitruvyan Core. Provides reusable infrastructure (Chat, Renderer, Composites) and a plugin system for domain-specific UX.

---

## 🎯 Philosophy

Vitruvyan UI is **not** a collection of components. It is a **cognitive interface** that transforms backend epistemic state into human-understandable narratives.

**Core Principles**:
1. **Separation of Thought and Visualization** — Cognitive layer (reasoning) vs Analytical layer (data)
2. **Adapter is the UX unit** — Each scenario = one adapter (not scattered component logic)
3. **Renderer is infrastructure** — Stable, domain-agnostic, feature-blind
4. **Explainability is first-class** — VEE, tooltips, badges are not afterthoughts

**Inspired by**: [Mercator UI Constitution](https://github.com/vitruvyan/vitruvyan-ui/blob/main/🏛️%20COSTITUZIONE%20UI%20DI%20VITRUVYAN.md)

---

## 📂 Structure

```
ui/
├── contracts/                   # 📜 UI CONTRACTS (TypeScript interfaces)
│   ├── UIContract.ts            # Canonical UI payload interface
│   ├── AdapterContract.ts       # Adapter interface + registry
│   ├── DomainPluginContract.ts  # Domain plugin system
│   └── index.ts                 # Central export
│
├── components/
│   ├── adapters/                # 🎯 UX MAPPERS (Backend → UI payload)
│   │   ├── _base/               # Base adapter examples
│   │   ├── _examples/           # Domain adapter examples (finance)
│   │   └── index.js             # Adapter registry
│   │
│   ├── chat/                    # 💬 CHAT MODULE (domain-agnostic)
│   │   ├── Chat.jsx             # Main chat orchestrator (183 LOC)
│   │   ├── ChatMessage.jsx      # Message renderer (145 LOC)
│   │   ├── ChatInput.jsx        # Input field
│   │   ├── ChatMessages.jsx     # Messages list
│   │   ├── ThinkingSteps.jsx    # Thinking indicator
│   │   ├── hooks/               # Chat hooks (useChat, useMessages)
│   │   └── artifacts/           # Domain artifacts (charts, etc.)
│   │
│   ├── response/                # 🎨 RENDERING LAYER (infrastructure)
│   │   ├── VitruvyanResponseRenderer.jsx  # Main renderer (336 LOC)
│   │   ├── EvidenceSectionRenderer.jsx    # Evidence sections
│   │   └── index.js
│   │
│   ├── composites/              # 🧱 REUSABLE BLOCKS
│   │   ├── NarrativeBlock.jsx   # Narrative text block
│   │   ├── EvidenceAccordion.jsx  # Evidence accordion
│   │   ├── FollowUpChips.jsx    # Follow-up chips
│   │   ├── IntentBadge.jsx      # Intent badge
│   │   ├── FallbackMessage.jsx  # Error states
│   │   └── AdvisorInsight.jsx   # Advisor recommendation (optional)
│   │
│   ├── explainability/          # 💡 VEE + EXPLAINABILITY
│   │   ├── vee/                 # VEE components
│   │   │   ├── VEEAccordions.jsx  # Stratified explanations
│   │   │   ├── VeeAnnotation.jsx
│   │   │   ├── VeeLayer.jsx
│   │   │   └── _domain_vee/     # Domain-specific VEE content
│   │   ├── tooltips/            # Tooltip library
│   │   │   └── TooltipLibrary.jsx
│   │   └── badges/              # Semantic badges
│   │
│   ├── cards/                   # 🃏 ATOMIC COMPONENTS
│   │   ├── CardLibrary.jsx      # Card library
│   │   ├── BaseCard.jsx         # Generic card
│   │   └── MetricCard.jsx       # Metric display card
│   │
│   ├── theme/                   # 🎨 DESIGN TOKENS
│   │   └── tokens.js            # Color, spacing, typography
│   │
│   ├── layouts/                 # 📐 PAGE STRUCTURES (optional)
│   ├── ui/                      # shadcn/ui primitives (optional)
│   ├── primitives/              # Low-level components (optional)
│   └── utils/                   # Utilities
│
├── hooks/                       # 🪝 CUSTOM HOOKS
│   ├── _core/                   # Core hooks (chat, streaming, typing)
│   └── _domain/                 # Domain hooks (trading, portfolio, etc.)
│
├── contexts/                    # 🌐 REACT CONTEXTS (optional)
├── lib/                         # 🧰 UTILITIES + TYPES
└── docs/                        # 📚 DOCUMENTATION
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Core dependencies (Next.js, React, Radix UI, Tailwind)
cd ui/
npm install next react react-dom
npm install @radix-ui/react-accordion @radix-ui/react-dialog
npm install lucide-react tailwindcss
```

### 2. Register Adapters

```javascript
// app/layout.js (Next.js) or index.js (Vite/CRA)
import { adapterRegistry } from '@/ui/contracts'
import { ConversationalAdapter } from '@/ui/components/adapters'

// Register core adapter
adapterRegistry.register(new ConversationalAdapter())
```

### 3. Use Chat Component

```javascript
// app/page.js
import Chat from '@/ui/components/chat/Chat'

export default function HomePage() {
  return (
    <div className="container">
      <Chat
        initialQuestion="Hello, Vitruvyan!"
        initialTickers={[]}
        onAnalysisComplete={(state) => console.log('Analysis done:', state)}
      />
    </div>
  )
}
```

### 4. Create Domain Adapter (Optional)

```javascript
// vitruvyan_core/domains/finance/ui/adapters/FinanceSingleTickerAdapter.js
import { BaseAdapter } from '@/ui/contracts'

export class FinanceSingleTickerAdapter extends BaseAdapter {
  name = 'finance_single_ticker'

  map(state) {
    return {
      narrative: this.buildNarrative(state.can_response.narrative),
      followUps: this.buildFollowUps([...]),
      evidence: { sections: [...] },
      vee_explanations: this.buildVEE(...),
      context: this.buildContext('single_ticker', state.tickers)
    }
  }
}

// Register
adapterRegistry.register(new FinanceSingleTickerAdapter())
```

---

## 📜 Contracts

All UI code **MUST** conform to the three core contracts:

### 1. UIContract

Defines the canonical payload structure consumed by the renderer.

```typescript
interface UIResponsePayload {
  narrative: NarrativePayload      // Layer 1: Natural language response
  followUps: FollowUpPayload[]     // Layer 2: Suggested questions
  evidence: EvidencePayload         // Layer 3: Structured data (accordions)
  vee_explanations: VEEPayload      // Layer 4: Explainability (VEE)
  context: ContextPayload           // Metadata
  [key: string]: any                // Domain extensions
}
```

### 2. AdapterContract

Every adapter transforms backend state → UIResponsePayload.

```typescript
interface AdapterContract {
  name: string
  map(state: any): UIResponsePayload
  validate?(payload: UIResponsePayload): ValidationResult
  metadata?: AdapterMetadata
}
```

### 3. DomainPluginContract

Domains extend UI via plugins (adapters + VEE + hooks + theme).

```typescript
interface DomainPluginContract {
  metadata: DomainPluginMetadata
  adapters: AdapterContract[]
  vee_content?: VEEContentRegistry
  hooks?: Record<string, Function>
  theme_overrides?: Partial<ThemeTokens>
}
```

**Read full contracts**: [ui/contracts/](contracts/)

---

## 🏗️ Architecture

### Flow

```
Backend (LangGraph)
  ↓
finalState (BaseGraphState)
  ↓
Adapter.map(finalState)  ← Domain-specific transformation
  ↓
UIResponsePayload        ← Canonical UI payload (UIContract)
  ↓
VitruvyanResponseRenderer.jsx  ← Infrastructure (domain-agnostic)
  ↓
User sees:
  1. Narrative (VEE Summary)
  2. Follow-up chips
  3. Evidence accordions (collapsed by default)
  4. VEE deep dive (optional)
```

### Adapter Pattern

**Adapters are the UX units**. Each conversation type has one adapter:

| Conversation Type | Adapter | Domain |
|-------------------|---------|--------|
| `conversational` | ConversationalAdapter | generic |
| `single_ticker` | FinanceSingleTickerAdapter | finance |
| `comparison` | FinanceComparisonAdapter | finance |
| `allocation` | FinanceAllocationAdapter | finance |
| `screening` | FinanceScreeningAdapter | finance |
| `energy_grid` | EnergyGridAdapter | energy |
| `facility_mgmt` | FacilityAdapter | facility |

**Adding a new UX = adding a new adapter** (not scattering logic across components).

### Renderer Stability

The renderer (`VitruvyanResponseRenderer.jsx`) is **infrastructure**:
- NO business logic
- NO domain knowledge
- NO feature-specific checks

If you need to modify the renderer for a new feature, **the architecture is wrong**. Create a new adapter or extend the contract instead.

---

## 🎨 Design System

### Theme Tokens

All styling derives from `components/theme/tokens.js`:

```javascript
export const tokens = {
  colors: {
    vitruvyan: {
      bg: 'bg-white',
      border: 'border-gray-200',
      text: 'text-gray-900'
    },
    metrics: {
      blue: 'bg-blue-50 border-blue-200 text-blue-900',
      green: 'bg-green-50 border-green-200 text-green-900',
      orange: 'bg-orange-50 border-orange-200 text-orange-900',
      red: 'bg-red-50 border-red-200 text-red-900',
      gray: 'bg-gray-50 border-gray-200 text-gray-900'
    }
  },
  spacing: {
    card: 'p-6',
    section: 'mb-4',
    metric: 'p-4'
  },
  radius: {
    card: 'rounded-lg',
    metric: 'rounded-md'
  }
}
```

**Rule**: NEVER hardcode colors/spacing. Always use tokens.

### Cards

Import from `CardLibrary.jsx`:

```javascript
import { BaseCard, MetricCard } from '@/ui/components/cards/CardLibrary'

<MetricCard
  label="Revenue Growth"
  value="+12.5%"
  color="green"
  tooltip="YoY revenue growth"
/>
```

### VEE (Explainability)

VEE = Vitruvyan Explainability Engine. Stratified explanations:

```javascript
import VEEAccordions from '@/ui/components/explainability/vee/VEEAccordions'

<VEEAccordions
  vee={{
    technical: "Technical explanation (for experts)",
    detailed: "Detailed explanation (for informed users)",
    contextualized: "Simple explanation (for everyone)"
  }}
/>
```

---

## 🧩 Domain Plugin System

Domains extend the UI via plugins without modifying core code.

### Example: Finance Plugin

```javascript
// vitruvyan_core/domains/finance/ui/plugin.js
import { FinanceSingleTickerAdapter } from './adapters/FinanceSingleTickerAdapter'
import { financeVEEContent } from './vee_content'
import { domainPluginRegistry } from '@/ui/contracts'

const financeUIPlugin = {
  metadata: {
    id: 'finance-ui-plugin',
    name: 'Finance UI Plugin',
    domain: 'finance',
    version: '1.0.0',
    description: 'Finance-specific UI components and adapters',
    author: 'vitruvyan-finance'
  },
  adapters: [
    new FinanceSingleTickerAdapter(),
    new FinanceComparisonAdapter(),
    new FinanceAllocationAdapter()
  ],
  vee_content: financeVEEContent,
  hooks: {
    useTradingOrder: () => { /* ... */ },
    usePortfolioCanvas: () => { /* ... */ }
  },
  theme_overrides: {
    colors: {
      primary: '#10b981' // Green for finance
    }
  }
}

// Register plugin
domainPluginRegistry.register(financeUIPlugin)
```

### Plugin Lifecycle

1. **Init**: Plugin loaded, adapters registered, VEE content indexed
2. **Runtime**: Adapters called based on conversation type
3. **Cleanup**: Plugin unloaded (optional)

---

## 📚 Documentation

- **Contracts**: [ui/contracts/](contracts/) — TypeScript interfaces
- **Adapter Pattern**: [ui/components/adapters/_base/BaseAdapterExample.js](components/adapters/_base/BaseAdapterExample.js)
- **Finance Example**: [ui/components/adapters/_examples/FinanceSingleTickerAdapter.js](components/adapters/_examples/FinanceSingleTickerAdapter.js)
- **Chat Module**: [ui/components/chat/](components/chat/)
- **Renderer**: [ui/components/response/VitruvyanResponseRenderer.jsx](components/response/VitruvyanResponseRenderer.jsx)
- **Mercator Constitution** (inspiration): [🏛️ COSTITUZIONE UI DI VITRUVYAN.md](../docs/COSTITUZIONE_UI.md)

---

## 🛠️ Development

### File Naming

- React components: `PascalCase.jsx` (e.g., `Chat.jsx`, `NarrativeBlock.jsx`)
- Utilities/helpers: `camelCase.js` (e.g., `tokens.js`, `veeUtils.js`)
- Contracts: `PascalCase.ts` (e.g., `UIContract.ts`, `AdapterContract.ts`)

### Import Paths

Prefer absolute imports from `@/ui/`:

```javascript
// ✅ CORRECT
import { adapterRegistry } from '@/ui/contracts'
import Chat from '@/ui/components/chat/Chat'

// ❌ WRONG
import { adapterRegistry } from '../../../contracts'
import Chat from '../components/chat/Chat'
```

### Testing

```bash
# Unit tests (components)
npm test

# Integration tests (adapters)
npm test adapters

# E2E tests (full flow)
npm test e2e
```

---

## 🤝 Contributing

### Adding a New Adapter

1. Create adapter class extending `BaseAdapter`
2. Implement `map(state)` → `UIResponsePayload`
3. Register in `adapterRegistry`
4. Add VEE content (if domain-specific)
5. Write tests

### Adding a New Component

1. Create component in appropriate directory (composites, cards, etc.)
2. Use theme tokens (NO hardcoded styles)
3. Make it domain-agnostic (NO business logic)
4. Export from index.js

### Deprecating Code

DO NOT delete. Move to `_deprecated/` with reason:

```javascript
// components/composites/_deprecated/OldComponent.jsx
/**
 * DEPRECATED: Jan 15, 2026
 * Reason: Replaced by NarrativeBlock.jsx (unified pattern)
 * Remove after: Feb 15, 2026
 */
```

---

## 📖 References

- **Mercator UI** (inspiration): https://github.com/vitruvyan/vitruvyan-ui
- **Vitruvyan Core**: [../README.md](../README.md)
- **Sacred Orders Pattern**: [../vitruvyan_core/core/governance/SACRED_ORDER_PATTERN.md](../vitruvyan_core/core/governance/SACRED_ORDER_PATTERN.md)
- **Radix UI**: https://www.radix-ui.com/
- **Tailwind CSS**: https://tailwindcss.com/

---

## 📝 License

Same as vitruvyan-core (see [../LICENSE.md](../LICENSE.md))

---

**Last updated**: Feb 20, 2026  
**Status**: ✅ Foundation complete — Ready for domain plugin development  
**Next**: Implement finance plugin, energy plugin, facility plugin
