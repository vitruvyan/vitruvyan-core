# Filosofia Web UI — Principi Costituzionali

> **Ultimo aggiornamento**: 20 Feb 2026 21:10 UTC  
> **Fonte**: Costituzione UI (architettura Mercator)  
> **Stato**: Principi immutabili

---

## Introduzione

La Web UI di Vitruvyan è governata da **17 articoli costituzionali** che definiscono le fondamenta architect turali e i principi di design UX. Questi principi garantiscono:

- **Domain agnosticism** — La UI core funziona per qualsiasi verticale
- **UX basata su adapter** — La logica di business vive negli adapter, non nei componenti
- **Stabilità del renderer** — I componenti infrastrutturali sono feature-blind
- **Explainability come first-class** — Ogni funzionalità ha VEE (spiegazioni a 3 livelli)

!!! warning "Autorità Costituzionale"
    Questi principi sono **immutabili**. Qualsiasi modifica al codice che li violi deve essere rifiutata.

---

## I 17 Articoli

### Articolo I — Separazione di Pensiero e Visualizzazione

**Principio**: Il calcolo backend (layer cognitivo) e la visualizzazione frontend (layer analitico) devono rimanere rigorosamente separati.

**Razionale**: Il backend produce *pensiero* (ragionamento LangGraph, computazione Sacred Orders). La UI produce *visualizzazione* (grafici, narrative, accordion). Mescolarli crea codice monolitico e non testabile.

**Implementazione**:
- Backend emette `LangGraphFinalState` (artefatto cognitivo)
- Adapter trasforma stato → `UIResponsePayload` (contratto canonico)
- Renderer consuma payload → DOM (artefatto visuale)

**Proibito**:
- ❌ Backend che ritorna JSX/HTML
- ❌ Frontend che calcola metriche/punteggi
- ❌ Componenti che chiamano API backend direttamente (usare adapter)

---

### Articolo II — L'Adapter è l'Unità di UX

