# Contratti Web UI — Documentazione Interfacce TypeScript

> **Ultimo aggiornamento**: 20 Feb 2026 21:20 UTC  
> **Posizione**: `ui/contracts/`  
> **Scopo**: Struttura payload canonico + sistema adapter + interfacce plugin dominio

---

## Panoramica

Il sistema di contratti della Web UI di Vitruvyan definisce **3 interfacce TypeScript core** che applicano la separazione delle responsabilità tra backend, adapter e UI:

| Contratto | Scopo | File |
|-----------|-------|------|
| **UIContract** | Payload canonico consumato dal renderer | `UIContract.ts` (195 LOC) |
| **AdapterContract** | Trasformazione stato backend → UI | `AdapterContract.ts` (260 LOC) |
| **DomainPluginContract** | Meccanismo estensione dominio | `DomainPluginContract.ts` (274 LOC) |

**Totale**: 820 righe di TypeScript

---

## 1. UIContract — Struttura Payload Canonico

### Scopo
Definisce la **single source of truth** per tutti i payload UI consumati da `VitruvyanResponseRenderer`.

### File
`ui/contracts/UIContract.ts` (195 righe)

### Interfaccia Core: `UIResponsePayload`

```typescript
export interface UIResponsePayload {
  narrative: NarrativeBlock | null;
  followUps: FollowUpChips | null;
  evidence: EvidenceSection[] | null;
  vee_explanations: VEEExplanations | null;
  context: ContextMetadata | null;
}
```

### Sub-Interfacce

#### `NarrativeBlock`
Riepilogo alto livello con annotazione VEE opzionale.

```typescript
export interface NarrativeBlock {
  text: string;               // Riepilogo formato Markdown (100-300 parole)
  vee_key?: string;           // Chiave VEE opzionale per explainability
  intent_badge?: IntentBadge; // Visualizzazione classificazione intent
}
```

**Esempio**:
```typescript
{
  text: "Apple Inc. (AAPL) mostra fondamentali solidi con un punteggio Solidità di +2.3σ sopra la mediana del settore.",
  vee_key: "vee_summary_finance_ticker",
  intent_badge: { label: "Analisi Finanziaria", color: "green" }
}
```

---

#### `FollowUpChips`
Chip di suggerimento follow-up interattivi.

```typescript
export interface FollowUpChips {
  chips: Array<{
    text: string;
    action?: "query" | "navigate" | "drill_down";
    payload?: any;
  }>;
}
```

**Esempio**:
```typescript
{
  chips: [
    { text: "Confronta con peer del settore", action: "query", payload: { sector: "tech" } },
    { text: "Analisi trend storico", action: "drill_down" },
    { text: "Mostra fattori di rischio", action: "navigate", payload: { section: "risk" } }
  ]
}
```

---

#### `EvidenceSection`
Accordion richiudibile con card metriche.

```typescript
export interface EvidenceSection {
  title: string;              // Titolo sezione (es. "Solidità — Bilancio")
  subtitle?: string;          // Sottotitolo opzionale
  cards: MetricCard[];        // Array card metriche
  vee_key?: string;           // VEE opzionale per spiegazione livello sezione
  epistemic_order?: number;   // Priorità epistemologica (1 = massima)
}

export interface MetricCard {
  label: string;              // Nome metrica (es. "Rapporto Debito/Equity")
  value: string | number;     // Valore visualizzato (es. "0.45" o "$12.5B")
  unit?: string;              // Unità opzionale (es. "%", "B", "x")
  trend?: "up" | "down" | "neutral"; // Indicatore trend
  severity?: "positive" | "negative" | "neutral"; // Codifica colore
  vee_key?: string;           // Chiave VEE per spiegazione livello metrica
  metadata?: Record<string, any>; // Metadata arbitrari
}
```

**Esempio**:
```typescript
{
  title: "Solidità — Forza del Bilancio",
  subtitle: "Metriche leva finanziaria e liquidità",
  epistemic_order: 1,
  vee_key: "vee_solidita_section",
  cards: [
    {
      label: "Debito/Equity",
      value: 0.45,
      unit: "x",
      trend: "down",
      severity: "positive",
      vee_key: "vee_debt_equity_ratio"
    },
    {
      label: "Rapporto Corrente",
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
Registro explainability a tre livelli.

```typescript
export interface VEEExplanations {
  [vee_key: string]: {
    technical: string;        // Lettura 5-15s (per ingegneri)
    detailed: string;         // Lettura 30-60s (per analisti)
    contextualized: string;   // Lettura 120-180s (per esperti dominio)
  };
}
```

**Esempio**:
```typescript
{
  "vee_debt_equity_ratio": {
    technical: "Rapporto tra passività totali e patrimonio netto. Formula: Debito Totale / Equity Totale.",
    detailed: "Misura la leva finanziaria. Valori più bassi indicano struttura del capitale conservativa. Mediana settore è 0.8x.",
    contextualized: "Un rapporto 0.45x suggerisce che l'azienda è sottoleva rispetto ai peer. Questo fornisce flessibilità in recessioni economiche ma può indicare capitale sottoutilizzato. Cross-referenziare con ROE e WACC per valutare efficienza del capitale."
  }
}
```

---

#### `ContextMetadata`
Contesto aggiuntivo per la risposta.

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

**Esempio**:
```typescript
{
  intent: "finance_single_ticker",
  domain: "finance",
  conversation_id: "conv_1234",
  timestamp: "2026-02-20T21:00:00Z",
  advisor: {
    text: "Questa analisi usa dati alla chiusura del mercato 2026-02-19. Eventi macroeconomici possono impattare le valutazioni.",
    severity: "info"
  }
}
```

---

### Tipi Esportati

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

## 2. AdapterContract — Interfaccia Trasformazione

### Scopo
Definisce l'interfaccia adapter che trasforma `LangGraphFinalState` backend in `UIResponsePayload`.

### File
`ui/contracts/AdapterContract.ts` (260 righe)

### Classe Astratta Core: `BaseAdapter`

```typescript
export abstract class BaseAdapter {
  abstract conversationType: string;

