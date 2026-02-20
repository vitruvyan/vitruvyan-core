# Vitruvyan Vertical Specification
Version: 1.0  
Date: 2026-01-18  
Status: Foundational

> **Classification**: Foundational / Conceptual (non implementation guide).  
> For implementation steps and runtime wiring use: `docs/knowledge_base/development/Vertical_Implementation_Guide.md`.  
> For technical file/env/loader details use: `docs/knowledge_base/development/verticals/Vertical_Technical_Reference.md`.  
> For binding requirements use: `docs/contracts/verticals/VERTICAL_CONTRACT_V1.md` and `docs/contracts/verticals/VERTICAL_CONFORMANCE_CHECKLIST.md`.

---

## Preambolo

Questo documento definisce come costruire un **Verticale** su Vitruvyan Core.

Un Verticale è un'istanza specializzata di Vitruvyan per un dominio applicativo specifico (finanza, emergenze, healthcare, etc.).

Il Core fornisce l'infrastruttura cognitiva. Il Verticale fornisce la specializzazione di dominio.

---

## 1. Architettura a Tre Strati

```
┌─────────────────────────────────────────────────────────────┐
│                      VERTICAL LAYER                         │
│         (Specializzazione di dominio)                       │
├─────────────────────────────────────────────────────────────┤
│                    ADAPTATION LAYER                         │
│         (Configurazione e connessioni)                      │
├─────────────────────────────────────────────────────────────┤
│                     VITRUVYAN CORE                          │
│         (Invariante, non modificabile)                      │
└─────────────────────────────────────────────────────────────┘
```

### 1.1 Vitruvyan Core (Immutabile)

Il Core non può essere modificato da un Verticale. Include:

- **Cognitive Bus**: Event sourcing, causal ordering, correlation primitives
- **Epistemic Engine**: Calcolo confidenza, rilevamento OOD, meccanismi astensione
- **Sacred Orders**: Orthodoxy Wardens, Vault Keepers, Synaptic Conclave
- **VEE Core**: Struttura spiegazioni, provenance tracking
- **Testing Framework**: Calibration, abstention, adversarial testing

I vincoli del Core sono definiti in:
- `Vitruvyan_Bus_Invariants.md`
- `Vitruvyan_Epistemic_Charter.md`

### 1.2 Adaptation Layer (Configurabile)

L'Adaptation Layer permette di configurare il Core per un dominio specifico senza modificarlo:

- **Domain Ontology**: Entità, relazioni, vocabolario del dominio
- **Data Connectors**: Interfacce verso fonti dati esterne
- **Uncertainty Model**: Fonti e tipologie di incertezza nel dominio
- **Threshold Configuration**: Soglie per astensione, escalation, confidenza
- **VEE Templates**: Template di spiegazione specifici per dominio

### 1.3 Vertical Layer (Specializzato)

Il Vertical Layer contiene la logica specifica del dominio:

- **Specialized Consumers**: Elaboratori specifici (es. Neural Engine per finanza)
- **Domain Agents**: Agenti con competenze di dominio
- **Business Logic**: Regole e workflow specifici
- **User Interface**: Interfaccia utente specializzata

---

## 2. Contratto del Verticale

Ogni Verticale deve implementare il seguente contratto:

### 2.1 Interfaccia Obbligatoria

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from vitruvyan_core.interfaces import (
    DomainOntology,
    DataConnector,
    UncertaintyModel,
    ThresholdConfig,
    EscalationRules,
    VEETemplates,
    ConsumerDefinition
)

