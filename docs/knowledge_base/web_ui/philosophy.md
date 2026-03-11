---
tags:
  - web-ui
  - architecture
  - governance
---

# Web UI Philosophy — Constitutional Principles

> **Last updated**: Feb 20, 2026 21:10 UTC  
> **Source**: Costituzione UI (Mercator architecture)  
> **Status**: Immutable principles

---

## Introduction

The Vitruvyan Web UI is governed by **17 constitutional articles** that define the architectural foundation and UX design principles. These principles ensure:

- **Domain agnosticism** — Core UI works for any vertical
- **Adapter-driven UX** — Business logic lives in adapters, not components
- **Renderer stability** — Infrastructure components are feature-blind
- **Explainability as first-class** — Every feature has VEE (3-level explanations)

!!! warning "Constitutional Authority"
    These principles are **immutable**. Any code change that violates them must be rejected.

---

## The 17 Articles

### Article I — Separation of Thought and Visualization

**Principle**: Backend computing (cognitive layer) and frontend visualization (analytical layer) must remain strictly separated.

**Rationale**: The backend produces *thought* (LangGraph reasoning, Sacred Orders computation). The UI produces *visualization* (charts, narratives, accordions). Mixing them creates monolithic, untestable code.

**Implementation**:
- Backend emits `LangGraphFinalState` (cognitive artifact)
- Adapter transforms state → `UIResponsePayload` (canonical contract)
- Renderer consumes payload → DOM (visual artifact)

**Forbidden**:
- ❌ Backend returning JSX/HTML
- ❌ Frontend computing metrics/scores
- ❌ Components calling backend APIs directly (use adapters)

---

### Article II — The Adapter is the UX Unit

**Principle**: Each conversation type (intent classification) must correspond to a dedicated adapter that knows how to transform backend cognitive state into narrative, evidence, and explainability.

**Rationale**: Different intents require different UX treatments:
- `finance_single_ticker` → Epistemological ordering (Solidità → Redditività → Crescita → Risk)
- `conversational` → Simple Q&A narrative
- `codex_expedition` → System introspection with technical diagrams

The adapter encapsulates **all UX decisions** for that conversation type.

**Implementation**:
```typescript
class FinanceSingleTickerAdapter extends BaseAdapter {
  conversationType = "finance_single_ticker";
  
  match(conversation) {
    return conversation.intent === "finance_single_ticker";
  }

  map(state) {
    // UX logic: order evidence by epistemological priority
    const evidence = [
      this.buildSoliditaSection(state),
      this.buildRedditaSection(state),
      this.buildCrescitaSection(state),
      this.buildRiskSection(state)
    ];
    
    return { narrative, followUps, evidence, vee_explanations, context };
  }
}
```

**Forbidden**:
- ❌ Renderer deciding evidence order
- ❌ Components with `if (intent === "finance")` logic
- ❌ Shared "generic adapter" doing everything

---

### Article III — Renderer Stability (Infrastructure is Feature-Blind)

**Principle**: The renderer (VitruvyanResponseRenderer) is **infrastructure**. It consumes `UIResponsePayload` and renders it exactly as specified, without inspecting intent, domain, or semantic content.

**Rationale**: If the renderer needs to know "what kind of conversation this is," the adapter failed to produce a complete payload.

**Implementation**:
Fixed render flow:
```typescript
function VitruvyanResponseRenderer({ payload }) {
  return (
    <>
      {payload.narrative && <NarrativeBlock {...payload.narrative} />}
      {payload.followUps && <FollowUpChips {...payload.followUps} />}
      {payload.evidence && <EvidenceSectionRenderer {...payload.evidence} />}
      {payload.vee_explanations && <VEEAccordions {...payload.vee_explanations} />}
      {payload.context?.advisor && <AdvisorInsight {...payload.context.advisor} />}
    </>
  );
}
```

**Forbidden**:
- ❌ `if (payload.intent === "finance")` in renderer
- ❌ Renderer calling backend APIs
- ❌ Renderer computing derived state from payload
- ❌ Conditional render flow based on domain

**Allowed**:
- ✅ Null checks (`if (payload.narrative)`)
- ✅ Array iteration (`payload.evidence.map(...)`)
- ✅ Delegating to composites (`<NarrativeBlock />`)

---

### Article IV — Components are Tools (No Business Logic)

**Principle**: UI components (NarrativeBlock, EvidenceAccordion, FollowUpChips) are **tools**. They accept props and render them. They contain **zero business logic**.