**Principio**: Ogni tipo di conversazione (classificazione dell'intent) deve corrispondere a un adapter dedicato che sa come trasformare lo stato cognitivo del backend in narrativa, evidenze ed explainability.

**Razionale**: Diversi intent richiedono diversi trattamenti UX:
- `finance_single_ticker` → Ordinamento epistemologico (Solidità → Redditività → Crescita → Risk)
- `conversational` → Semplice narrativa Q&A
- `codex_expedition` → Introspezione di sistema con diagrammi tecnici

L'adapter incapsula **tutte le decisioni UX** per quel tipo di conversazione.

**Implementazione**:
```typescript
class FinanceSingleTickerAdapter extends BaseAdapter {
  conversationType = "finance_single_ticker";
  
  match(conversation) {
    return conversation.intent === "finance_single_ticker";
  }

  map(state) {
    // Logica UX: ordina evidenze per priorità epistemologica
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

**Proibito**:
- ❌ Renderer che decide l'ordine delle evidenze
- ❌ Componenti con logica `if (intent === "finance")`
- ❌ "Adapter generico" condiviso che fa tutto

---

### Articolo III — Stabilità del Renderer (L'Infrastruttura è Feature-Blind)

**Principio**: Il renderer (VitruvyanResponseRenderer) è **infrastruttura**. Consuma `UIResponsePayload` e lo renderizza esattamente come specificato, senza ispezionare intent, dominio o contenuto semantico.

**Razionale**: Se il renderer deve sapere "che tipo di conversazione è questa," l'adapter ha fallito nel produrre un payload completo.

**Implementazione**:
Flusso render fisso:
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

**Proibito**:
- ❌ `if (payload.intent === "finance")` nel renderer
- ❌ Renderer che chiama API backend
- ❌ Renderer che calcola stato derivato dal payload
- ❌ Flusso render condizionale basato sul dominio

**Consentito**:
- ✅ Controlli null (`if (payload.narrative)`)
- ✅ Iterazione array (`payload.evidence.map(...)`)
- ✅ Delega a composites (`<NarrativeBlock />`)

---

### Articolo IV — I Componenti sono Strumenti (Nessuna Logica di Business)

**Principio**: I componenti UI (NarrativeBlock, EvidenceAccordion, FollowUpChips) sono **strumenti**. Accettano props e li renderizzano. Contengono **zero logica di business**.

**Razionale**: La logica di business appartiene agli adapter. I componenti sono riusabili in tutti i domini.

**Esempio (NarrativeBlock)**:
```tsx
// ✅ BENE: Componente di rendering puro
function NarrativeBlock({ text, vee_key }) {
  return (
    <div className="narrative">
      <Markdown>{text}</Markdown>
      {vee_key && <VeeAnnotation veeKey={vee_key} />}
    </div>
  );
}

// ❌ MALE: Logica di business nel componente
function NarrativeBlock({ text, state }) {
  const isFinance = state.intent === "finance_single_ticker";
  const summary = isFinance ? computeFinanceSummary(state) : state.summary;
  return <div>{summary}</div>;
}
```

**Proibito**:
- ❌ Componenti che calcolano metriche
- ❌ Componenti che chiamano adapter
- ❌ Componenti con logica domain-specific
- ❌ Componenti che leggono direttamente dallo stato backend

**Consentito**:
- ✅ Rendering props
- ✅ Stato UI locale (accordion aperto/chiuso)
- ✅ Event handler (onClick, onChange)
- ✅ Decisioni styling CSS/Tailwind

---

### Articolo V — Struttura Semantica ad Albero (Le Cartelle sono Verbi)

**Principio**: La struttura delle directory deve riflettere lo **scopo semantico**, non la tassonomia tecnica.

**Razionale**: "Cosa fa questa cartella?" deve essere rispondibile senza leggere codice.

**Struttura**:
```
ui/components/
├── adapters/         # Trasforma (backend → UI)
├── chat/             # Orchestra (flusso conversazione)
├── response/         # Renderizza (payload → DOM)
├── composites/       # Combina (blocchi riusabili)
├── explainability/   # Spiega (VEE, tooltip)
├── cards/            # Visualizza (unità atomiche)
└── theme/            # Stilizza (token, costanti)
```

**Proibito**:
- ❌ `components/common/` (senza significato)
- ❌ `components/utils/` (vuoto semantico)
- ❌ `components/misc/` (ammissione di fallimento)

**Consentito**:
- ✅ Cartelle con nomi verbali (render, transform, orchestrate)
- ✅ Sottocartelle per dominio (`cards/finance/`, `cards/energy/`)
- ✅ `_base/` per classi astratte
- ✅ `_examples/` per implementazioni di riferimento

---

### Articolo VI — Explainability come Dominio (VEE è First-Class)

**Principio**: L'explainability non è un ripensamento. Ogni funzionalità, metrica e decisione deve avere **VEE a 3 livelli** (Technical, Detailed, Contextualized).

**Razionale**: Gli utenti necessitano di profondità variabili di spiegazione:
- **Technical** (5-15s) — Per ingegneri in debug
- **Detailed** (30-60s) — Per analisti che comprendono
- **Contextualized** (120-180s) — Per esperti di dominio che decidono

**Implementazione**:
```typescript
vee_explanations: {
  "vee_solidita_score": {
    technical: "Normalizzazione Z-score (scala -3 a +3) del rapporto debito/equity.",
    detailed: "Confronta la leva finanziaria dell'azienda vs mediana del settore. Positivo = sottoleva.",
    contextualized: "Basso debito consente flessibilità in recessioni. Alto debito magnifica ritorni in mercati rialzisti. Questa metrica da sola è insufficiente; cross-referenziare con Free Cash Flow."
  }
}
```

**Proibito**:
- ❌ Metriche senza chiavi VEE
- ❌ VEE come pura logica backend (deve essere mappato alla UI)
- ❌ Spiegazioni a singolo livello
- ❌ VEE domain-specific nei componenti core

**Consentito**:
- ✅ Registro VEE nei plugin di dominio
- ✅ `<VeeAnnotation veeKey="..." />` nelle narrative
- ✅ Override VEE per adapter
- ✅ Messaggio default "VEE mancante"

---

### Articolo VII — Nessuno Stile Hardcoded (Sistema Token)

**Principio**: Tutte le decisioni di design (colori, spaziature, tipografia) devono provenire da `components/theme/tokens.js`.

**Razionale**: Token centralizzati consentono cambio tema, override di dominio e aggiustamenti accessibilità.

**Implementazione**:
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

// Uso nel componente
import { tokens } from '@/components/theme/tokens';

<div style={{ padding: tokens.spacing.card.padding }}>
```

**Proibito**:
- ❌ `<div style={{ color: '#3b82f6' }}>`
- ❌ Colori hex inline
- ❌ Valori pixel hardcoded (eccetto eccezioni puntuali)
- ❌ Variabili CSS non nei token

**Consentito**:
- ✅ Classi Tailwind (costruite sui token)
- ✅ Override token domain-specific (via plugin)
- ✅ Variabili semantiche Radix UI (es. `--accent-a11`)

---

### Articolo VIII — Silenzio Sopra Ambiguità

**Principio**: Se i dati sono incompleti, mancanti o ambigui, **non renderizzare nulla** piuttosto che indovinare o riempire con placeholder.

**Razionale**: Una sezione vuota è meglio di informazioni fuorvianti.

**Implementazione**:
```tsx
// ✅ BENE: Controllo null
{payload.evidence && <EvidenceSectionRenderer {...payload.evidence} />}

// ❌ MALE: Placeholder
{payload.evidence || <div>Nessuna evidenza disponibile (caricamento...)</div>}
```

**Proibito**:
- ❌ Placeholder "Caricamento..." per risposte statiche
- ❌ Valori default che mascherano fallimenti backend
- ❌ Dati sintetici "N/A"

**Consentito**:
- ✅ Skeleton loader per operazioni asincrone
- ✅ UI stato vuoto (quando esplicitamente segnalato dall'adapter)
- ✅ Error boundary

---

### Articolo IX — Registro Adapter come Single Source of Truth

**Principio**: La selezione dell'adapter deve passare attraverso `AdapterRegistry.selectAdapter()`. Nessuna istanziazione manuale di adapter nei componenti.

**Implementazione**:
```typescript
// ✅ BENE: Selezione basata su registro
const adapter = adapterRegistry.selectAdapter(conversation);
const payload = adapter.map(state);

// ❌ MALE: Istanziazione manuale adapter
const adapter = conversation.intent === "finance" 
  ? new FinanceAdapter() 
  : new ConversationalAdapter();
```

**Proibito**:
- ❌ Componenti che importano adapter direttamente
- ❌ Logica che duplica la funzione `match()`
- ❌ Bypass del registro

**Consentito**:
- ✅ Registrazione adapter al boot
- ✅ Adapter plugin di dominio auto-registrati
- ✅ Fallback a `ConversationalAdapter` se nessuna corrispondenza

---

### Articolo X — I Plugin di Dominio Estendono, Mai Modificano

**Principio**: Funzionalità domain-specific (finance, energy, facility) devono essere aggiunte via **plugin**, non modificando codice core.

**Implementazione**:
```typescript
// ✅ BENE: Sistema plugin
const financePlugin: DomainPlugin = {
  metadata: { id: 'finance-ui', domain: 'finance', version: '1.0.0' },
  adapters: [new FinanceSingleTickerAdapter()],
  vee_content: { /* registro VEE finance */ },
  hooks: { useTradingOrder, usePortfolioCanvas },
  theme_overrides: { colors: { primary: '#10b981' } }
};

domainPluginRegistry.register(financePlugin);

// ❌ MALE: Modifica core
// ui/components/response/VitruvyanResponseRenderer.jsx
if (payload.domain === "finance") {
  return <FinanceSpecificRenderer {...payload} />;
}
```

**Proibito**:
- ❌ Codice domain-specific nei componenti core
- ❌ Import condizionali basati sul dominio
- ❌ Feature flag per funzionalità di dominio

**Consentito**:
- ✅ Adapter di dominio in `vitruvyan_core/domains/<domain>/ui/`
- ✅ Registrazione plugin nel bootstrap app
- ✅ Hook di dominio nel manifest plugin

---

### Articolo XI — Paginazione Sopra Virtualizzazione (Quando Possibile)

**Principio**: Preferire paginazione a virtualizzazione per liste lunghe.

**Razionale**: La paginazione è più semplice, più accessibile e più facile da testare.

**Implementazione**:
```tsx
// ✅ BENE: Paginazione
<Accordion>
  {evidence.slice(page * 10, (page + 1) * 10).map(...)}
</Accordion>
<Pagination currentPage={page} onPageChange={setPage} />

// ❌ MALE: Virtualizzazione prematura
<VirtualizedList items={evidence} />
```

**Eccezioni**:
- Streaming real-time (messaggi chat, log)
- Dataset molto grandi (>500 elementi)

---

### Articolo XII — Ordinamento Epistemologico (Esempio Finance)

**Principio**: Le evidenze devono essere ordinate per **priorità epistemologica**, non convenienza visuale.

**Ordinamento Finance-specific**:
1. **Solidità** — Solidità bilancio
2. **Redditività** — Performance conto economico
3. **Crescita** — Potenziale futuro
4. **Risk** — Scenari negativi

**Razionale**: Addestrare gli utenti a leggere evidenze in ordine logico di dipendenza (non puoi valutare la crescita senza conoscere la redditività).

**Implementazione** (adapter):
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

**Proibito**:
- ❌ Ordinamento alfabetico
- ❌ Ordinamento per bilanciamento visuale (3 card per riga)
- ❌ Ordinamento personalizzabile dall'utente (rompe l'epistemologia)

---

### Articolo XIII — Read-Only per Default

**Principio**: La UI è **read-only** per default. Le operazioni di scrittura richiedono autenticazione esplicita, conferma e audit trail.

**Implementazione**:
- Tutti endpoint GET: Nessuna auth richiesta (read-only)
- Tutti POST/PUT/DELETE: OAuth/Keycloak richiesto
- Operazioni di scrittura mostrano dialog conferma con preview audit

**Proibito**:
- ❌ Mutazioni silenziose
- ❌ Update UI ottimistici senza rollback
- ❌ Operazioni di scrittura nei query hook

**Consentito**:
- ✅ Filtri client-side (nessuna mutazione backend)
- ✅ Stato UI locale (accordion aperto/chiuso)
- ✅ Hook di scrittura autenticati (espliciti)

---

### Articolo XIV — Progressiva Divulgazione

**Principio**: La densità di informazione deve aumentare con la profondità utente (superficiale → profondo).

**Livelli**:
1. **Narrativa** — Riepilogo alto livello (100-200 parole)
2. **Accordion Evidenze** — Metriche dettagliate (chiuse per default)
3. **VEE Deep Dive** — Explainability completa (on demand)

**Implementazione**:
```tsx
<NarrativeBlock>{payload.narrative}</NarrativeBlock>
<Accordion defaultValue="">
  {payload.evidence.map(section => <AccordionItem>...</AccordionItem>)}
</Accordion>
<VEEAccordions>{payload.vee_explanations}</VEEAccordions>
```

**Proibito**:
- ❌ Tutti accordion aperti per default
- ❌ Nascondere informazioni critiche dietro 4+ click
- ❌ VEE come tooltip inline (troppo distraente)

---

### Articolo XV — Accessibilità è Non-Negoziabile

**Principio**: Tutti i componenti devono soddisfare gli standard **WCAG 2.1 AA**.

**Requisiti**:
- Navigazione tastiera (Tab, Enter, Escape)
- Label screen reader (aria-label, aria-describedby)
- Contrasto colore ≥ 4.5:1 (testo), ≥ 3:1 (UI)
- Indicatori focus

**Implementazione**:
- Usare primitive Radix UI (accessibilità integrata)
- Testare con aXe DevTools
- Test tastiera ogni componente interattivo

**Proibito**:
- ❌ `<div onClick>` senza keyboard handler
- ❌ Informazioni solo-colore (aggiungere testo/icone)
- ❌ Rimozione outline focus

---

### Articolo XVI — Nessun Segreto Client-Side

**Principio**: API key, token e segreti non devono **mai** essere nel codice frontend.

**Implementazione**:
- Pattern Backend-for-Frontend (BFF)
- API key pubbliche devono essere scoped (read-only, rate-limited)
- Flusso OAuth gestito server-side

**Proibito**:
- ❌ `const API_KEY = "sk-..."`
- ❌ Token JWT hardcoded
- ❌ Variabili `.env` con key write-access

---

### Articolo XVII — Documentazione come Codice

**Principio**: Ogni adapter, plugin e componente principale deve avere:
1. **README.md** — Scopo, utilizzo, esempi
2. **Contenuto VEE** — Spiegazioni a 3 livelli
3. **Test** — Unit test per logica `map()`

**Razionale**: Codice non documentato è non manutenibile.

**Enforcement**:
- CI fallisce se nuovo adapter manca README
- Checklist PR richiede registrazione VEE
- Target copertura test: 80%

---

## Enforcement

Le violazioni costituzionali sono identificate da:

1. **Code review** — Ispezione manuale
2. **Linting** — Regole ESLint (es. no colori hardcoded)
3. **Architecture test** — Snapshot Jest registro adapter
4. **Audit documentazione** — Revisione trimestrale

**Penalità per violazione**: Il codice è rifiutato, indipendentemente dalla funzionalità.

---

## Processo di Emendamento

Questi articoli sono **immutabili** per v1.0 della UI. Per emendare:

1. Proporre emendamento in RFC (Request for Comments)
2. Dimostrare caso di fallimento dove articolo attuale blocca funzionalità critica
3. Ottenere approvazione unanime da team architettura UI
4. Incrementare versione costituzione (v1.0 → v2.0)

**Nota storica**: Questi principi sono derivati dalla Costituzione UI Mercator (Gen 2026), adattati per Vitruvyan OS domain-agnostic.

---

## Riferimenti

- [Costituzione UI](../../ui/docs/COSTITUZIONE_UI.md) — 17 articoli originali
- [Contratti](contracts.it.md) — Enforcement interfacce TypeScript
- [Stack](stack.it.md) — Scelte tecnologiche allineate ai principi
- [Panoramica UI](index.it.md) — Riferimento rapido

---

**Ultimo aggiornamento**: 20 Feb 2026 21:10 UTC
