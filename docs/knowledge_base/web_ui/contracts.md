---
tags:
  - web-ui
  - api
  - governance
---

# Web UI Contracts — TypeScript Interface Documentation

> **Last updated**: Feb 20, 2026 21:20 UTC  
> **Location**: `ui/contracts/`  
> **Purpose**: Canonical payload structure + adapter system + domain plugin interfaces

---

## Overview

The Vitruvyan Web UI contract system defines **3 core TypeScript interfaces** that enforce separation of concerns between backend, adapters, and UI:

| Contract | Purpose | File |
|----------|---------|------|
| **UIContract** | Canonical payload consumed by renderer | `UIContract.ts` (195 LOC) |
| **AdapterContract** | Backend state → UI transformation | `AdapterContract.ts` (260 LOC) |
| **DomainPluginContract** | Domain extension mechanism | `DomainPluginContract.ts` (274 LOC) |

**Total**: 820 lines of TypeScript

---

## 1. UIContract — Canonical Payload Structure

### Purpose
Defines the **single source of truth** for all UI payloads consumed by `VitruvyanResponseRenderer`.

### File
`ui/contracts/UIContract.ts` (195 lines)

### Core Interface: `UIResponsePayload`

```typescript
export interface UIResponsePayload {
  narrative: NarrativeBlock | null;
  followUps: FollowUpChips | null;
  evidence: EvidenceSection[] | null;
  vee_explanations: VEEExplanations | null;
  context: ContextMetadata | null;
}
```

### Sub-Interfaces

#### `NarrativeBlock`
High-level summary with optional VEE annotation.

```typescript
export interface NarrativeBlock {
  text: string;               // Markdown-formatted summary (100-300 words)
  vee_key?: string;           // Optional VEE key for explainability
  intent_badge?: IntentBadge; // Intent classification display
}
```

**Example**:
```typescript
{
  text: "Apple Inc. (AAPL) shows strong fundamentals with a Solidità score of +2.3σ above sector median.",
  vee_key: "vee_summary_finance_ticker",
  intent_badge: { label: "Finance Analysis", color: "green" }
}
```

---

#### `FollowUpChips`
Interactive follow-up suggestion chips.

```typescript
export interface FollowUpChips {
  chips: Array<{
    text: string;
    action?: "query" | "navigate" | "drill_down";
    payload?: any;
  }>;
}
```

**Example**:
```typescript
{
  chips: [
    { text: "Compare with sector peers", action: "query", payload: { sector: "tech" } },
    { text: "Historical trend analysis", action: "drill_down" },
    { text: "Show risk factors", action: "navigate", payload: { section: "risk" } }
  ]
}
```

---

#### `EvidenceSection`
Collapsible accordion with metric cards.

```typescript
export interface EvidenceSection {
  title: string;              // Section title (e.g., "Solidità — Balance Sheet")
  subtitle?: string;          // Optional subtitle
  cards: MetricCard[];        // Array of metric cards
  vee_key?: string;           // Optional VEE for section-level explanation
  epistemic_order?: number;   // Epistemological priority (1 = highest)
}

export interface MetricCard {
  label: string;              // Metric name (e.g., "Debt-to-Equity Ratio")
  value: string | number;     // Display value (e.g., "0.45" or "$12.5B")
  unit?: string;              // Optional unit (e.g., "%", "B", "x")
  trend?: "up" | "down" | "neutral"; // Trend indicator
  severity?: "positive" | "negative" | "neutral"; // Color coding
  vee_key?: string;           // VEE key for metric-level explanation
  metadata?: Record<string, any>; // Arbitrary metadata
}
```

**Example**:
```typescript
{
  title: "Solidità — Balance Sheet Strength",
  subtitle: "Leverage and liquidity metrics",
  epistemic_order: 1,
  vee_key: "vee_solidita_section",
  cards: [
    {
      label: "Debt-to-Equity",
      value: 0.45,
      unit: "x",
      trend: "down",
      severity: "positive",
      vee_key: "vee_debt_equity_ratio"
    },
    {
      label: "Current Ratio",
      value: 2.1,
      unit: "x",
      trend: "up",
      severity: "positive",
      vee_key: "vee_current_ratio"
    }
  ]
}
```