  /**
   * Verifica se questo adapter dovrebbe gestire la conversazione
   */
  abstract match(conversation: ConversationType): boolean;

  /**
   * Trasforma stato backend in payload UI
   */
  abstract map(state: LangGraphFinalState): UIResponsePayload;

  /**
   * Helper: Costruisce blocco narrativa
   */
  protected buildNarrative(
    text: string,
    vee_key?: string,
    intent_badge?: IntentBadge
  ): NarrativeBlock {
    return { text, vee_key, intent_badge };
  }

  /**
   * Helper: Costruisce chip follow-up
   */
  protected buildFollowUps(chips: string[]): FollowUpChips {
    return {
      chips: chips.map(text => ({ text, action: "query" }))
    };
  }

  /**
   * Helper: Costruisce sezione evidenze
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
   * Helper: Costruisce spiegazioni VEE
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
   * Helper: Costruisce metadata contesto
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

### Interfaccia Registro Adapter

```typescript
export interface AdapterRegistry {
  /**
   * Registra un adapter
   */
  register(adapter: BaseAdapter): void;

  /**
   * Seleziona l'adapter appropriato per una conversazione
   */
  selectAdapter(conversation: ConversationType): BaseAdapter;

  /**
   * Lista tutti gli adapter registrati
   */
  list(): BaseAdapter[];
}
```

---

### Implementazione: `AdapterRegistryImpl`

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
    
    // Fallback a ConversationalAdapter
    return new ConversationalAdapter();
  }

  list(): BaseAdapter[] {
    return [...this.adapters];
  }
}

export const adapterRegistry: AdapterRegistry = new AdapterRegistryImpl();
```

---

### Esempio Utilizzo

```typescript
import { BaseAdapter, adapterRegistry } from '@/contracts/AdapterContract';

class MyAdapter extends BaseAdapter {
  conversationType = "my_intent";

  match(conversation) {
    return conversation.intent === "my_intent";
  }

  map(state) {
    return {
      narrative: this.buildNarrative("Testo riepilogo", "vee_summary"),
      followUps: this.buildFollowUps(["Domanda 1?", "Domanda 2?"]),
      evidence: [
        this.buildEvidenceSection("Sezione 1", [
          { label: "Metrica A", value: 123, unit: "x", vee_key: "vee_metric_a" }
        ])
      ],
      vee_explanations: this.buildVEE(
        "vee_summary",
        "Spiegazione tecnica",
        "Spiegazione dettagliata",
        "Spiegazione contestualizzata"
      ),
      context: this.buildContext(state)
    };
  }
}

// Registra al boot app
adapterRegistry.register(new MyAdapter());

// Usa nel componente
const adapter = adapterRegistry.selectAdapter(conversation);
const payload = adapter.map(state);
```

---

## 3. DomainPluginContract — Meccanismo Estensione

### Scopo
Abilita estensioni domain-specific (adapter, contenuto VEE, hook, override tema) senza modificare codice UI core.

### File
`ui/contracts/DomainPluginContract.ts` (274 righe)

### Interfaccia Core: `DomainPlugin`

```typescript
export interface DomainPlugin {
  metadata: {
    id: string;              // ID plugin univoco (es. "finance-ui")
    domain: string;          // Nome dominio (es. "finance", "energy")
    version: string;         // Versione semantica (es. "1.0.0")
    description?: string;    // Descrizione opzionale
  };

  adapters?: BaseAdapter[];  // Adapter domain-specific
  vee_content?: VEEExplanations; // Contenuto VEE default per dominio
  hooks?: Record<string, any>; // Hook React personalizzati
  theme_overrides?: {
    colors?: Record<string, string>;
    spacing?: Record<string, any>;
    radius?: Record<string, number>;
  };
}
```

---

### Interfaccia Registro Plugin Dominio