**Rationale**: Business logic belongs in adapters. Components are reusable across all domains.

**Example (NarrativeBlock)**:
```tsx
// ✅ GOOD: Pure rendering component
function NarrativeBlock({ text, vee_key }) {
  return (
    <div className="narrative">
      <Markdown>{text}</Markdown>
      {vee_key && <VeeAnnotation veeKey={vee_key} />}
    </div>
  );
}

// ❌ BAD: Business logic in component
function NarrativeBlock({ text, state }) {
  const isFinance = state.intent === "finance_single_ticker";
  const summary = isFinance ? computeFinanceSummary(state) : state.summary;
  return <div>{summary}</div>;
}
```

**Forbidden**:
- ❌ Components computing metrics
- ❌ Components calling adapters
- ❌ Components with domain-specific logic
- ❌ Components reading from backend state directly

**Allowed**:
- ✅ Rendering props
- ✅ Local UI state (accordions open/closed)
- ✅ Event handlers (onClick, onChange)
- ✅ CSS/Tailwind styling decisions

---

### Article V — Semantic Tree Structure (Folders are Verbs)

**Principle**: Directory structure must reflect **semantic purpose**, not technical taxonomy.

**Rationale**: "What does this folder do?" should be answerable without reading code.

**Structure**:
```
ui/components/
├── adapters/         # Transform (backend → UI)
├── chat/             # Orchestrate (conversation flow)
├── response/         # Render (payload → DOM)
├── composites/       # Combine (reusable blocks)
├── explainability/   # Explain (VEE, tooltips)
├── cards/            # Display (atomic units)
└── theme/            # Style (tokens, constants)
```

**Forbidden**:
- ❌ `components/common/` (meaningless)
- ❌ `components/utils/` (semantic void)
- ❌ `components/misc/` (admission of failure)

**Allowed**:
- ✅ Verb-named folders (render, transform, orchestrate)
- ✅ Domain-scoped subfolders (`cards/finance/`, `cards/energy/`)
- ✅ `_base/` for abstract classes
- ✅ `_examples/` for reference implementations

---

### Article VI — Explainability as Domain (VEE is First-Class)

**Principle**: Explainability is not an afterthought. Every feature, metric, and decision must have **3-level VEE** (Technical, Detailed, Contextualized).

**Rationale**: Users need varying depths of explanation:
- **Technical** (5-15s) — For engineers debugging
- **Detailed** (30-60s) — For analysts understanding
- **Contextualized** (120-180s) — For domain experts deciding

**Implementation**:
```typescript
vee_explanations: {
  "vee_solidita_score": {
    technical: "Z-score normalization (-3 to +3 scale) of debt-to-equity ratio.",
    detailed: "Compares company's leverage vs. sector median. Positive = underleveraged.",
    contextualized: "Low debt enables flexibility in downturns. High debt magnifies returns in bull markets. This metric alone is insufficient; cross-reference with Free Cash Flow."
  }
}
```

**Forbidden**:
- ❌ Metrics without VEE keys
- ❌ VEE as pure backend logic (must be mapped to UI)
- ❌ Single-level explanations
- ❌ Domain-specific VEE in core components

**Allowed**:
- ✅ VEE registry in domain plugins
- ✅ `<VeeAnnotation veeKey="..." />` in narratives
- ✅ VEE overrides per adapter
- ✅ Default "missing VEE" message

---

### Article VII — No Hardcoded Styles (Token System)

**Principle**: All design decisions (colors, spacing, typography) must come from `components/theme/tokens.js`.

**Rationale**: Centralized tokens enable theme switching, domain overrides, and accessibility adjustments.

**Implementation**:
```javascript
// components/theme/tokens.js
export const tokens = {
  colors: {
    vitruvyan: { primary: '#000000', accent: '#3b82f6' },
    metrics: { positive: '#10b981', negative: '#ef4444', neutral: '#6b7280' }
  },
  spacing: {
    card: { gap: 16, padding: 20 },
    section: { gap: 20 }
  },
  radius: { card: 12, metric: 8 }
};

// Component usage
import { tokens } from '@/components/theme/tokens';

<div style={{ padding: tokens.spacing.card.padding }}>
```

**Forbidden**:
- ❌ `<div style={{ color: '#3b82f6' }}>`
- ❌ Inline hex colors
- ❌ Hardcoded pixel values (except one-off exceptions)
- ❌ CSS variables not in tokens

