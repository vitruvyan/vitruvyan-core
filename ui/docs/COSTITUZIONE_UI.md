# 🏛️ UI Constitution — Core Principles

> **Last updated**: Feb 20, 2026  
> **Status**: Constitutional (immutable)  
> **Inspired by**: [Mercator UI Constitution](https://github.com/vitruvyan/vitruvyan-ui/blob/main/ 🏛️%20COSTITUZIONE%20UI%20DI%20VITRUVYAN.md)

---

## Preamble

> Vitruvyan is not a dashboard.  
> Vitruvyan is not a collection of components.  
> **Vitruvyan is a cognitive system that dialogues with humans.**

This Constitution defines the immutable principles governing the UI of Vitruvyan and all its verticals.

---

## Article I — Separation of Thought and Visualization

The UI is divided into two distinct domains:

1. **Cognitive Domain** (reasoning, explanation, intention)
2. **Analytical Domain** (data, metrics, charts)

**The user speaks with the consultant first, not with data.**

No quantitative data may:
- Interrupt the narrative
- Anticipate the explanation
- Compete visually with conversational text

---

## Article II — The Adapter is the UX Unit

Every adapter represents a **complete and autonomous UX**.

An adapter:
- Knows the context
- Decides what to show
- Decides the order
- Decides the depth

> Components don't know context.  
> Adapters do.

UI scalability happens by **adding adapters**, not components.

---

## Article III — The Renderer is Stable

The final renderer (`VitruvyanResponseRenderer`) is **infrastructure**, not features.

The renderer:
- Contains no business logic
- Doesn't know the domain
- Doesn't evolve to support new UX

> If a new requirement demands modifying the renderer,  
> **the architecture is wrong upstream**.

---

## Article IV — Components are Tools, Not Decisions

A component:
- Visualizes
- Doesn't interpret
- Doesn't decide
- Doesn't orchestrate

Components:
- Must not contain domain logic
- Must not duplicate formatting
- Must not "know" why they're being used

---

## Article V — Semantic Tree Structure

Every folder represents a **verb**, not an arbitrary container.

| Folder | Verb |
|--------|------|
| `adapters/` | transforms |
| `response/` | renders |
| `composites/` | composes |
| `cards/` | displays |
| `explainability/` | explains |
| `theme/` | defines |
| `utils/` | supports |
| `_deprecated/` | preserves technical memory |

> ❌ **No JSX files may live in the root of `components/`.**

---

## Article VI — Explainability is a Domain, Not an Accessory

Everything that explains:
- VEE
- Tooltips
- Semantic badges
- Annotations

...lives in `explainability/`.

Explainability:
- Is not a visual detail
- Is not optional
- Is not delegated to individual components

> **Explanation is a cognitive layer, not a footnote.**

---

## Article VII — Information Stratification

Information is **not shown all at once**.

Every response is stratified:
1. Primary narrative
2. Explainability (VEE)
3. Structured data
4. Optional deep dives

Each level can be:
- Collapsed
- Expanded
- Ignored

> **The UI doesn't presume competence, it accompanies it.**

---

## Article VIII — Visual Consistency as Law

Colors, fonts, spacing, and hierarchies:
- Derive **only from tokens**
- Are never hardcoded

If two responses look visually different:
- User loses trust
- System loses authority

> **Vitruvyan UI must be recognizable as a single voice, like a coherent person.**

---

## Article IX — Conscious Deprecation

Code is **not deleted**: it's deprecated.

Every deprecated file:
- Is moved to `_deprecated/`
- Is clearly marked
- Has a future destination (removal or replacement)

> **Architectural memory is value, not weight.**

---

## Article X — Invariance Across Verticals

Every Vitruvyan vertical:
- Mercator (finance)
- Vector (energy)
- Ignis (facilities)
- Future domains

...must respect this Constitution.

**What changes:**
- Adapters
- Data
- Priorities

**What doesn't change:**
- Structure
- Cognitive flow
- Role separation

---

## Article XI — Silence Over Ambiguity

Vitruvyan **does not show incomplete data**.

If a section lacks sufficient information to be meaningful:
- It's not rendered
- It doesn't show "N/A" placeholders
- It doesn't suggest incompleteness

> **Better to say nothing than to say something misleading.**

Minimum thresholds per section:
- Fundamentals: min 3 metrics
- Risk: min 2 dimensions
- Comparison: min 2 valid tickers

---

## Article XII — Epistemic Order of Evidence

The order of evidence sections **is not arbitrary**.

It reflects how a rational system evaluates:

**Finance Example:**
1. **Solidity** — survival prerequisite
2. **Profitability** — current efficiency
3. **Growth** — future trajectory
4. **Risk** — limits and constraints
5. **Momentum/Trend** — market signals
6. **Sentiment** — external perception

> **Without solidity, the rest is noise.**

This order:
- Is epistemic, not graphical
- Is locked for each vertical
- Cannot be overridden by UX preferences

---

## Article XIII — Epistemic Tension

If data contradicts the verdict, **Vitruvyan declares it explicitly**.

Epistemic tension:
- Is detected by the **backend** (compose_node / decision engine)
- Is communicated to UI as a flag (`tension_detected: true`)
- Is made visible in narrative and badges

> **The UI doesn't infer, doesn't deduce, doesn't discover.**  
> **The UI makes visible a decision already made upstream.**

This distinguishes a narrative system from a cognitive system.  
Vitruvyan is both, but doesn't confuse them.

---

## Article XIV — Accompaniment, Not Imposition

The user **doesn't decide whether to trust** the verdict.

They are **accompanied to understand** why it's reasonable.

The UI structure:
- Doesn't ask for blind trust
- Doesn't hide reasoning
- Doesn't delegate synthesis to the user

> **Vitruvyan explains, doesn't convince.**

This is the heart of Vitruvyan's value.

---

## Article XV — Perceptual Micro-Signals

Badges and micro-indicators:
- Are **state signals**, not call-to-action
- Use **text + color**, not emojis
- Are visible even when sections are collapsed

Standard format:
- `Solidi` (green)
- `Neutrali` (gray)
- `In tensione` (orange/red)

> **A micro-badge is like a dashboard light: it informs, doesn't alert.**

This distinguishes Vitruvyan from anxiety-inducing dashboards.

---

## Article XVI — Evidence is Not a Playground

Evidence sections (Fundamentals, Risk, etc.):
- **Prove** the verdict, don't explore it
- Don't teach finance/energy/facilities
- Don't invite manual comparisons
- Are not infinitely expandable

> **The Fundamentals section doesn't serve to "understand fundamentals".**  
> **It serves to understand if Vitruvyan's answer has foundations.**

---

## Article XVII — Aggregate Indicators

Aggregate indicators (e.g., `fundamentals_z`) are **coherence indicators**, not mathematical averages.

A neutral `fundamentals_z` can derive from:
- All neutral metrics
- Discordant metrics that balance out

In both cases, the meaning is: **no net direction**.

> **The aggregate measures pattern coherence, not value sum.**

---

## Final Clause

This Constitution:
- Precedes code
- Governs choices
- Limits entropy
- Enables scalability

> **Every unjustified violation is conscious architectural debt.**

---

**Enforcement**: Any UI code violating these principles must be justified in code comments or refactored.

**Amendments**: Constitutional amendments require consensus among core maintainers and must preserve backward compatibility.

**Reference Implementation**: Mercator UI (finance vertical)

---

**Last updated**: Feb 20, 2026  
**Status**: ✅ Constitutional (immutable)  
**Approved by**: Vitruvyan Core Team