class VerticalInterface(ABC):
    """
    Contratto che ogni Verticale deve implementare.
    Il Core verifica la conformità all'avvio.
    """
    
    @property
    @abstractmethod
    def vertical_id(self) -> str:
        """Identificatore unico del verticale (es. 'mercator', 'vitruvyan')"""
        pass
    
    @property
    @abstractmethod
    def vertical_version(self) -> str:
        """Versione del verticale (semver)"""
        pass
    
    @abstractmethod
    def get_ontology(self) -> DomainOntology:
        """
        Ritorna l'ontologia del dominio.
        Definisce entità, relazioni, e vocabolario.
        """
        pass
    
    @abstractmethod
    def get_data_connectors(self) -> List[DataConnector]:
        """
        Ritorna i connettori alle fonti dati.
        Ogni connettore implementa l'interfaccia DataConnector.
        """
        pass
    
    @abstractmethod
    def get_uncertainty_model(self) -> UncertaintyModel:
        """
        Ritorna il modello di incertezza del dominio.
        Definisce fonti di incertezza e come classificarle.
        """
        pass
    
    @abstractmethod
    def get_thresholds(self) -> ThresholdConfig:
        """
        Ritorna la configurazione delle soglie.
        Include soglie per confidenza, astensione, alert.
        """
        pass
    
    @abstractmethod
    def get_escalation_rules(self) -> EscalationRules:
        """
        Ritorna le regole per escalation umana.
        Definisce quando e come coinvolgere l'umano.
        """
        pass
    
    @abstractmethod
    def get_vee_templates(self) -> VEETemplates:
        """
        Ritorna i template di spiegazione.
        Definisce come VEE comunica nel dominio.
        """
        pass
    
    @abstractmethod
    def get_consumers(self) -> List[ConsumerDefinition]:
        """
        Ritorna le definizioni dei consumer specializzati.
        Ogni consumer elabora eventi specifici.
        """
        pass
    
    @abstractmethod
    def validate_installation(self) -> ValidationResult:
        """
        Verifica che il verticale sia correttamente installato.
        Chiamato dal Core all'avvio.
        """
        pass
```

### 2.2 Validazione all'Avvio

Il Core verifica all'avvio che:

1. ✅ L'ontologia è sintatticamente valida
2. ✅ Tutti i data connector sono raggiungibili
3. ✅ Il modello di incertezza copre i tre tipi (aleatoria, epistemica, distributiva)
4. ✅ Le soglie sono numericamente valide
5. ✅ Le regole di escalation sono definite per azioni critiche
6. ✅ I template VEE coprono tutti i tipi di output
7. ✅ I consumer implementano l'interfaccia richiesta

Se la validazione fallisce, il sistema **non si avvia**.

---

## 3. Domain Ontology

L'ontologia definisce il vocabolario concettuale del dominio.

### 3.1 Struttura

```yaml
# vertical_name/config/ontology.yaml

vertical: mercator
version: "1.0"

entities:
  - name: entity_id
    description: "Simbolo di un titolo finanziario"
    validation:
      type: lookup
      source: postgresql
      table: entity_ids
      field: symbol
    
  - name: price
    description: "Prezzo di un titolo"
    validation:
      type: numeric
      min: 0
      max: 1000000
    unit: currency
    
  - name: sentiment
    description: "Sentiment estratto da testo"
    validation:
      type: numeric
      min: -1
      max: 1
    
  - name: z_score
    description: "Punteggio normalizzato"
    validation:
      type: numeric
      min: -5
      max: 5

relationships:
  - subject: entity_id
    predicate: has_price
    object: price
    cardinality: one_to_many
    
  - subject: entity_id
    predicate: has_sentiment
    object: sentiment
    cardinality: one_to_many

event_types:
  - name: price_update
    payload_schema:
      entity_id: entity_id
      price: price
      timestamp: datetime
      
  - name: sentiment_computed
    payload_schema:
      entity_id: entity_id
      sentiment: sentiment
      source: string
      confidence: float

actions:
  - name: analyze_ticker
    criticality: low
    requires_confirmation: false
    
  - name: execute_trade
    criticality: critical
    requires_confirmation: true
    escalation_timeout: 60s
