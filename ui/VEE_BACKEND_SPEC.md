# VEE Backend Specification - ChatGPT Generation

**Data:** 30 Novembre 2025  
**Per:** Backend Team (compose_node.py / vee_generator.py)

---

## 🎯 Obiettivo

Il **backend DEVE sempre generare VEE via ChatGPT** e passare il testo al frontend tramite `final_state.narrative` o `final_state.vee_explanations[ticker].conversational`.

Il frontend ha generatori di fallback, ma **NON devono essere usati** in produzione.

---

## 📋 Cosa Deve Generare il Backend

### Campo da Popolare

\`\`\`python
# compose_node.py
state.narrative = chatgpt_generated_text  # PRIORITÀ 1

# OPPURE (se multi-ticker)
state.vee_explanations[ticker]["conversational"] = chatgpt_generated_text
\`\`\`

### Prompt ChatGPT per Generazione VEE

**Beginner Layer (Default per Chat):**

\`\`\`
Sei un analista finanziario educativo. Analizza questo ticker in modo semplice per utenti non esperti.

Dati:
- Ticker: {ticker}
- Momentum (z-score): {momentum_z}
- Trend (z-score): {trend_z}
- Volatility (z-score): {volatility_z}
- Sentiment: {sentiment_direction}
- Composite Score: {composite_score}

Genera una spiegazione di 2-3 frasi in italiano, stile:
- Semplicità assoluta
- Nessun tecnicismo
- Linguaggio: "Il titolo mostra momentum [positivo/neutrale/negativo], trend [forte/debole], volatilità [contenuta/normale/instabile]"
- Sentiment [positivo/negativo/neutrale]
- Quadro complessivo [positivo/neutrale/negativo]

Esempio output:
"Apple (AAPL) mostra momentum positivo, un trend forte e volatilità contenuta. Il sentiment è positivo. Il quadro complessivo è costruttivo."

Regole:
- NON dare consigli di acquisto/vendita
- NON inventare numeri
- Tono didattico ed elegante (Palantir/Victorian)
\`\`\`

---

## 📊 Interpretazione Z-Score per ChatGPT

**Fornisci questa tabella a ChatGPT:**

| Z-Score | Interpretazione |
|---------|-----------------|
| ≥ 1.5   | Estremamente forte |
| 0.5–1.5 | Forte |
| -0.5–0.5| Neutrale |
| -1.5–-0.5| Debole |
| ≤ -1.5  | Estremamente debole |

**Volatility:**
- z ≤ -0.5: "volatilità contenuta (calma)"
- -0.5 < z ≤ 0.5: "volatilità normale"
- z > 0.5: "volatilità elevata (instabile)"

**Sentiment:**
- bullish → "positivo"
- bearish → "negativo"
- neutral → "neutrale"

**Composite Score:**
- score ≥ 0.3 → "positivo"
- -0.3 ≤ score < 0.3 → "neutrale"
- score < -0.3 → "negativo"

---

## 🧪 Esempio Completo Backend → Frontend

### Backend Output (compose_node.py):

\`\`\`python
state.narrative = """
PLD mostra momentum positivo, un trend forte e volatilità contenuta. 
Il sentiment è leggermente positivo. Il quadro complessivo è costruttivo.
"""

# oppure per multi-ticker:
state.vee_explanations = {
    "AAPL": {
        "conversational": "Apple mostra momentum forte...",
        "beginner": "...",
        "intermediate": "...",
        "technical": "..."
    }
}
\`\`\`

### Frontend Display (ComposeNodeUI):

\`\`\`jsx
// Prende state.narrative e lo mostra nella box blu
<div className="bg-gradient-to-br from-blue-50 to-indigo-50">
  <Brain icon />
  {narrative}  {/* ← Testo generato da ChatGPT */}
</div>
\`\`\`

---

## ⚠️ Fallback Frontend (Emergenza)

Se il backend **non riesce** a generare VEE (ChatGPT down, timeout, error), il frontend ha generatori di emergenza:

\`\`\`javascript
// lib/utils/veeGenerator.js
generateBeginnerLayer(numericalPanel)
\`\`\`

**Questo genera testo basico tipo:**
> "Il titolo mostra momentum positivo, un trend forte e volatilità contenuta. Il sentiment è positivo. Il quadro complessivo è positivo."

Ma è **meno elegante e contestuale** rispetto a ChatGPT.

---

## 📘 3 Layer VEE (Future Enhancement)

In futuro, il backend dovrebbe generare anche:

1. **Beginner Layer** (già implementato sopra)
2. **Intermediate Layer** (educational, z-score explanation)
3. **Technical Layer** (entry/exit zones, market regime)

Per ora, **focus su Beginner Layer** nella chat conversazionale.

Gli altri 2 layer saranno in Market Intelligence section.

---

## ✅ Checklist Backend

- [ ] `compose_node.py` chiama ChatGPT per generare narrative
- [ ] Usa prompt sopra con interpretazioni z-score corrette
- [ ] Popola `state.narrative` o `state.vee_explanations[ticker].conversational`
- [ ] Testo in italiano, 2-3 frasi, stile educational
- [ ] Non dare consigli buy/sell
- [ ] Gestire timeout ChatGPT (fallback a stato vuoto, frontend gestisce)

---

## 🔗 Riferimenti

- Frontend: `components/nodes/ComposeNodeUI.jsx`
- Fallback: `lib/utils/veeGenerator.js`
- Utils: `lib/utils/veeUtils.js`

---

**Conclusione:**

Il frontend è pronto a ricevere VEE da ChatGPT. Il backend deve popolare `state.narrative` con testo generato via LLM usando le interpretazioni z-score fornite.