**Allowed**:
- ✅ Tailwind classes (built on tokens)
- ✅ Domain-specific token overrides (via plugins)
- ✅ Radix UI semantic variables (e.g., `--accent-a11`)

---

### Article VIII — Silence Over Ambiguity

**Principle**: If data is incomplete, missing, or ambiguous, **render nothing** rather than guessing or filling with placeholders.

**Rationale**: A blank section is better than misleading information.

**Implementation**:
```tsx
// ✅ GOOD: Null check
{payload.evidence && <EvidenceSectionRenderer {...payload.evidence} />}

// ❌ BAD: Placeholder
{payload.evidence || <div>No evidence available (loading...)</div>}
```

**Forbidden**:
- ❌ "Loading..." placeholders for static responses
- ❌ Default values masking backend failures
- ❌ Synthetic "N/A" data

**Allowed**:
- ✅ Skeleton loaders for async operations
- ✅ Empty state UI (when explicitly signaled by adapter)
- ✅ Error boundaries

---

### Article IX — Adapter Registry as Single Source of Truth

**Principle**: Adapter selection must go through `AdapterRegistry.selectAdapter()`. No manual adapter instantiation in components.

**Implementation**:
```typescript
// ✅ GOOD: Registry-based selection
const adapter = adapterRegistry.selectAdapter(conversation);
const payload = adapter.map(state);

// ❌ BAD: Manual adapter instantiation
const adapter = conversation.intent === "finance" 
  ? new FinanceAdapter() 
  : new ConversationalAdapter();
```

**Forbidden**:
- ❌ Components importing adapters directly
- ❌ Logic duplicating `match()` function
- ❌ Bypassing registry

**Allowed**:
- ✅ Adapter registration at boot
- ✅ Domain plugin adapters auto-registered
- ✅ Fallback to `ConversationalAdapter` if no match

---

### Article X — Domain Plugins Extend, Never Modify

**Principle**: Domain-specific functionality (finance, energy, facility) must be added via **plugins**, not by modifying core code.

**Implementation**:
```typescript
// ✅ GOOD: Plugin system
const financePlugin: DomainPlugin = {
  metadata: { id: 'finance-ui', domain: 'finance', version: '1.0.0' },
  adapters: [new FinanceSingleTickerAdapter()],
  vee_content: { /* finance VEE registry */ },
  hooks: { useTradingOrder, usePortfolioCanvas },
  theme_overrides: { colors: { primary: '#10b981' } }
};

domainPluginRegistry.register(financePlugin);

// ❌ BAD: Core modification
// ui/components/response/VitruvyanResponseRenderer.jsx
if (payload.domain === "finance") {
  return <FinanceSpecificRenderer {...payload} />;
}
```

**Forbidden**:
- ❌ Domain-specific code in core components
- ❌ Conditional imports based on domain
- ❌ Feature flags for domain functionality

**Allowed**:
- ✅ Domain adapters in `vitruvyan_core/domains/<domain>/ui/`
- ✅ Plugin registration in app bootstrap
- ✅ Domain hooks in plugin manifest

---

### Article XI — Pagination Over Virtualization (When Possible)

**Principle**: Prefer pagination to virtualization for long lists.

**Rationale**: Pagination is simpler, more accessible, and easier to test.

**Implementation**:
```tsx
// ✅ GOOD: Pagination
<Accordion>
  {evidence.slice(page * 10, (page + 1) * 10).map(...)}
</Accordion>
<Pagination currentPage={page} onPageChange={setPage} />

// ❌ BAD: Premature virtualization
<VirtualizedList items={evidence} />
```

**Exceptions**:
- Real-time streaming (chat messages, logs)
- Very large datasets (>500 items)

---

### Article XII — Epistemological Ordering (Finance Example)

**Principle**: Evidence must be ordered by **epistemological priority**, not visual convenience.

**Finance-specific ordering**:
1. **Solidità** (Solidity) — Balance sheet strength
2. **Redditività** (Profitability) — Income statement performance
3. **Crescita** (Growth) — Future potential
4. **Risk** — Downside scenarios