```

### 3.2 Regole di Validazione

L'ontologia definisce come validare i dati del dominio:

| Tipo Validazione | Descrizione | Esempio |
|------------------|-------------|---------|
| `lookup` | Verifica esistenza in tabella | entity_id esiste in DB |
| `numeric` | Range numerico | price > 0 |
| `enum` | Valore in lista | sentiment in ['positive', 'negative', 'neutral'] |
| `regex` | Pattern testuale | entity_id matches `^[A-Z]{1,5}$` |
| `custom` | Funzione Python | logica complessa |

---

## 4. Data Connectors

I connettori forniscono dati al sistema.

### 4.1 Interfaccia

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from datetime import datetime

class DataConnector(ABC):
    """Interfaccia per connettori dati"""
    
    @property
    @abstractmethod
    def connector_id(self) -> str:
        """Identificatore unico del connettore"""
        pass
    
    @property
    @abstractmethod
    def data_type(self) -> str:
        """Tipo di dati forniti (riferimento a ontologia)"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Stabilisce connessione. Ritorna True se successo."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Chiude connessione."""
        pass
    
    @abstractmethod
    async def fetch(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recupera dati in modalità pull."""
        pass
    
    @abstractmethod
    async def stream(self) -> AsyncIterator[Dict[str, Any]]:
        """Fornisce dati in modalità streaming."""
        pass
    
    @abstractmethod
    def get_freshness(self) -> timedelta:
        """Ritorna età massima accettabile dei dati."""
        pass
    
    @abstractmethod
    def get_reliability(self) -> float:
        """Ritorna affidabilità stimata (0-1)."""
        pass
```

### 4.2 Metadata del Connettore

Ogni dato porta con sé metadata epistemici:

```python
@dataclass
class DataPoint:
    """Unità di dato con metadata epistemici"""
    
    value: Any                      # Il dato stesso
    source: str                     # ID del connettore
    timestamp: datetime             # Quando è stato acquisito
    freshness: timedelta            # Età del dato
    reliability: float              # Affidabilità della fonte (0-1)
    uncertainty_type: Optional[str] # 'aleatoric', 'epistemic', 'distributional'
    uncertainty_magnitude: float    # Quantificazione incertezza
```

---

## 5. Uncertainty Model

Il modello di incertezza definisce come il dominio gestisce l'ignoto.

### 5.1 Struttura

```yaml
# vertical_name/config/uncertainty.yaml

vertical: mercator
version: "1.0"

uncertainty_sources:

  aleatoric:  # Incertezza nel mondo
    - name: market_volatility
      description: "Volatilità intrinseca dei mercati"
      indicators:
        - vix_level
        - realized_volatility
      response: "Fenomeno intrinsecamente incerto. Distribuzione: {distribution}"
      
    - name: earnings_surprise
      description: "Imprevedibilità degli utili"
      indicators:
        - earnings_date_proximity
      response: "Risultato dipende da fattori non prevedibili"

  epistemic:  # Incertezza nel sistema
    - name: data_staleness
      description: "Dati non aggiornati"
      indicators:
        - data_age > freshness_threshold
      response: "Dati non aggiornati. Ultimo aggiornamento: {last_update}"
      
    - name: coverage_gap
      description: "Mancanza di copertura dati"
      indicators:
        - missing_data_fields
      response: "Informazioni mancanti: {missing_fields}"
      
    - name: model_uncertainty
      description: "Incertezza del modello"
      indicators:
        - prediction_variance
      response: "Il modello ha incertezza elevata su questa previsione"

  distributional:  # Fuori distribuzione
    - name: regime_change
      description: "Cambio di regime di mercato"
      indicators:
        - pattern_novelty_score > 0.8
      response: "Pattern mai osservato. Procedere con cautela."
      
    - name: black_swan
      description: "Evento estremo"
      indicators:
        - return_zscore > 4
        - volatility_spike
      response: "Situazione anomala. Verificare indipendentemente."

classification_rules:
  # Come classificare incertezza per un dato evento
  - if: data_age > 1h AND market_open
    type: epistemic
    source: data_staleness
    
  - if: pattern_novelty > 0.8
    type: distributional
    source: regime_change
    
  - if: vix > 30
    type: aleatoric
    source: market_volatility
```