---

#### `VEEExplanations`
Three-level explainability registry.

```typescript
export interface VEEExplanations {
  [vee_key: string]: {
    technical: string;        // 5-15s read (for engineers)
    detailed: string;         // 30-60s read (for analysts)
    contextualized: string;   // 120-180s read (for domain experts)
  };
}
```

**Example**:
```typescript
{
  "vee_debt_equity_ratio": {
    technical: "Ratio of total liabilities to shareholder equity. Formula: Total Debt / Total Equity.",
    detailed: "Measures financial leverage. Lower values indicate conservative capital structure. Sector median is 0.8x.",
    contextualized: "A 0.45x ratio suggests the company is underleveraged compared to peers. This provides flexibility in economic downturns but may indicate underutilized capital. Cross-reference with ROE and WACC to assess capital efficiency."
  }
}
```

---

#### `ContextMetadata`
Additional context for the response.

```typescript
export interface ContextMetadata {
  intent?: string;
  domain?: string;
  conversation_id?: string;
  timestamp?: string;
  advisor?: {
    text: string;
    severity: "info" | "warning" | "critical";
  };
  debug?: Record<string, any>;
}
```

**Example**:
```typescript
{
  intent: "finance_single_ticker",
  domain: "finance",
  conversation_id: "conv_1234",
  timestamp: "2026-02-20T21:00:00Z",
  advisor: {
    text: "This analysis uses data as of market close 2026-02-19. Macroeconomic events may impact valuations.",
    severity: "info"
  }
}
```

---

### Exported Types

```typescript
export type {
  UIResponsePayload,
  NarrativeBlock,
  FollowUpChips,
  EvidenceSection,
  MetricCard,
  VEEExplanations,
  ContextMetadata,
  IntentBadge
};
```

---

## 2. AdapterContract — Transformation Interface

### Purpose
Defines the adapter interface that transforms backend `LangGraphFinalState` into `UIResponsePayload`.

### File
`ui/contracts/AdapterContract.ts` (260 lines)

### Core Abstract Class: `BaseAdapter`

```typescript
export abstract class BaseAdapter {
  abstract conversationType: string;

  /**
   * Check if this adapter should handle the conversation
   */
  abstract match(conversation: ConversationType): boolean;

  /**
   * Transform backend state into UI payload
   */
  abstract map(state: LangGraphFinalState): UIResponsePayload;

  /**
   * Helper: Build narrative block
   */
  protected buildNarrative(
    text: string,
    vee_key?: string,
    intent_badge?: IntentBadge
  ): NarrativeBlock {
    return { text, vee_key, intent_badge };
  }

  /**
   * Helper: Build follow-up chips
   */
  protected buildFollowUps(chips: string[]): FollowUpChips {
    return {
      chips: chips.map(text => ({ text, action: "query" }))
    };
  }

  /**
   * Helper: Build evidence section
   */
  protected buildEvidenceSection(
    title: string,
    cards: MetricCard[],
    options?: {
      subtitle?: string;
      vee_key?: string;
      epistemic_order?: number;
    }
  ): EvidenceSection {
    return { title, cards, ...options };
  }

  /**
   * Helper: Build VEE explanations
   */
  protected buildVEE(
    key: string,
    technical: string,
    detailed: string,
    contextualized: string
  ): VEEExplanations {
    return { [key]: { technical, detailed, contextualized } };
  }

  /**
   * Helper: Build context metadata
   */
  protected buildContext(state: LangGraphFinalState): ContextMetadata {
    return {
      intent: state.intent,
      domain: state.domain,
      conversation_id: state.conversation_id,
      timestamp: new Date().toISOString()
    };
  }
}
```

---

### Adapter Registry Interface

```typescript
export interface AdapterRegistry {
  /**
   * Register an adapter
   */
  register(adapter: BaseAdapter): void;

  /**
   * Select the appropriate adapter for a conversation
   */
  selectAdapter(conversation: ConversationType): BaseAdapter;

  /**
   * List all registered adapters
   */
  list(): BaseAdapter[];
}
```

---

### Implementation: `AdapterRegistryImpl`