**Rationale**: Train users to read evidence in logical dependency order (you can't evaluate growth without knowing profitability).

**Implementation** (adapter):
```typescript
map(state) {
  const evidence = [];
  
  if (state.solidita) evidence.push(this.buildSoliditaSection(state));
  if (state.reddittivita) evidence.push(this.buildRedditaSection(state));
  if (state.crescita) evidence.push(this.buildCrescitaSection(state));
  if (state.risk) evidence.push(this.buildRiskSection(state));
  
  return { narrative, followUps, evidence, vee_explanations, context };
}
```

**Forbidden**:
- ❌ Alphabetical ordering
- ❌ Visual balance ordering (3 cards per row)
- ❌ User-customizable ordering (breaks epistemology)

---

### Article XIII — Read-Only by Default

**Principle**: The UI is **read-only** by default. Write operations require explicit authentication, confirmation, and audit trails.

**Implementation**:
- All GET endpoints: No auth required (read-only)
- All POST/PUT/DELETE: OAuth/Keycloak required
- Write operations show confirmation dialog with audit preview

**Forbidden**:
- ❌ Silent mutations
- ❌ Optimistic UI updates without rollback
- ❌ Write operations in query hooks

**Allowed**:
- ✅ Client-side filters (no backend mutation)
- ✅ Local UI state (accordion open/closed)
- ✅ Authenticated write hooks (explicit)

---

### Article XIV — Progressive Disclosure

**Principle**: Information density should increase with user depth (shallow → deep).

**Levels**:
1. **Narrative** — High-level summary (100-200 words)
2. **Evidence Accordions** — Detailed metrics (collapsed by default)
3. **VEE Deep Dive** — Full explainability (on demand)

**Implementation**:
```tsx
<NarrativeBlock>{payload.narrative}</NarrativeBlock>
<Accordion defaultValue="">
  {payload.evidence.map(section => <AccordionItem>...</AccordionItem>)}
</Accordion>
<VEEAccordions>{payload.vee_explanations}</VEEAccordions>
```

**Forbidden**:
- ❌ All accordions open by default
- ❌ Hiding critical information behind 4+ clicks
- ❌ VEE as inline tooltips (too distracting)

---

### Article XV — Accessibility is Non-Negotiable

**Principle**: All components must meet **WCAG 2.1 AA** standards.

**Requirements**:
- Keyboard navigation (Tab, Enter, Escape)
- Screen reader labels (aria-label, aria-describedby)
- Color contrast ≥ 4.5:1 (text), ≥ 3:1 (UI)
- Focus indicators

**Implementation**:
- Use Radix UI primitives (accessibility built-in)
- Test with aXe DevTools
- Keyboard-test every interactive component

**Forbidden**:
- ❌ `<div onClick>` without keyboard handler
- ❌ Color-only information (add text/icons)
- ❌ Removing focus outlines

---

### Article XVI — No Client-Side Secrets

**Principle**: API keys, tokens, and secrets must **never** be in frontend code.

**Implementation**:
- Backend-for-frontend (BFF) pattern
- Public API keys must be scoped (read-only, rate-limited)
- OAuth flow handled server-side

**Forbidden**:
- ❌ `const API_KEY = "sk-..."`
- ❌ Hardcoded JWT tokens
- ❌ `.env` variables with write-access keys

---

### Article XVII — Documentation as Code

**Principle**: Every adapter, plugin, and major component must have:
1. **README.md** — Purpose, usage, examples
2. **VEE content** — 3-level explanations
3. **Tests** — Unit tests for `map()` logic

**Rationale**: Undocumented code is unmaintainable.

**Enforcement**:
- CI fails if new adapter missing README
- PR checklist requires VEE registration
- Test coverage target: 80%

---

## Enforcement

Constitutional violations are identified by:

1. **Code review** — Manual inspection
2. **Linting** — ESLint rules (e.g., no hardcoded colors)
3. **Architecture tests** — Jest snapshots of adapter registry
4. **Documentation audits** — Quarterly review

**Penalty for violation**: Code is rejected, regardless of functionality.

---

## Amendment Process

These articles are **immutable** for v1.0 of the UI. To amend:

1. Propose amendment in RFC (Request for Comments)
2. Demonstrate failure case where current article blocks critical functionality
3. Get unanimous approval from UI architecture team
4. Increment constitution version (v1.0 → v2.0)

**Historical note**: These principles are derived from the Mercator UI Constitution (Jan 2026), adapted for domain-agnostic Vitruvyan OS.

---

## References

- [Costituzione UI (Italian)](../../ui/docs/COSTITUZIONE_UI.md) — Original 17 articles
- [Contracts](contracts.md) — TypeScript interface enforcement
- [Stack](stack.md) — Technology choices aligned with principles
- [UI Overview](index.md) — Quick reference

---

**Last updated**: Feb 20, 2026 21:10 UTC