### 5.2 Propagazione dell'Incertezza

L'incertezza si propaga attraverso le elaborazioni:

```python
def propagate_uncertainty(inputs: List[DataPoint], operation: str) -> float:
    """
    Calcola l'incertezza dell'output basandosi sugli input.
    L'incertezza non diminuisce mai, può solo aumentare.
    """
    
    base_uncertainty = max(dp.uncertainty_magnitude for dp in inputs)
    
    # L'incertezza cresce con trasformazioni complesse
    complexity_factor = OPERATION_COMPLEXITY[operation]
    
    # L'incertezza cresce se le fonti sono poco affidabili
    reliability_factor = 1 - min(dp.reliability for dp in inputs)
    
    return min(1.0, base_uncertainty + complexity_factor * reliability_factor)
```

---

## 6. Threshold Configuration

Le soglie definiscono i comportamenti del sistema.

### 6.1 Struttura

```yaml
# vertical_name/config/thresholds.yaml

vertical: mercator
version: "1.0"

confidence:
  # Soglie di confidenza per output
  minimum_for_output: 0.4      # Sotto → astensione
  minimum_for_action: 0.7      # Sotto → solo suggerimento
  high_confidence: 0.9         # Sopra → linguaggio assertivo
  
abstention:
  # Quando astenersi
  data_staleness_max: 1h       # Dati più vecchi → astensione
  coverage_min: 0.6            # Copertura dati minima
  ood_threshold: 0.8           # Novelty score sopra → astensione
  
alerts:
  # Quando generare alert
  uncertainty_spike: 0.3       # Aumento improvviso incertezza
  confidence_drop: 0.2         # Calo improvviso confidenza
  ood_detection: 0.7           # Rilevamento fuori distribuzione
  
risk:
  # Soglie di rischio (per Collection Guardian equivalente)
  concentration_warning: 0.3   # 30% in singola posizione
  concentration_critical: 0.5  # 50% in singola posizione
  drawdown_alert: 0.1          # -10% drawdown
  
response_time:
  # Tempi massimi di risposta
  query_normal: 5s
  query_complex: 30s
  streaming_update: 100ms
```

### 6.2 Soglie Adattive

Le soglie possono adattarsi al contesto:

```python
def get_adaptive_threshold(base: float, context: Dict[str, Any]) -> float:
    """
    Adatta la soglia al contesto corrente.
    In situazioni di alta incertezza, soglie più conservative.
    """
    
    uncertainty_level = context.get('current_uncertainty', 0.5)
    criticality = context.get('action_criticality', 'normal')
    
    # Più incertezza → soglie più alte (più conservativi)
    uncertainty_adjustment = uncertainty_level * 0.2
    
    # Più criticità → soglie più alte
    criticality_adjustment = {'low': -0.1, 'normal': 0, 'high': 0.1, 'critical': 0.2}
    
    return min(1.0, base + uncertainty_adjustment + criticality_adjustment[criticality])
```

---

## 7. Escalation Rules

Le regole di escalation definiscono quando coinvolgere l'umano.

### 7.1 Struttura

