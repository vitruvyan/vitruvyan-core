# Neural Engine Core - Philosophy

## What is a Cognitive Substrate?

The Neural Engine Core is not a framework.  
It is not a library of ready-to-use components.  
It is not a collection of best practices.

**It is a blank computational substrate.**

Think of it as:
- A spreadsheet with formula support, but no data
- A CPU without an operating system
- An empty factory floor with conveyor belts, but no workers or products

---

## What the Core Does NOT Do

The Neural Engine Core has **zero opinions** about:

- What makes an entity "good" or "bad"
- Which factors matter in your domain
- How to weigh different dimensions of quality
- What "normal" or "optimal" means
- How to interpret scores or rankings

It provides **no domain knowledge**:
- No entity entity_ids, sectors, or financial ratios
- No patient symptoms, diagnoses, or treatments
- No routes, vehicles, or delivery windows
- No weapons systems, threat levels, or readiness scores

It provides **no preferred patterns**:
- No "best way" to organize factors
- No "recommended" normalization strategy
- No default aggregation weights
- No built-in filters or thresholds

---

## What the Core DOES Provide

The core provides **structure without content**:

1. **Three abstract contracts** that define:
   - What it means to compute a factor
   - What it means to normalize scores
   - What it means to aggregate into a composite

2. **An orchestration flow** that coordinates:
   - Raw factor computation
   - Score normalization
   - Weighted aggregation
   - Result packaging

3. **Data structures** for:
   - Evaluation inputs (context, entity list)
   - Evaluation outputs (scores, ranks, contributions)

4. **One reference implementation** (ZScoreNormalizer):
   - Not because it's "best"
   - But to show how contracts work
   - Your domain may need something completely different

---

## The Philosophy: Structure, Not Solution

### Core is Ontologically Neutral

The core does not teach you **what to evaluate**.  
It teaches you **how to structure evaluation**.

It says: "If you have computed dimensions of quality, here's how to:
- Normalize them to comparable scales
- Combine them into a composite
- Track how each dimension contributed"

But it never tells you:
- Which dimensions matter
- How to compute them
- What the scores mean

### Verticals Are Epistemologically Specific

Your vertical (Mercator, AEGIS, custom domain) makes the **epistemological choices**:

- **Mercator** says: "Quality = momentum + trend + volatility"
- **AEGIS** says: "Readiness = training + equipment + morale"
- **Your domain** says: "[YOUR DEFINITION OF QUALITY]"

The core doesn't care. It executes the structure you define.

---

## Why This Matters

### Anti-Framework Design

Most evaluation systems are frameworks:
- "Here are 50 factors you can use"
- "Here are 10 profiles we recommend"
- "Here's the best way to normalize"

This creates **conceptual lock-in**. You start thinking in the framework's terms, not your domain's terms.

Vitruvyan Core inverts this:
- "Here are zero factors. You define yours."
- "Here are zero profiles. You define yours."
- "Here's one normalizer as an example. Yours will differ."

### Cognitive Flexibility

By providing **only structure**, the core forces you to think:

- What does "better" mean in my domain?
- How do I measure the qualities that matter?
- What tradeoffs am I making when I set weights?

You can't cargo-cult from the core. You must understand your domain.

---

## What Success Looks Like

### Bad Usage (Framework Thinking)
```python
# User treats core as a ready-made solution
factors = [
    momentum_factor,  # "The framework has this"
    trend_factor,     # "Everyone uses this"
]
profile = balanced_profile  # "The default profile"
```

### Good Usage (Substrate Thinking)
```python
# User defines domain-specific logic
factors = [
    PatientRecoverySpeed(data_source=ehr),
    ComplicationRisk(model=risk_model),
    TreatmentCompliance(threshold=0.8)
]

profile = ClinicalPrioritization(
    speed_weight=0.3,
    risk_weight=0.5,
    compliance_weight=0.2
)
```

The core doesn't know about "patients" or "recovery".  
It just executes: compute → normalize → aggregate.

---

## The Inevitable Discomfort

Using the Neural Engine Core **should feel uncomfortable at first**.

You will think: "But where are the examples?"  
You will ask: "What's the best way to do X?"  
You will want: "A quick start guide with defaults."

**This discomfort is intentional.**

It's the discomfort of taking responsibility for your domain's conceptual model.

The core doesn't give you answers because **there are no universal answers**.

- Finance thinks in momentum and volatility
- Healthcare thinks in outcomes and risks
- Logistics thinks in efficiency and reliability

These are **incommensurable** concepts. No single framework can unify them without distortion.

The core unifies only the **structure of evaluation**, not the **content of evaluation**.

---

## Design Principles

1. **Contracts over implementations**  
   Define what something IS, not what it DOES in practice.

2. **One example, not many options**  
   One reference normalizer teaches the pattern. Multiple normalizers suggest choices.

3. **Documentation that resists, not assists**  
   Guide users to think, not to copy-paste.

4. **Patterns as separate library**  
   Utilities exist, but are clearly marked "optional, not identity".

5. **No domain vocabulary**  
   Only generic: entity, factor, score, weight, aggregate.

---

## For Vertical Developers

If you're building on top of Neural Engine Core:

**Stop here. Think before you code.**

Ask yourself:
1. What does "quality" mean in my domain?
2. What are the fundamental dimensions I'm measuring?
3. How do these dimensions trade off against each other?
4. What would change if my domain's goals shifted?

Only when you can answer these questions should you start implementing factors.

The core is not a shortcut. It's a foundation for **thoughtful evaluation**.

---

## Closing Thought

> "A blank canvas is not 'missing' the painting.  
> It's providing the space where your painting can exist."

The Neural Engine Core is that blank canvas.  
Your vertical is the painting.

The core's job is to stay blank.