```typescript
class AdapterRegistryImpl implements AdapterRegistry {
  private adapters: BaseAdapter[] = [];

  register(adapter: BaseAdapter): void {
    this.adapters.push(adapter);
  }

  selectAdapter(conversation: ConversationType): BaseAdapter {
    for (const adapter of this.adapters) {
      if (adapter.match(conversation)) {
        return adapter;
      }
    }
    
    // Fallback to ConversationalAdapter
    return new ConversationalAdapter();
  }

  list(): BaseAdapter[] {
    return [...this.adapters];
  }
}

export const adapterRegistry: AdapterRegistry = new AdapterRegistryImpl();
```

---

### Usage Example

```typescript
import { BaseAdapter, adapterRegistry } from '@/contracts/AdapterContract';

class MyAdapter extends BaseAdapter {
  conversationType = "my_intent";

  match(conversation) {
    return conversation.intent === "my_intent";
  }

  map(state) {
    return {
      narrative: this.buildNarrative("Summary text", "vee_summary"),
      followUps: this.buildFollowUps(["Question 1?", "Question 2?"]),
      evidence: [
        this.buildEvidenceSection("Section 1", [
          { label: "Metric A", value: 123, unit: "x", vee_key: "vee_metric_a" }
        ])
      ],
      vee_explanations: this.buildVEE(
        "vee_summary",
        "Technical explanation",
        "Detailed explanation",
        "Contextualized explanation"
      ),
      context: this.buildContext(state)
    };
  }
}

// Register at app boot
adapterRegistry.register(new MyAdapter());

// Use in component
const adapter = adapterRegistry.selectAdapter(conversation);
const payload = adapter.map(state);
```

---

## 3. DomainPluginContract — Extension Mechanism

### Purpose
Enables domain-specific extensions (adapters, VEE content, hooks, theme overrides) without modifying core UI code.

### File
`ui/contracts/DomainPluginContract.ts` (274 lines)

### Core Interface: `DomainPlugin`

```typescript
export interface DomainPlugin {
  metadata: {
    id: string;              // Unique plugin ID (e.g., "finance-ui")
    domain: string;          // Domain name (e.g., "finance", "energy")
    version: string;         // Semantic version (e.g., "1.0.0")
    description?: string;    // Optional description
  };

  adapters?: BaseAdapter[];  // Domain-specific adapters
  vee_content?: VEEExplanations; // Default VEE content for domain
  hooks?: Record<string, any>; // Custom React hooks
  theme_overrides?: {
    colors?: Record<string, string>;
    spacing?: Record<string, any>;
    radius?: Record<string, number>;
  };
}
```

---

### Domain Plugin Registry Interface

```typescript
export interface DomainPluginRegistry {
  /**
   * Register a domain plugin
   */
  register(plugin: DomainPlugin): void;

  /**
   * Get plugin by ID
   */
  getPlugin(id: string): DomainPlugin | undefined;

  /**
   * Get all plugins for a domain
   */
  getPluginsByDomain(domain: string): DomainPlugin[];

  /**
   * List all registered plugins
   */
  list(): DomainPlugin[];
}
```

---

### Implementation: `DomainPluginRegistryImpl`

```typescript
class DomainPluginRegistryImpl implements DomainPluginRegistry {
  private plugins: Map<string, DomainPlugin> = new Map();

  register(plugin: DomainPlugin): void {
    this.plugins.set(plugin.metadata.id, plugin);
    
    // Auto-register adapters
    if (plugin.adapters) {
      plugin.adapters.forEach(adapter => {
        adapterRegistry.register(adapter);
      });
    }
  }

  getPlugin(id: string): DomainPlugin | undefined {
    return this.plugins.get(id);
  }

  getPluginsByDomain(domain: string): DomainPlugin[] {
    return Array.from(this.plugins.values())
      .filter(p => p.metadata.domain === domain);
  }

  list(): DomainPlugin[] {
    return Array.from(this.plugins.values());
  }
}

export const domainPluginRegistry: DomainPluginRegistry = new DomainPluginRegistryImpl();
```

---

### Usage Example: Finance Plugin