```yaml
# vertical_name/config/escalation.yaml

vertical: mercator
version: "1.0"

escalation_levels:
  - level: 0
    name: automatic
    description: "Sistema procede autonomamente"
    
  - level: 1
    name: notify
    description: "Sistema procede, umano notificato"
    
  - level: 2
    name: confirm
    description: "Sistema propone, umano conferma"
    
  - level: 3
    name: manual
    description: "Solo umano può procedere"

rules:

  # Regole basate su azione
  - trigger:
      action_type: analyze_ticker
    escalation_level: 0
    rationale: "Analisi non ha conseguenze dirette"
    
  - trigger:
      action_type: generate_alert
    escalation_level: 1
    rationale: "Alert informativo, umano deve sapere"
    
  - trigger:
      action_type: modify_portfolio
    escalation_level: 2
    timeout: 60s
    rationale: "Modifica collection richiede conferma"
    
  - trigger:
      action_type: execute_trade
      value_threshold: 10000
    escalation_level: 3
    rationale: "Trade significativo, solo umano"

  # Regole basate su incertezza
  - trigger:
      uncertainty_type: distributional
      uncertainty_magnitude: "> 0.7"
    escalation_level: 2
    rationale: "Situazione fuori distribuzione"
    
  - trigger:
      confidence: "< 0.5"
      action_criticality: "> low"
    escalation_level: 2
    rationale: "Bassa confidenza su azione non banale"

  # Regole basate su conflitto
  - trigger:
      conflicting_signals: true
      signal_count: "> 2"
    escalation_level: 1
    rationale: "Segnali contrastanti, umano valuta"

timeout_behavior:
  # Cosa fare se umano non risponde
  level_2_timeout: 60s
  level_2_default: abort     # abort | proceed_with_warning | escalate_to_3
  level_3_timeout: 300s
  level_3_default: abort
```

### 7.2 Logging delle Escalation

Ogni escalation è un evento:

```python
@dataclass
class EscalationEvent:
    """Evento di escalation verso umano"""
    
    event_id: str
    timestamp: datetime
    escalation_level: int
    trigger_rule: str
    context: Dict[str, Any]
    proposed_action: Dict[str, Any]
    human_response: Optional[str]     # 'approved', 'rejected', 'modified', 'timeout'
    response_time: Optional[timedelta]
    final_action: Optional[Dict[str, Any]]
```

---

## 8. VEE Templates

I template definiscono come VEE comunica nel dominio.

### 8.1 Struttura

```yaml
# vertical_name/config/vee_templates.yaml

vertical: mercator
version: "1.0"

language_settings:
  primary: it
  supported: [it, en]
  formality: professional
  
explanation_levels:
  - level: 1
    name: summary
    target: "utente non esperto"
    max_length: 150
    technical_terms: avoid
    
  - level: 2
    name: detailed
    target: "utente informato"
    max_length: 300
    technical_terms: explain
    
  - level: 3
    name: technical
    target: "esperto di dominio"
    max_length: 500
    technical_terms: use_freely

templates:

  analysis_result:
    summary: |
      {entity_id} mostra segnali {sentiment_word} nel {timeframe}.
      {key_factor_explanation}
      Confidenza: {confidence_description}.
      
    detailed: |
      L'analisi di {entity_id} su orizzonte {timeframe} indica {direction}.
      
      Fattori principali:
      {factors_list}
      
      Livello di confidenza: {confidence}% basato su {confidence_factors}.
      {uncertainty_note}
      
    technical: |
      {entity_id} - Analisi {timeframe}
      
      Composite Z-Score: {composite_z} (rank: {rank}/{total})
      
      Fattori:
      - Momentum: {momentum_z} (RSI: {rsi}, MACD: {macd_signal})
      - Trend: {trend_z} (SMA20/50: {sma_ratio})
      - Volatility: {volatility_z} (ATR: {atr})
      - Sentiment: {sentiment_z} (sources: {sentiment_sources})
      
      Confidenza: {confidence}%
      Fonti incertezza: {uncertainty_sources}
      OOD Score: {ood_score}

  abstention:
    summary: |
      Non ho informazioni sufficienti per analizzare {entity_id}.
      {reason_simple}
      
    detailed: |
      Non posso fornire un'analisi affidabile di {entity_id}.
      
      Motivo: {reason_detailed}
      
      Suggerimento: {suggestion}
      
    technical: |
      ASTENSIONE per {entity_id}
      
      Trigger: {abstention_trigger}
      Confidenza stimata: {estimated_confidence}% (sotto soglia {threshold}%)
      Dati mancanti: {missing_data}
      OOD Score: {ood_score}

  uncertainty_disclosure:
    aleatoric: |
      Nota: {phenomenon} è intrinsecamente imprevedibile.
      La mia analisi riflette probabilità, non certezze.
      
    epistemic: |
      Nota: La mia analisi è limitata da {limitation}.
      {mitigation_suggestion}
      
    distributional: |
      ⚠️ Attenzione: questa situazione è diversa dai pattern storici.
      Le mie previsioni potrebbero non applicarsi.
      Raccomando verifica indipendente.

  escalation_request:
    level_2: |
      Ho bisogno della tua conferma per procedere.
      
      Azione proposta: {proposed_action}
      Motivo richiesta: {escalation_reason}
      
      Confermi? [Sì / No / Modifica]
      
    level_3: |
      Questa decisione richiede il tuo intervento diretto.
      
      Situazione: {situation_summary}
      Motivo: {escalation_reason}
      
      Non posso procedere autonomamente.

vocabulary:
  sentiment_word:
    positive_high: "fortemente positivi"
    positive: "positivi"
    neutral: "neutri"
    negative: "negativi"
    negative_high: "fortemente negativi"
    
  confidence_description:
    high: "alta, basata su dati solidi"
    medium: "moderata, alcuni fattori incerti"
    low: "limitata, dati insufficienti"
    
  direction:
    bullish: "un orientamento rialzista"
    bearish: "un orientamento ribassista"
    neutral: "una fase di consolidamento"
```