```typescript
export interface DomainPluginRegistry {
  /**
   * Registra un plugin dominio
   */
  register(plugin: DomainPlugin): void;

  /**
   * Ottieni plugin per ID
   */
  getPlugin(id: string): DomainPlugin | undefined;

  /**
   * Ottieni tutti i plugin per un dominio
   */
  getPluginsByDomain(domain: string): DomainPlugin[];

  /**
   * Lista tutti i plugin registrati
   */
  list(): DomainPlugin[];
}
```

---

### Implementazione: `DomainPluginRegistryImpl`

```typescript
class DomainPluginRegistryImpl implements DomainPluginRegistry {
  private plugins: Map<string, DomainPlugin> = new Map();

  register(plugin: DomainPlugin): void {
    this.plugins.set(plugin.metadata.id, plugin);
    
    // Auto-registra adapter
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

### Esempio Utilizzo: Plugin Finance

```typescript
import { domainPluginRegistry } from '@/contracts/DomainPluginContract';
import { FinanceSingleTickerAdapter } from './adapters/FinanceSingleTickerAdapter';
import { useTradingOrder, usePortfolioCanvas } from './hooks';

const financePlugin: DomainPlugin = {
  metadata: {
    id: 'finance-ui',
    domain: 'finance',
    version: '1.0.0',
    description: 'Estensioni UI verticale finance'
  },

  adapters: [
    new FinanceSingleTickerAdapter(),
    new FinanceScreeningAdapter(),
    new FinancePortfolioAdapter()
  ],

  vee_content: {
    "vee_pe_ratio": {
      technical: "Rapporto Price-to-Earnings. Formula: Market Cap / Utile Netto.",
      detailed: "Multiplo di valutazione. Mediana settore è 18x. Più alto = il mercato si aspetta crescita.",
      contextualized: "I rapporti P/E variano per settore. Le aziende tech operano a 25-40x per aspettative di crescita. Le utility operano a 10-15x per flussi di cassa stabili. Confrontare con rapporto PEG per valutazione aggiustata per crescita."
    }
  },

  hooks: {
    useTradingOrder,
    usePortfolioCanvas
  },

  theme_overrides: {
    colors: {
      primary: '#10b981', // Verde per finance
      accent: '#3b82f6'
    }
  }
};

// Registra al boot app (es. in app/layout.tsx)
domainPluginRegistry.register(financePlugin);
```

---

## Enforcement Contratti

### Type Safety

Tutti i contratti sono **interfacce TypeScript** applicate a compile time:

```typescript
// ✅ BENE: Conforme a UIResponsePayload
const payload: UIResponsePayload = {
  narrative: { text: "Riepilogo", vee_key: "vee_summary" },
  followUps: { chips: [{ text: "Domanda?" }] },
  evidence: null,
  vee_explanations: null,
  context: null
};

// ❌ ERRORE: Campo richiesto mancante
const badPayload: UIResponsePayload = {
  narrative: { text: "Riepilogo" }
  // Mancanti: followUps, evidence, vee_explanations, context
};
```

---

### Validazione Runtime

Usa type guard per validazione runtime:

```typescript
export function isUIResponsePayload(obj: any): obj is UIResponsePayload {
  return (
    obj !== null &&
    typeof obj === 'object' &&
    ('narrative' in obj || 'followUps' in obj || 'evidence' in obj)
  );
}

// Utilizzo
if (isUIResponsePayload(payload)) {
  // Sicuro usare payload
}
```

---

## Indice Export

Tutti i contratti esportati via `ui/contracts/index.ts`:

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

## Versionamento Contratti

I contratti seguono il **versionamento semantico**:

- **Major** (1.0.0 → 2.0.0): Breaking change (rimozione/rinomina campo)
- **Minor** (1.0.0 → 1.1.0): Nuovi campi (backward compatible)
- **Patch** (1.0.0 → 1.0.1): Documentazione/fix (nessun cambio interfaccia)

**Versione corrente**: `1.0.0` (rilascio iniziale, Feb 2026)

---

## Guida Migrazione

### Da Legacy a Contratti (Pre-Feb 2026 → v1.0.0)

| Pattern Legacy | Nuovo Pattern Contratti |
|----------------|-------------------------|
| Componente legge `state.summary` | Adapter produce `narrative: { text: state.summary }` |
| Componente calcola metriche | Adapter popola `evidence: [{ cards: [...] }]` |
| VEE hardcoded nel componente | Adapter fornisce `vee_explanations: { ... }` |
| Rendering basato su intent | Registro adapter seleziona adapter via `match()` |

---

## Riferimenti

- [Filosofia UI](philosophy.it.md) — Principi costituzionali che applicano contratti
- [Stack](stack.it.md) — Configurazione TypeScript per enforcement contratti
- [Panoramica UI](index.it.md) — Uso contratti in architettura UI
- [UIContract.ts](../../ui/contracts/UIContract.ts) — Codice sorgente
- [AdapterContract.ts](../../ui/contracts/AdapterContract.ts) — Codice sorgente
- [DomainPluginContract.ts](../../ui/contracts/DomainPluginContract.ts) — Codice sorgente

---

**Ultimo aggiornamento**: 20 Feb 2026 21:20 UTC