```typescript
import { domainPluginRegistry } from '@/contracts/DomainPluginContract';
import { FinanceSingleTickerAdapter } from './adapters/FinanceSingleTickerAdapter';
import { useTradingOrder, usePortfolioCanvas } from './hooks';

const financePlugin: DomainPlugin = {
  metadata: {
    id: 'finance-ui',
    domain: 'finance',
    version: '1.0.0',
    description: 'Finance vertical UI extensions'
  },

  adapters: [
    new FinanceSingleTickerAdapter(),
    new FinanceScreeningAdapter(),
    new FinancePortfolioAdapter()
  ],

  vee_content: {
    "vee_pe_ratio": {
      technical: "Price-to-Earnings ratio. Formula: Market Cap / Net Income.",
      detailed: "Valuation multiple. Sector median is 18x. Higher = market expects growth.",
      contextualized: "P/E ratios vary by industry. Tech companies trade at 25-40x due to growth expectations. Utilities trade at 10-15x due to stable cash flows. Compare to PEG ratio for growth-adjusted valuation."
    }
  },

  hooks: {
    useTradingOrder,
    usePortfolioCanvas
  },

  theme_overrides: {
    colors: {
      primary: '#10b981', // Green for finance
      accent: '#3b82f6'
    }
  }
};

// Register at app boot (e.g., in app/layout.tsx)
domainPluginRegistry.register(financePlugin);
```

---

## Contract Enforcement

### Type Safety

All contracts are **TypeScript interfaces** enforced at compile time:

```typescript
// ✅ GOOD: Conforms to UIResponsePayload
const payload: UIResponsePayload = {
  narrative: { text: "Summary", vee_key: "vee_summary" },
  followUps: { chips: [{ text: "Question?" }] },
  evidence: null,
  vee_explanations: null,
  context: null
};

// ❌ ERROR: Missing required field
const badPayload: UIResponsePayload = {
  narrative: { text: "Summary" }
  // Missing: followUps, evidence, vee_explanations, context
};
```

---

### Runtime Validation

Use type guards for runtime validation:

```typescript
export function isUIResponsePayload(obj: any): obj is UIResponsePayload {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    ('narrative' in obj || 'followUps' in obj || 'evidence' in obj)
  );
}

// Usage
if (isUIResponsePayload(payload)) {
  // Safe to use payload
}
```

---

## Export Index

All contracts exported via `ui/contracts/index.ts`:

```typescript
// ui/contracts/index.ts
export type {
  UIResponsePayload,
  NarrativeBlock,
  FollowUpChips,
  EvidenceSection,
  MetricCard,
  VEEExplanations,
  ContextMetadata
} from './UIContract';

export {
  BaseAdapter,
  type AdapterRegistry,
  adapterRegistry
} from './AdapterContract';

export {
  type DomainPlugin,
  type DomainPluginRegistry,
  domainPluginRegistry
} from './DomainPluginContract';
```

---

## Contract Versioning

Contracts follow **semantic versioning**:

- **Major** (1.0.0 → 2.0.0): Breaking changes (field removal/rename)
- **Minor** (1.0.0 → 1.1.0): New fields (backward compatible)
- **Patch** (1.0.0 → 1.0.1): Documentation/fixes (no interface changes)

**Current version**: `1.0.0` (initial release, Feb 2026)

---

## Migration Guide

### From Legacy to Contracts (Pre-Feb 2026 → v1.0.0)

| Legacy Pattern | New Contract Pattern |
|----------------|----------------------|
| Component reads `state.summary` | Adapter produces `narrative: { text: state.summary }` |
| Component calculates metrics | Adapter populates `evidence: [{ cards: [...] }]` |
| Hardcoded VEE in component | Adapter provides `vee_explanations: { ... }` |
| Intent-based rendering | Adapter registry selects adapter by `match()` |

---

## References

- [UI Philosophy](philosophy.md) — Constitutional principles enforcing contracts
- [Stack](stack.md) — TypeScript configuration for contract enforcement
- [UI Overview](index.md) — Contract usage in UI architecture
- [UIContract.ts](../../ui/contracts/UIContract.ts) — Source code
- [AdapterContract.ts](../../ui/contracts/AdapterContract.ts) — Source code
- [DomainPluginContract.ts](../../ui/contracts/DomainPluginContract.ts) — Source code

---

**Last updated**: Feb 20, 2026 21:20 UTC