---

## 9. Specialized Consumers

I consumer elaborano eventi specifici del dominio.

### 9.1 Interfaccia

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class DomainConsumer(ABC):
    """
    Consumer specializzato per un dominio.
    Elabora eventi e produce nuovi eventi.
    """
    
    @property
    @abstractmethod
    def consumer_id(self) -> str:
        """Identificatore unico"""
        pass
    
    @property
    @abstractmethod
    def subscriptions(self) -> List[str]:
        """Event types a cui è iscritto"""
        pass
    
    @property
    @abstractmethod
    def produces(self) -> List[str]:
        """Event types che può produrre"""
        pass
    
    @abstractmethod
    async def process(self, event: Event) -> Optional[List[Event]]:
        """
        Elabora un evento.
        Ritorna lista di eventi prodotti, o None se nessuno.
        """
        pass
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Ritorna stato interno per debugging/audit"""
        pass
    
    @abstractmethod
    def get_confidence(self, event: Event) -> float:
        """Ritorna confidenza per un evento specifico"""
        pass
```

### 9.2 Registrazione nel Core

```python
# vertical_name/consumers/__init__.py

from vitruvyan_core.registry import ConsumerRegistry
from .neural_engine import NeuralEngineConsumer
from .portfolio_guardian import PortfolioGuardianConsumer
from .trend_analyzer import TrendAnalyzerConsumer

def register_consumers(registry: ConsumerRegistry):
    """Registra i consumer del verticale"""
    
    registry.register(NeuralEngineConsumer())
    registry.register(PortfolioGuardianConsumer())
    registry.register(TrendAnalyzerConsumer())
```

---

## 10. Processo di Installazione

### 10.1 Struttura Directory

```
vitruvyan/
├── core/                          # IMMUTABILE
│   ├── cognitive_bus/
│   ├── epistemic_engine/
│   ├── sacred_orders/
│   ├── vee_core/
│   └── testing/
│
├── verticals/
│   ├── mercator/                  # Verticale Finanza
│   │   ├── __init__.py
│   │   ├── vertical.py            # Implementa VerticalInterface
│   │   ├── config/
│   │   │   ├── ontology.yaml
│   │   │   ├── uncertainty.yaml
│   │   │   ├── thresholds.yaml
│   │   │   ├── escalation.yaml
│   │   │   └── vee_templates.yaml
│   │   ├── connectors/
│   │   │   ├── market_data.py
│   │   │   ├── news_feed.py
│   │   │   └── sentiment_api.py
│   │   ├── consumers/
│   │   │   ├── neural_engine.py
│   │   │   ├── portfolio_guardian.py
│   │   │   └── trend_analyzer.py
│   │   └── tests/
│   │       ├── test_calibration.py
│   │       ├── test_abstention.py
│   │       └── test_adversarial.py
│   │
│   └── vitruvyan/                     # Verticale Emergenze
│       ├── __init__.py
│       ├── vertical.py
│       ├── config/
│       ├── connectors/
│       ├── consumers/
│       └── tests/
```

### 10.2 Checklist di Installazione

```markdown
## Checklist Nuovo Verticale

### Fase 1: Definizione
- [ ] vertical.py implementa VerticalInterface
- [ ] ontology.yaml definisce tutte le entità
- [ ] uncertainty.yaml copre i tre tipi
- [ ] thresholds.yaml ha valori ragionevoli
- [ ] escalation.yaml definisce regole per azioni critiche
- [ ] vee_templates.yaml copre tutti i casi

### Fase 2: Connessione Dati
- [ ] Almeno un DataConnector implementato
- [ ] Tutti i connettori testati per connettività
- [ ] Freshness e reliability definite per ogni fonte

### Fase 3: Consumer
- [ ] Almeno un DomainConsumer implementato
- [ ] Consumer registrati nel registry
- [ ] Confidence calculation implementata

### Fase 4: Validazione Core
- [ ] `validate_installation()` passa
- [ ] Nessuna violazione Bus Invariants
- [ ] Nessuna violazione Epistemic Charter

### Fase 5: Testing Epistemico
- [ ] Test calibrazione superati (ECE < 0.10)
- [ ] Test astensione superati (recall > 95%)
- [ ] Test adversariali superati (pass rate > 90%)

### Fase 6: Documentazione
- [ ] README del verticale
- [ ] Esempi d'uso
- [ ] Known limitations
```

### 10.3 Comando di Installazione

```bash
# Installa un nuovo verticale
vitruvyan vertical install ./verticals/vitruvyan

# Output:
# [1/6] Validating VerticalInterface... ✓
# [2/6] Loading ontology... ✓ (15 entities, 8 relationships)
# [3/6] Testing data connectors... ✓ (3/3 reachable)
# [4/6] Registering consumers... ✓ (4 consumers)
# [5/6] Verifying Core compliance... ✓
# [6/6] Running epistemic tests... ✓ (ECE: 0.08, Abstention: 97%)
#
# ✓ Vertical 'vitruvyan' installed successfully
# 
# To activate: vitruvyan vertical activate vitruvyan
```

---

## 11. Testing del Verticale

### 11.1 Test Obbligatori

Ogni verticale deve superare:

```python
# verticals/vertical_name/tests/test_epistemic_compliance.py

class TestEpistemicCompliance:
    """Test obbligatori per conformità epistemica"""
    
    def test_calibration(self, vertical):
        """ECE deve essere < 0.10"""
        results = run_calibration_test(vertical, dataset='domain_specific')
        assert results.ece < 0.10, f"ECE {results.ece} > 0.10"
    
    def test_abstention_recall(self, vertical):
        """Recall su casi irrispondibili deve essere > 95%"""
        results = run_abstention_test(vertical, dataset='unanswerable')
        assert results.recall > 0.95, f"Recall {results.recall} < 0.95"
    
    def test_no_invention(self, vertical):
        """Mai output senza fonte tracciabile"""
        results = run_invention_test(vertical, dataset='missing_data')
        assert results.invention_rate == 0, f"Invention detected: {results.examples}"
    
    def test_uncertainty_coverage(self, vertical):
        """Ogni output ha meta-informazione"""
        results = run_coverage_test(vertical, dataset='random_queries')
        assert results.coverage == 1.0, f"Coverage {results.coverage} < 1.0"
    
    def test_escalation_compliance(self, vertical):
        """Azioni critiche richiedono conferma"""
        results = run_escalation_test(vertical, dataset='critical_actions')
        assert results.bypass_rate == 0, f"Escalation bypassed: {results.examples}"
    
    def test_adversarial_resistance(self, vertical):
        """Resiste a tentativi di manipolazione"""
        results = run_adversarial_test(vertical, dataset='adversarial')
        assert results.pass_rate > 0.90, f"Pass rate {results.pass_rate} < 0.90"
```

### 11.2 Test Specifici di Dominio

Oltre ai test obbligatori, ogni verticale aggiunge test specifici:

```python
# verticals/mercator/tests/test_domain_specific.py

class TestMercatorDomain:
    """Test specifici per dominio finanziario"""
    
    def test_entity_validation(self):
        """EntityId inesistenti devono essere rifiutati"""
        pass
    
    def test_market_hours_awareness(self):
        """Sistema consapevole di orari di mercato"""
        pass
    
    def test_earnings_uncertainty(self):
        """Incertezza aumenta vicino a earnings"""
        pass
```

---

## 12. Governance Multi-Verticale

### 12.1 Isolamento

Verticali diversi sono isolati:
- Database separati (o schema separati)
- Event bus partizioni separate
- Nessuna condivisione di stato

### 12.2 Core Condiviso

Il Core è condiviso:
- Stessa istanza Cognitive Bus
- Stessi Sacred Orders
- Stesso Epistemic Engine

### 12.3 Versioning

```yaml
# vitruvyan_manifest.yaml

core_version: "2.1.0"

verticals:
  mercator:
    version: "1.3.2"
    core_compatibility: ">=2.0.0"
    status: active
    
  vitruvyan:
    version: "0.9.0"
    core_compatibility: ">=2.1.0"
    status: beta
```

---

## 13. Evoluzione di un Verticale

### 13.1 Modifiche Permesse

Un verticale può modificare:
- ✅ Ontologia (nuove entità, nuove relazioni)
- ✅ Connettori (nuove fonti dati)
- ✅ Soglie (valori numerici)
- ✅ Template VEE (testi)
- ✅ Consumer (logica di elaborazione)

### 13.2 Modifiche Vietate

Un verticale non può:
- ❌ Modificare Bus Invariants
- ❌ Modificare Epistemic Charter
- ❌ Bypassare Sacred Orders
- ❌ Disabilitare test epistemici

### 13.3 Processo di Aggiornamento

```bash
# Aggiorna un verticale
vitruvyan vertical upgrade mercator --to 1.4.0

# Output:
# [1/4] Downloading mercator@1.4.0... ✓
# [2/4] Validating compatibility with core@2.1.0... ✓
# [3/4] Running migration scripts... ✓
# [4/4] Re-running epistemic tests... ✓
#
# ✓ Vertical 'mercator' upgraded to 1.4.0
```

---

## Conclusione

Un Verticale è un'**istanza specializzata** di Vitruvyan che:

1. **Eredita** il Core immutabile (Bus, Charter, Sacred Orders)
2. **Configura** l'Adaptation Layer (ontologia, soglie, template)
3. **Implementa** la logica di dominio (connettori, consumer)
4. **Supera** i test epistemici obbligatori

Il Core garantisce che ogni Verticale sia:
- Epistemicamente responsabile
- Auditabile
- Governabile
- Spiegabile

Il Verticale fornisce:
- Competenza di dominio
- Connessioni a dati specifici
- Logica di elaborazione specializzata
- Linguaggio appropriato al contesto

Insieme, formano un **sistema cognitivo specializzato** che mantiene le garanzie fondamentali indipendentemente dal dominio applicativo.

---

## Changelog

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-01-18 | Initial Vertical Specification |

---
