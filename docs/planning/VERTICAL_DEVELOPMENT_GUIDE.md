# Guida alla Costruzione di una Verticale su Vitruvyan Core

> **Last updated**: February 15, 2026  
> **Version**: 1.0  
> **Prerequisito**: Conoscenza base di Python 3.10+, FastAPI, e il pattern Plugin

---

## Indice

1. [Panoramica](#1-panoramica)
2. [Architettura del Sistema Plugin](#2-architettura-del-sistema-plugin)
3. [Quick Start — Verticale Minima (30 minuti)](#3-quick-start--verticale-minima-30-minuti)
4. [Guida Completa — Verticale Produzione](#4-guida-completa--verticale-produzione)
5. [Contratti e ABC disponibili](#5-contratti-e-abc-disponibili)
6. [Ricettario — Casi d'Uso Comuni](#6-ricettario--casi-duso-comuni)
7. [Testing della Verticale](#7-testing-della-verticale)
8. [Deployment (Docker + Service)](#8-deployment-docker--service)
9. [Checklist Pre-Rilascio](#9-checklist-pre-rilascio)
10. [Anti-Pattern da Evitare](#10-anti-pattern-da-evitare)
11. [Riferimenti](#11-riferimenti)

---

## 1. Panoramica

Vitruvyan Core è un **sistema operativo epistemico domain-agnostic**. Il core fornisce:

- Pipeline cognitiva (LangGraph) con 15+ nodi orchestrati
- Sacred Orders (Perception, Memory, Reason, Truth) come servizi governati
- Bus cognitivo (Redis Streams) per comunicazione asincrona
- Agenti singleton per accesso a PostgreSQL, Qdrant, LLM

Una **verticale** (domain vertical) è un pacchetto che aggiunge conoscenza e comportamento specifici di un dominio al core, **senza modificare il core stesso**.

### Cosa fornisce una verticale

| Componente | Responsabilità | Obbligatorio? |
|:---|:---|:---:|
| Intent Config | Definire gli intenti del dominio | **Sì** |
| Graph Plugin | Estendere la pipeline con nodi custom | No (consigliato) |
| Prompt Registry | Personalità e scenari LLM per il dominio | No (consigliato) |
| Slot Filler | Raccolta parametri mancanti via dialogo | No |
| Response Formatter | Formattazione output specifica | No |
| Entity Resolver | Mapping entità dominio-specifiche | No |
| Execution Handler | Logica di esecuzione custom | No |
| Governance Rules | Regole di compliance specifiche | No |
| Domain Contracts | Implementazioni di scoring, risk, explainability | No |

### Diagrama di integrazione

```
┌─────────────────────────────────────────────────────────┐
│                    VITRUVYAN CORE                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Pipeline  │  │  Sacred  │  │ Agents   │              │
│  │ LangGraph │  │  Orders  │  │ PG/QD/LLM│              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │              │              │                    │
│  ┌────┴──────────────┴──────────────┴────┐              │
│  │          contracts/ (ABCs)            │              │
│  │  BaseGraphState, GraphPlugin,         │              │
│  │  Parser, ILLMProvider, SlotFiller,    │              │
│  │  ResponseFormatter, BaseDomain        │              │
│  └────────────────┬──────────────────────┘              │
└───────────────────┼──────────────────────────────────────┘
                    │
          ┌─────────┴─────────┐
          │  domains/<tuo>/   │   ← La tua verticale
          │  intent_config.py │
          │  graph_plugin.py  │
          │  prompts/         │
          │  slot_filler.py   │
          │  ...              │
          └───────────────────┘
```

---

## 2. Architettura del Sistema Plugin

### Come il Core carica le verticali

Il caricamento è controllato da **variabili d'ambiente**:

| Env Var | Default | Funzione |
|:---|:---|:---|
| `INTENT_DOMAIN` | `generic` | Quale `intent_config.py` caricare |
| `ENTITY_DOMAIN` | (= `INTENT_DOMAIN`) | Quale `entity_resolver_config.py` caricare |
| `EXEC_DOMAIN` | — | Quale `execution_config.py` caricare |

Il meccanismo di caricamento (in `graph_flow.py`):

```python
# 1. Legge la variabile d'ambiente
domain = os.getenv("INTENT_DOMAIN", "generic")

# 2. Importa dinamicamente il modulo
module = importlib.import_module(f"domains.{domain}.intent_config")

# 3. Chiama la factory function
registry = module.create_{domain}_registry()

# 4. Carica opzionali
context_keywords = getattr(module, "CONTEXT_KEYWORDS", {})
ambiguous_patterns = getattr(module, "AMBIGUOUS_PATTERNS", {})
```

**Fallback**: se il dominio non esiste o l'import fallisce, usa `create_generic_registry()` (solo intent `soft` + `unknown`).

### PYTHONPATH

I servizi e il core usano `vitruvyan_core/` come root del PYTHONPATH. L'import `from domains.healthcare.intent_config import ...` funziona perché `vitruvyan_core/domains/` è sul path.

---

## 3. Quick Start — Verticale Minima (30 minuti)

Creiamo una verticale per il dominio **healthcare** come esempio.

### Passo 1: Creare la struttura

```bash
mkdir -p vitruvyan_core/domains/healthcare
touch vitruvyan_core/domains/healthcare/__init__.py
```

### Passo 2: `intent_config.py` (UNICO FILE OBBLIGATORIO)

```python
# vitruvyan_core/domains/healthcare/intent_config.py
"""
Healthcare Domain — Intent Configuration
==========================================
Minimum viable domain plugin for healthcare vertical.
"""

from core.orchestration.intent_registry import IntentRegistry, IntentDefinition, ScreeningFilter


def create_healthcare_registry() -> IntentRegistry:
    """Factory function — MUST be named create_{domain}_registry()."""
    
    registry = IntentRegistry(domain_name="healthcare")
    
    # --- Intenti del dominio ---
    
    registry.register_intent(IntentDefinition(
        name="symptom_check",
        description="Patient describes symptoms for triage assessment",
        examples=[
            "I have a headache and fever since yesterday",
            "My child has been coughing for three days",
        ],
        synonyms=["symptoms", "triage", "check_symptoms"],
        requires_entities=False,
        route_type="exec",
    ))
    
    registry.register_intent(IntentDefinition(
        name="medication_info",
        description="Questions about medications, dosages, interactions",
        examples=[
            "What are the side effects of ibuprofen?",
            "Can I take aspirin with metformin?",
        ],
        synonyms=["drug_info", "medicine", "pharma"],
        requires_entities=True,  # Richiede almeno un farmaco identificato
        route_type="exec",
    ))
    
    registry.register_intent(IntentDefinition(
        name="appointment",
        description="Scheduling, rescheduling, or canceling appointments",
        examples=[
            "I need to book an appointment with Dr. Smith",
            "Cancel my appointment for next Monday",
        ],
        synonyms=["booking", "schedule", "calendar"],
        requires_entities=False,
        route_type="exec",
    ))
    
    # --- Filtri (opzionali, per raffinamento) ---
    
    registry.register_filter(ScreeningFilter(
        name="urgency_level",
        description="How urgent is the medical need",
        value_type="enum",
        enum_values=["emergency", "urgent", "routine", "preventive"],
        keywords=["emergency", "urgent", "routine", "checkup"],
    ))
    
    registry.register_filter(ScreeningFilter(
        name="specialty",
        description="Medical specialty area",
        value_type="enum",
        enum_values=["general", "cardiology", "neurology", "pediatrics", "orthopedics"],
        keywords=["heart", "brain", "children", "bones", "general"],
    ))
    
    return registry


# --- Opzionali: keyword per validazione contesto professionale ---

CONTEXT_KEYWORDS = {
    "symptom_check": ["pain", "fever", "cough", "headache", "nausea", "fatigue"],
    "medication_info": ["dose", "mg", "tablet", "capsule", "prescription", "interaction"],
    "appointment": ["doctor", "clinic", "hospital", "schedule", "available"],
}

AMBIGUOUS_PATTERNS = {
    "too_vague": [
        r"^(help|info|question)$",
        r"^what should i do\??$",
    ],
}
```

### Passo 3: Attivare la verticale

```bash
# In .env o docker-compose.yml
INTENT_DOMAIN=healthcare
```

### Passo 4: Verificare

```python
# Test rapido
import os
os.environ["INTENT_DOMAIN"] = "healthcare"

from domains.healthcare.intent_config import create_healthcare_registry

registry = create_healthcare_registry()
print(f"Domain: {registry.domain_name}")
print(f"Intents: {registry.get_intent_labels()}")
print(f"Exec intents: {registry.get_exec_intent_names()}")
print(f"Soft intents: {registry.get_soft_intent_names()}")

# Output atteso:
# Domain: healthcare
# Intents: ['symptom_check', 'medication_info', 'appointment', 'soft', 'unknown']
# Exec intents: ['symptom_check', 'medication_info', 'appointment']
# Soft intents: ['soft']
```

**Fatto.** Con questo singolo file, la pipeline LangGraph riconosce i 3 intenti healthcare e li instraderà correttamente.

---

## 4. Guida Completa — Verticale Produzione

Una verticale per produzione richiede 5-8 componenti. Ecco la struttura obiettivo:

```
vitruvyan_core/domains/healthcare/
├── __init__.py                    # Package exports
├── intent_config.py               # ✅ Intenti e filtri (OBBLIGATORIO)
├── graph_plugin.py                # ✅ GraphPlugin — nodi, routing, stato
├── entity_resolver_config.py      # Hook per risoluzione entità
├── execution_config.py            # Hook per esecuzione comandi
├── governance_rules.py            # Regole di compliance
├── slot_filler.py                 # Raccolta parametri via dialogo
├── response_formatter.py          # Formattazione output
├── prompts/
│   └── __init__.py                # Identità LLM + scenari
└── README.md                      # Documentazione verticale
```

### 4.1 Graph Plugin (Estensione della Pipeline)

Il `GraphPlugin` è il cuore della verticale: definisce come il dominio estende la pipeline cognitiva.

```python
# vitruvyan_core/domains/healthcare/graph_plugin.py
"""Healthcare Graph Plugin — Extends the cognitive pipeline."""

from typing import Dict, Any, List, Tuple, Optional
from typing_extensions import TypedDict

from core.orchestration.graph_engine import GraphPlugin, NodeContract
from core.orchestration.base_state import BaseGraphState
from core.orchestration.parser import BaseParser, ParsedSlots


# --- 1. State Extension: campi aggiuntivi specifici del dominio ---

class HealthcareStateExtension(TypedDict, total=False):
    """Domain-specific state fields — merged with BaseGraphState."""
    patient_id: Optional[str]
    symptoms: Optional[List[str]]
    medications: Optional[List[str]]
    urgency_level: Optional[str]           # emergency|urgent|routine|preventive
    specialty: Optional[str]
    medical_history_context: Optional[str]
    triage_result: Optional[Dict[str, Any]]


# --- 2. Parser: estrazione parametri dal testo ---

class HealthcareParser(BaseParser):
    """
    Extracts healthcare-specific slots from user input.
    
    Inherits from BaseParser which provides:
    - detect_contextual_reference() (LLM-first)
    - detect_vague_query()
    - merge_slots_from_context()
    """
    
    def extract_slots(self, text: str, language: str = "en") -> ParsedSlots:
        """Extract healthcare entities from text."""
        slots = {}
        entities = []
        
        # La logica di estrazione vera delega all'LLM via pipeline
        # Qui si possono aggiungere hint strutturali
        
        return ParsedSlots(
            input_text=text,
            context_entities=entities,
            semantic_matches=[],
            is_contextual=False,
            slots=slots,
        )
    
    def validate_entity(self, entity: str) -> bool:
        """Validate that an entity is a recognized medical term."""
        # In produzione: lookup su database farmaci / ICD-10
        return bool(entity and len(entity) > 1)
    
    def get_company_map(self) -> Dict[str, str]:
        """Not used in healthcare — return empty."""
        return {}


# --- 3. Nodi custom (handler functions) ---

def symptom_triage_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Triage node — classifies symptom urgency.
    
    This node demonstrates a domain-specific cognitive step.
    In production, this would call the LLM for triage assessment.
    """
    symptoms = state.get("symptoms", [])
    
    # LLM-first: delegate triage classification to LLM
    # (in produzione, usa get_llm_agent())
    urgency = "routine"  # placeholder
    
    return {
        "urgency_level": urgency,
        "triage_result": {
            "symptoms_count": len(symptoms),
            "assessed_urgency": urgency,
        },
    }


def medication_lookup_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Medication information lookup.
    
    In production, queries a pharmaceutical database
    via domain-specific adapter.
    """
    medications = state.get("medications", [])
    
    return {
        "result": {
            "medications": medications,
            "interactions_checked": True,
        },
    }


# --- 4. GraphPlugin Implementation ---

class HealthcareGraphPlugin(GraphPlugin):
    """
    Healthcare vertical plugin.
    
    Registers domain-specific nodes, routes, state fields, and intents
    with the GraphEngine for pipeline assembly.
    """
    
    def get_domain_name(self) -> str:
        return "healthcare"
    
    def get_state_extensions(self) -> Dict[str, Any]:
        """Healthcare-specific state fields."""
        return HealthcareStateExtension.__annotations__
    
    def get_nodes(self) -> Dict[str, NodeContract]:
        """Domain nodes to add to the pipeline."""
        return {
            "symptom_triage": NodeContract(
                name="symptom_triage",
                handler=symptom_triage_node,
                description="Triage assessment based on symptoms",
                required_fields=["symptoms"],
                produced_fields=["urgency_level", "triage_result"],
                domain="healthcare",
            ),
            "medication_lookup": NodeContract(
                name="medication_lookup",
                handler=medication_lookup_node,
                description="Medication information and interactions",
                required_fields=["medications"],
                produced_fields=["result"],
                domain="healthcare",
            ),
        }
    
    def get_route_map(self) -> Dict[str, str]:
        """Mapping route → nodo target del dominio."""
        return {
            "symptom_triage": "symptom_triage",
            "medication_lookup": "medication_lookup",
        }
    
    def get_intents(self) -> List[str]:
        """Intenti riconosciuti dal dominio."""
        return ["symptom_check", "medication_info", "appointment"]
    
    def get_entry_pipeline(self) -> List[str]:
        """Nodi da inserire prima del routing."""
        return []  # Nessun nodo pre-routing custom
    
    def get_post_routing_edges(self) -> List[Tuple[str, str]]:
        """Archi aggiuntivi dopo il routing."""
        return [
            ("symptom_triage", "compose"),     # Triage → composizione risposta
            ("medication_lookup", "compose"),   # Lookup → composizione risposta
        ]
    
    def get_keywords(self) -> Dict[str, List[str]]:
        """Keyword per Sacred Orders (Orthodoxy, Vault)."""
        return {
            "sensitive_terms": ["diagnosis", "prescription", "prognosis"],
            "action_verbs": ["prescribe", "diagnose", "treat"],
            "disclaimer_required": ["medication", "dosage", "interaction"],
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Configurazione dominio."""
        return {
            "disclaimer_enabled": True,
            "triage_llm_model": "gpt-4o",  # Modello più potente per triage
        }


# --- Factory ---

def get_healthcare_plugin() -> HealthcareGraphPlugin:
    """Factory function for the healthcare plugin."""
    return HealthcareGraphPlugin()
```

### 4.2 Prompt Registry (Personalità LLM)

```python
# vitruvyan_core/domains/healthcare/prompts/__init__.py
"""Healthcare domain prompts — Identity and scenario templates."""

from core.llm.prompts.registry import PromptRegistry


def register_healthcare_prompts():
    """Register healthcare-specific prompts with the PromptRegistry."""
    
    PromptRegistry.register_domain(
        domain="healthcare",
        
        identity_template="""You are {assistant_name}, a medical information assistant.

IMPORTANT BOUNDARIES:
- You provide GENERAL health information, NOT medical diagnoses
- Always recommend consulting a qualified healthcare professional
- Never prescribe medications or replace medical advice
- Flag emergencies clearly with urgency indicators

COMMUNICATION STYLE:
- Empathetic and reassuring
- Use clear, non-technical language unless the user is a professional
- Always include disclaimers on medical information
- Adapt tone to urgency level (calm for routine, direct for urgent)

CAPABILITIES:
- Symptom triage (informational only, not diagnostic)
- Medication information (publicly available data)
- Appointment scheduling support
- Health education and prevention tips
""",
        
        scenario_templates={
            "symptom_assessment": """Assess the following symptoms and provide:
1. Possible general categories (NOT diagnoses)
2. Urgency level (emergency/urgent/routine/preventive)
3. Recommended next steps (always including "consult a doctor")
4. Red flags to watch for

Symptoms: {symptoms}
Context: {context}

DISCLAIMER: This is informational only. Not a medical diagnosis.""",
            
            "medication_info": """Provide general information about:
Medication: {medication}

Include:
1. General purpose/class
2. Common side effects (publicly available)
3. General interaction warnings
4. Standard disclaimers

IMPORTANT: Direct the user to their pharmacist/doctor for personalized advice.""",
            
            "appointment_assist": """Help the user with appointment management:
Request: {request}
Available context: {context}

Provide clear, actionable guidance.""",
        },
        
        translations={
            "it": {
                "identity": """Sei {assistant_name}, un assistente informativo per la salute.

LIMITI IMPORTANTI:
- Fornisci informazioni sanitarie GENERALI, NON diagnosi mediche
- Raccomanda sempre di consultare un professionista sanitario qualificato
- Non prescrivere mai farmaci né sostituire il parere medico
- Segnala chiaramente le emergenze con indicatori di urgenza

STILE COMUNICATIVO:
- Empatico e rassicurante
- Usa linguaggio chiaro e non tecnico
- Includi sempre i disclaimer sulle informazioni mediche
- Adatta il tono al livello di urgenza
""",
            },
        },
        
        version="1.0",
        set_as_default=False,  # Non sovrascrivere il dominio default
    )
```

### 4.3 Slot Filler (Raccolta Parametri)

```python
# vitruvyan_core/domains/healthcare/slot_filler.py
"""Healthcare Slot Filler — Emotion-aware parameter collection."""

from typing import Any, Dict, List

from core.orchestration.compose.slot_filler import (
    SlotFiller, SlotDefinition, SlotQuestion, SlotBundle
)


class HealthcareSlotFiller(SlotFiller):
    """
    Fills missing healthcare parameters via dialogue.
    
    Adapts questions based on language and detected emotion
    (e.g., anxious patients get more reassuring phrasing).
    """
    
    # --- Definizioni slot ---
    
    SLOT_DEFS = [
        SlotDefinition(
            name="urgency_level",
            display_name="Urgency",
            description="How urgent is the medical need",
            valid_values=["emergency", "urgent", "routine", "preventive"],
            default_value="routine",
            required_for_intents=["symptom_check"],
        ),
        SlotDefinition(
            name="symptom_duration",
            display_name="Duration",
            description="How long symptoms have been present",
            valid_values=None,  # Free text
            required_for_intents=["symptom_check"],
        ),
        SlotDefinition(
            name="specialty",
            display_name="Specialty",
            description="Medical specialty needed",
            valid_values=["general", "cardiology", "neurology", "pediatrics", "orthopedics"],
            required_for_intents=["appointment"],
        ),
    ]
    
    # --- Domande multilingua ---
    
    QUESTIONS = {
        "urgency_level": {
            "en": "How would you describe the urgency? (emergency, urgent, routine, or preventive)",
            "it": "Come descriveresti l'urgenza? (emergenza, urgente, routine, o preventivo)",
        },
        "symptom_duration": {
            "en": "How long have you been experiencing these symptoms?",
            "it": "Da quanto tempo hai questi sintomi?",
        },
        "specialty": {
            "en": "Which medical specialty are you looking for?",
            "it": "Quale specialità medica stai cercando?",
        },
    }
    
    # --- Adattamento emotivo ---
    
    EMOTION_TEMPLATES = {
        "anxious": {
            "en": "I understand this can be worrying. {question} Take your time.",
            "it": "Capisco che possa essere preoccupante. {question} Prenditi il tuo tempo.",
        },
        "frustrated": {
            "en": "I want to help you as quickly as possible. {question}",
            "it": "Voglio aiutarti il più velocemente possibile. {question}",
        },
    }
    
    def get_slot_definitions(self) -> List[SlotDefinition]:
        return self.SLOT_DEFS
    
    def check_missing_slots(self, current_slots: Dict[str, Any], intent: str) -> List[str]:
        missing = []
        for slot_def in self.SLOT_DEFS:
            if intent in slot_def.required_for_intents:
                if slot_def.name not in current_slots or current_slots[slot_def.name] is None:
                    if slot_def.default_value is None:  # No default → must ask
                        missing.append(slot_def.name)
        return missing
    
    def generate_question(
        self,
        slot_name: str,
        language: str,
        state: Dict[str, Any],
    ) -> SlotQuestion:
        lang = language if language in ("en", "it") else "en"
        base_question = self.QUESTIONS.get(slot_name, {}).get(lang, f"Please provide: {slot_name}")
        
        # Adatta all'emozione rilevata
        emotion = state.get("emotion_detected", "neutral")
        if emotion in self.EMOTION_TEMPLATES:
            template = self.EMOTION_TEMPLATES[emotion].get(lang, "{question}")
            question = template.format(question=base_question)
        else:
            question = base_question
        
        # Opzioni suggerite
        slot_def = next((s for s in self.SLOT_DEFS if s.name == slot_name), None)
        options = slot_def.valid_values if slot_def else None
        
        return SlotQuestion(
            slot_name=slot_name,
            question=question,
            options=options,
            is_required=True,
        )
    
    def generate_bundled_questions(
        self,
        slot_names: List[str],
        language: str,
        state: Dict[str, Any],
    ) -> SlotBundle:
        questions = [self.generate_question(s, language, state) for s in slot_names]
        lang = language if language in ("en", "it") else "en"
        
        if lang == "it":
            bundled = "Per aiutarti al meglio, ho bisogno di alcune informazioni:\n"
        else:
            bundled = "To help you best, I need a few details:\n"
        
        for i, q in enumerate(questions, 1):
            bundled += f"\n{i}. {q.question}"
        
        return SlotBundle(
            slots=slot_names,
            questions=questions,
            bundled_question=bundled,
        )
```

### 4.4 Response Formatter (Formattazione Output)

```python
# vitruvyan_core/domains/healthcare/response_formatter.py
"""Healthcare Response Formatter — Domain-specific output formatting."""

from typing import Any, Dict, Optional

from core.orchestration.compose.response_formatter import (
    ResponseFormatter, FormattedResponse, ConversationType, RawEngineOutput
)


class HealthcareResponseFormatter(ResponseFormatter):
    """
    Formats healthcare pipeline outputs for the end user.
    
    Handles:
    - Triage results with urgency coloring
    - Medication info with mandatory disclaimers
    - Appointment confirmations
    """
    
    DISCLAIMERS = {
        "en": "⚕️ This information is for educational purposes only. "
              "Always consult a qualified healthcare professional.",
        "it": "⚕️ Queste informazioni hanno solo scopo educativo. "
              "Consulta sempre un professionista sanitario qualificato.",
    }
    
    def format_response(
        self,
        raw_output: RawEngineOutput,
        conversation_type: ConversationType,
        language: str = "en",
        **kwargs,
    ) -> FormattedResponse:
        """Format the response with healthcare-specific structure."""
        
        intent = raw_output.intent or "unknown"
        lang = language if language in ("en", "it") else "en"
        disclaimer = self.DISCLAIMERS[lang]
        
        # Formattazione per tipo di intent
        if intent == "symptom_check":
            body = self._format_triage(raw_output, lang)
        elif intent == "medication_info":
            body = self._format_medication(raw_output, lang)
        else:
            body = raw_output.text or ""
        
        # Aggiungi disclaimer a tutti gli output medici
        full_text = f"{body}\n\n---\n{disclaimer}"
        
        return FormattedResponse(
            text=full_text,
            metadata={"domain": "healthcare", "intent": intent},
        )
    
    def _format_triage(self, output: RawEngineOutput, lang: str) -> str:
        data = output.data or {}
        urgency = data.get("urgency_level", "unknown")
        
        urgency_emoji = {
            "emergency": "🔴", "urgent": "🟠",
            "routine": "🟢", "preventive": "🔵",
        }.get(urgency, "⚪")
        
        return f"{urgency_emoji} **Urgency: {urgency.upper()}**\n\n{output.text or ''}"
    
    def _format_medication(self, output: RawEngineOutput, lang: str) -> str:
        return f"💊 **Medication Information**\n\n{output.text or ''}"
```

### 4.5 Entity Resolver Hook

```python
# vitruvyan_core/domains/healthcare/entity_resolver_config.py
"""Healthcare Entity Resolver — Maps medical terms to canonical entities."""

from core.orchestration.entity_resolver_registry import EntityResolverRegistry


def register_healthcare_entity_resolver():
    """
    Register healthcare-specific entity resolver.
    
    Called by graph_flow.py when ENTITY_DOMAIN=healthcare.
    Maps common names → canonical identifiers (ICD-10, ATC codes, etc.)
    """
    registry = EntityResolverRegistry()
    
    # Esempio: mapping sintomi → categorie ICD-10
    symptom_map = {
        "headache": {"code": "R51", "category": "nervous_system"},
        "fever": {"code": "R50.9", "category": "general"},
        "cough": {"code": "R05", "category": "respiratory"},
        "chest pain": {"code": "R07.9", "category": "cardiovascular"},
    }
    
    # Esempio: mapping farmaci → ATC codes
    medication_map = {
        "ibuprofen": {"atc": "M01AE01", "class": "NSAID"},
        "paracetamol": {"atc": "N02BE01", "class": "analgesic"},
        "metformin": {"atc": "A10BA02", "class": "antidiabetic"},
    }
    
    # Registra i resolver
    registry.register_resolver(
        domain="healthcare",
        resolver_fn=lambda entity: symptom_map.get(entity.lower(), None),
        entity_type="symptom",
    )
    
    registry.register_resolver(
        domain="healthcare",
        resolver_fn=lambda entity: medication_map.get(entity.lower(), None),
        entity_type="medication",
    )
    
    return registry
```

### 4.6 Governance Rules (Compliance)

```python
# vitruvyan_core/domains/healthcare/governance_rules.py
"""Healthcare Governance Rules — Orthodoxy compliance for medical domain."""


def get_domain_rules():
    """
    Return healthcare-specific compliance rules.
    
    These are evaluated by the orthodoxy_node to ensure
    responses meet medical information standards.
    """
    return (
        {
            "rule_id": "HC-001",
            "name": "no_diagnosis",
            "description": "Never provide definitive medical diagnoses",
            "severity": "critical",
            "patterns": [
                r"you have \w+",
                r"you are diagnosed with",
                r"this is definitely",
            ],
            "action": "reject_and_rephrase",
        },
        {
            "rule_id": "HC-002",
            "name": "disclaimer_required",
            "description": "All medical info must include disclaimer",
            "severity": "warning",
            "check": "response_must_contain_disclaimer",
            "action": "append_disclaimer",
        },
        {
            "rule_id": "HC-003",
            "name": "emergency_redirect",
            "description": "Emergency situations must redirect to 112/911",
            "severity": "critical",
            "trigger_keywords": ["overdose", "not breathing", "unconscious", "bleeding heavily"],
            "action": "prepend_emergency_notice",
        },
    )
```

---

## 5. Contratti e ABC Disponibili

### 5.1 Contratti del Core (obbligatorietà descritta per ciascuno)

| Contratto | Modulo | Metodi astratti | Quando implementare |
|:---|:---|:---:|:---|
| `GraphPlugin` | `core.orchestration.graph_engine` | 7 | Quando aggiungi nodi alla pipeline |
| `Parser` / `BaseParser` | `core.orchestration.parser` | 3 | Quando estrai parametri dal testo |
| `SlotFiller` | `core.orchestration.compose.slot_filler` | 3 | Quando raccogli parametri via dialogo |
| `ResponseFormatter` | `core.orchestration.compose.response_formatter` | 1 | Quando formatti l'output utente |
| `BaseDomain` | `domains.base_domain` | 7 | Quando registri un dominio formale |
| `ILLMProvider` | `core.contracts.llm_provider` | 5 | Solo se sostituisci OpenAI con un provider custom |
| `AggregationProvider` | `domains.aggregation_contract` | 5 | Per scoring/ranking personalizzati |
| `ExplainabilityProvider` | `domains.explainability_contract` | 7 | Per explainability personalizzata |
| `RiskProvider` | `domains.risk_contract` | 5 | Per valutazione rischio personalizzata |

### 5.2 GraphPlugin — Metodi obbligatori

```python
class GraphPlugin(ABC):
    @abstractmethod
    def get_domain_name(self) -> str: ...
    
    @abstractmethod
    def get_state_extensions(self) -> Dict[str, Any]: ...
    
    @abstractmethod
    def get_nodes(self) -> Dict[str, NodeContract]: ...
    
    @abstractmethod
    def get_route_map(self) -> Dict[str, str]: ...
    
    @abstractmethod
    def get_intents(self) -> List[str]: ...
    
    @abstractmethod
    def get_entry_pipeline(self) -> List[str]: ...
    
    @abstractmethod
    def get_post_routing_edges(self) -> List[Tuple[str, str]]: ...
    
    # Opzionali (con default):
    def get_keywords(self) -> Dict[str, List[str]]: return {}
    def get_config(self) -> Dict[str, Any]: return {}
```

### 5.3 BaseDomain — Metodi astratti

```python
class BaseDomain(ABC):
    @abstractmethod
    def get_domain_name(self) -> str: ...
    
    @abstractmethod
    def get_entity_schema(self) -> List[EntitySchema]: ...
    
    @abstractmethod
    def get_signal_types(self) -> List[SignalSchema]: ...
    
    @abstractmethod
    def get_scoring_factors(self) -> List[ScoringFactor]: ...
    
    @abstractmethod
    def get_policies(self) -> List[DomainPolicy]: ...
    
    @abstractmethod
    def validate_entity(self, entity_id: str) -> bool: ...
    
    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]: ...
    
    # Opzionale:
    def get_graph_plugin(self) -> Optional[GraphPlugin]: return None
```

### 5.4 BaseGraphState — Campi disponibili (37 campi base)

I campi sono organizzati in categorie:

| Categoria | Campi | Accesso |
|:---|:---|:---|
| Essential | `input_text`, `route`, `result`, `error`, `response`, `user_id` | `state["input_text"]` |
| Intent | `intent`, `needs_clarification`, `clarification_reason` | `state["intent"]` |
| Language | `language_detected`, `language_confidence`, `cultural_context`, `babel_status` | `state["language_detected"]` |
| Emotion | `emotion_detected`, `emotion_confidence`, `emotion_intensity`, ... | `state["emotion_detected"]` |
| Orthodoxy | `orthodoxy_status`, `orthodoxy_verdict`, `orthodoxy_findings`, ... | `state["orthodoxy_status"]` |
| Vault | `vault_status`, `vault_protection`, ... | `state["vault_status"]` |
| Tracing | `trace_id`, `semantic_matches`, `vsgs_status` | `state["trace_id"]` |
| CAN | `can_response`, `can_mode`, `final_response`, ... | `state["final_response"]` |

Il tuo dominio **estende** questi campi con i propri (via `get_state_extensions()`).

---

## 6. Ricettario — Casi d'Uso Comuni

### 6.1 Aggiungere un intent che richiede entità

```python
registry.register_intent(IntentDefinition(
    name="drug_interaction",
    description="Check interactions between multiple medications",
    examples=["Does aspirin interact with warfarin?"],
    requires_entities=True,   # ← Il pipeline chiederà entità se mancanti
    route_type="exec",
))
```

### 6.2 Aggiungere un intent "soft" (conversazionale, niente esecuzione)

```python
registry.register_intent(IntentDefinition(
    name="health_education",
    description="General health education questions",
    examples=["How does the immune system work?"],
    route_type="soft",   # ← Instraderà verso LLM conversazionale
))
```

### 6.3 Usare l'LLM da un nodo custom

```python
from core.agents.llm_agent import get_llm_agent

def my_domain_node(state: Dict[str, Any]) -> Dict[str, Any]:
    llm = get_llm_agent()
    
    # Completamento singolo
    response = llm.complete(
        prompt=f"Analyze: {state['input_text']}",
        system_prompt="You are a domain expert."
    )
    
    # Output JSON strutturato
    result = llm.complete_json(
        prompt=f"Extract entities from: {state['input_text']}",
        system_prompt="Return JSON with 'entities' array."
    )
    
    return {"result": result}
```

### 6.4 Emettere eventi sul bus cognitivo (StreamBus)

```python
from core.synaptic_conclave.transport.streams import StreamBus

def my_node_with_events(state: Dict[str, Any]) -> Dict[str, Any]:
    bus = StreamBus()
    
    # Emettere un evento dominio-specifico
    bus.emit("healthcare.triage.completed", {
        "patient_id": state.get("patient_id"),
        "urgency": state.get("urgency_level"),
        "trace_id": state.get("trace_id"),
    })
    
    return state
```

### 6.5 Accesso al database

```python
from core.agents.postgres_agent import PostgresAgent

def persistence_node(state: Dict[str, Any]) -> Dict[str, Any]:
    pg = PostgresAgent()
    
    # Query
    rows = pg.fetch("SELECT * FROM patients WHERE id = %s", (state["patient_id"],))
    
    # Insert transazionale
    with pg.transaction():
        pg.execute(
            "INSERT INTO consultations (patient_id, symptoms, urgency) VALUES (%s, %s, %s)",
            (state["patient_id"], str(state.get("symptoms")), state.get("urgency_level"))
        )
    
    return {"result": rows}
```

### 6.6 Registrare prompt multilingua

```python
PromptRegistry.register_domain(
    domain="healthcare",
    identity_template="You are {assistant_name}...",
    scenario_templates={
        "triage": "Assess symptoms: {symptoms}...",
        "education": "Explain {topic} in simple terms...",
    },
    translations={
        "it": {"identity": "Sei {assistant_name}..."},
        "es": {"identity": "Eres {assistant_name}..."},
    },
)

# Uso nei nodi:
identity = PromptRegistry.get_identity("healthcare", language="it", assistant_name="MediBot")
scenario = PromptRegistry.get_scenario("healthcare", "triage", language="en", symptoms="headache, fever")
combined = PromptRegistry.get_combined("healthcare", "triage", language="en", symptoms="...")
```

---

## 7. Testing della Verticale

### 7.1 Struttura test consigliata

```
tests/
└── verticals/
    └── healthcare/
        ├── __init__.py
        ├── test_intent_config.py      # Intent registration + classification
        ├── test_graph_plugin.py        # Plugin contract compliance
        ├── test_slot_filler.py         # Slot filling logic
        ├── test_response_formatter.py  # Output formatting
        └── conftest.py                 # Fixtures con importorskip
```

### 7.2 Conftest con guard (isolamento verticale)

```python
# tests/verticals/healthcare/conftest.py
import pytest

# Guard: skip tutti i test se il modulo non è installato
healthcare = pytest.importorskip(
    "domains.healthcare.intent_config",
    reason="Healthcare vertical not available"
)
```

### 7.3 Test intent_config

```python
# tests/verticals/healthcare/test_intent_config.py
import pytest

healthcare = pytest.importorskip("domains.healthcare.intent_config")


class TestHealthcareIntentConfig:
    """Verify healthcare intent registration contract."""
    
    def test_factory_returns_registry(self):
        registry = healthcare.create_healthcare_registry()
        assert registry.domain_name == "healthcare"
    
    def test_all_intents_registered(self):
        registry = healthcare.create_healthcare_registry()
        labels = registry.get_intent_labels()
        
        # Domain intents + core intents (soft, unknown)
        assert "symptom_check" in labels
        assert "medication_info" in labels
        assert "appointment" in labels
        assert "soft" in labels      # Core intent — always present
        assert "unknown" in labels   # Core intent — always present
    
    def test_exec_intents_have_route_type_exec(self):
        registry = healthcare.create_healthcare_registry()
        exec_intents = registry.get_exec_intent_names()
        
        assert "symptom_check" in exec_intents
        assert "medication_info" in exec_intents
        assert "appointment" in exec_intents
    
    def test_no_intent_name_collision_with_core(self):
        """Domain intents must not shadow core intents."""
        registry = healthcare.create_healthcare_registry()
        domain_intents = [i for i in registry.get_intent_labels() 
                         if i not in ("soft", "unknown")]
        
        assert "soft" not in domain_intents
        assert "unknown" not in domain_intents
    
    def test_classification_prompt_generation(self):
        """Verify prompt builds correctly for LLM."""
        registry = healthcare.create_healthcare_registry()
        prompt = registry.build_classification_prompt("I have a headache")
        
        assert "symptom_check" in prompt
        assert "medication_info" in prompt
        assert len(prompt) > 50
    
    def test_context_keywords_present(self):
        assert hasattr(healthcare, "CONTEXT_KEYWORDS")
        assert isinstance(healthcare.CONTEXT_KEYWORDS, dict)
    
    def test_filters_registered(self):
        registry = healthcare.create_healthcare_registry()
        filter_prompt = registry.build_filter_list_for_prompt()
        assert "urgency_level" in filter_prompt
```

### 7.4 Test isolamento multi-dominio

```python
def test_no_cross_domain_pollution():
    """Loading healthcare must not affect other domains."""
    from domains.healthcare.intent_config import create_healthcare_registry
    
    hc = create_healthcare_registry()
    
    # Se il finance è disponibile
    try:
        from domains.finance.intent_config import create_finance_registry
        fin = create_finance_registry()
        
        # Gli intenti devono essere disgiunti
        hc_intents = set(hc.get_exec_intent_names())
        fin_intents = set(fin.get_exec_intent_names())
        
        assert hc_intents.isdisjoint(fin_intents), \
            f"Intent collision: {hc_intents & fin_intents}"
    except ImportError:
        pass  # Finance non disponibile — OK
```

### 7.5 Esecuzione test

```bash
# Solo test della verticale healthcare
PYTHONPATH=vitruvyan_core:$PYTHONPATH pytest tests/verticals/healthcare/ -v

# Tutti i test (incluse tutte le verticali)
PYTHONPATH=vitruvyan_core:$PYTHONPATH pytest tests/ -v

# Verifica che il core funzioni SENZA la verticale (nessun import hard)
INTENT_DOMAIN=generic PYTHONPATH=vitruvyan_core:$PYTHONPATH pytest tests/ -v --ignore=tests/verticals/
```

---

## 8. Deployment (Docker + Service)

Se la verticale necessita di un servizio dedicato (API, listener, etc.), segui il pattern LIVELLO 2.

### 8.1 Struttura servizio

```
services/api_healthcare/
├── main.py              # < 100 righe (FastAPI bootstrap)
├── config.py            # os.getenv() centralizzato
├── adapters/
│   ├── bus_adapter.py   # Orchestrazione consumer LIVELLO 1 + StreamBus
│   └── persistence.py   # UNICO punto I/O (PostgresAgent, QdrantAgent)
├── api/
│   └── routes.py        # Endpoint HTTP sottili
├── models/
│   └── schemas.py       # Pydantic request/response
├── monitoring/
│   └── health.py        # Health check + metriche
├── streams_listener.py  # Consumer Redis Streams
├── Dockerfile
└── requirements.txt
```

### 8.2 Template `main.py` (< 50 righe)

```python
# services/api_healthcare/main.py
"""Healthcare API Service — LIVELLO 2"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, SERVICE_PORT
from api.routes import router
from core.middleware.auth import AuthMiddleware

logger = logging.getLogger("api_healthcare")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Healthcare service starting")
    yield
    logger.info("Healthcare service stopping")


app = FastAPI(
    title="Vitruvyan Healthcare API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
```

### 8.3 Docker Compose

```yaml
# In infrastructure/docker/docker-compose.yml (aggiungere)
  healthcare:
    build:
      context: ../../
      dockerfile: services/api_healthcare/Dockerfile
    container_name: core_healthcare
    ports:
      - "8030:8030"
    environment:
      - INTENT_DOMAIN=healthcare
      - POSTGRES_HOST=core_postgres
      - REDIS_HOST=core_redis
    depends_on:
      - core_postgres
      - core_redis
    networks:
      - vitruvyan_network
```

---

## 9. Checklist Pre-Rilascio

### Contratto Plugin

- [ ] `intent_config.py` presente con `create_{domain}_registry()` che ritorna `IntentRegistry`
- [ ] Tutti gli intenti hanno `name`, `description`, `examples` (almeno 2)
- [ ] Nessun nome intent collide con core (`soft`, `unknown`) o altri domini
- [ ] `route_type` corretto per ogni intent (`exec` o `soft`)
- [ ] Factory testata in isolamento (no Docker/Redis necessari)

### Isolamento

- [ ] Zero import da `core.governance.*` → `domains.{tuo}/` (flusso unidirezionale)
- [ ] Zero import cross-dominio: `domains.finance.*` in `domains.healthcare.*`
- [ ] Nessun `load_dotenv()` nel codice
- [ ] Nessun secret hardcoded
- [ ] Tutti i config via `os.getenv()`

### Testing

- [ ] Test intent registration (factory, labels, exec/soft, collision)
- [ ] Test classification prompt (genera correttamente)
- [ ] Test graph plugin (se presente) — tutti i metodi astratti implementati
- [ ] Test slot filler (se presente) — missing slots, question generation
- [ ] Test in `tests/verticals/{domain}/` con `importorskip` guard
- [ ] Test funzionano con `INTENT_DOMAIN=generic` (non rompono il core)

### Documentazione

- [ ] `README.md` nella directory del dominio
- [ ] Esempi eseguibili in `examples/`
- [ ] Charter/filosofia documentata (opzionale ma consigliato)

### Deployment (se servizio dedicato)

- [ ] `main.py` < 100 righe
- [ ] `config.py` centralizza tutti `os.getenv()`
- [ ] `Dockerfile` e `requirements.txt` presenti
- [ ] Health check endpoint (`/health`)
- [ ] Auth middleware integrato
- [ ] CORS middleware configurato

---

## 10. Anti-Pattern da Evitare

| ❌ Anti-Pattern | ✅ Pattern Corretto |
|:---|:---|
| Importare `from core.governance.orthodoxy_wardens...` nel dominio | Comunicare via StreamBus o contratti ABC |
| Hardcodare URL/password nel codice | Usare `os.getenv("VAR_NAME")` |
| Creare `OpenAI()` direttamente | Usare `from core.agents.llm_agent import get_llm_agent` |
| Usare regex come engine primario per intent detection | Delegare all'LLM; regex solo come fallback |
| Modificare file in `vitruvyan_core/core/` per il tuo dominio | Usare i contratti in `contracts/` ed estendere |
| Import cross-dominio (`from domains.finance...` in healthcare) | Ogni dominio è indipendente — comunica via bus |
| Importare `psycopg2` direttamente | Usare `PostgresAgent` via `core.agents.postgres_agent` |
| `load_dotenv()` in qualsiasi file | Mai — config solo via environment variables |
| Mettere logica di business nel `main.py` del servizio | Delegare ad `adapters/` e consumer LIVELLO 1 |
| Test che richiedono Docker/Redis/Postgres per il dominio | Test puri Python in LIVELLO 1, test infra solo in LIVELLO 2 |
| Nomi intent generici ("analyze", "process") | Nomi domain-qualified ("symptom_check", "drug_interaction") |
| Override forzato di `validated_entities` nel backend | Rispettare la lista validated dal client (anche se `[]`) |

---

## 11. Riferimenti

### Implementazioni di riferimento

| Dominio | Complessità | File | Scopo |
|:---|:---:|:---|:---|
| `domains/finance/` | Alta | 10 file, 2000+ righe | Verticale completa di produzione |
| `domains/energy/` | Minima | 2 file | Plugin minimo con 3 intenti |
| `domains/facility/` | Minima | 2 file | Plugin minimo con 3 intenti |
| `domains/dummy_test/` | Baseline | 2 file | Plugin assoluto minimo (1 intent) |

### Documentazione architetturale

- [SERVICE_PATTERN.md](../../services/SERVICE_PATTERN.md) — Template servizio LIVELLO 2
- [SACRED_ORDER_PATTERN.md](../../vitruvyan_core/core/governance/SACRED_ORDER_PATTERN.md) — Pattern Sacred Order
- [copilot-instructions.md](../../.github/copilot-instructions.md) — Regole invarianti del core
- [V1_0_RELEASE_AUDIT_FEB15_2026.md](V1_0_RELEASE_AUDIT_FEB15_2026.md) — Stato dell'arte V1.0

### Contratti ABC (codice sorgente)

- `vitruvyan_core/core/contracts/__init__.py` — Import point unico
- `vitruvyan_core/core/orchestration/graph_engine.py` — `GraphPlugin`, `NodeContract`, `GraphEngine`
- `vitruvyan_core/core/orchestration/intent_registry.py` — `IntentRegistry`, `IntentDefinition`
- `vitruvyan_core/core/orchestration/base_state.py` — `BaseGraphState` (37 campi)
- `vitruvyan_core/core/orchestration/parser.py` — `Parser`, `BaseParser`, `ParsedSlots`
- `vitruvyan_core/core/orchestration/compose/slot_filler.py` — `SlotFiller`, `SlotDefinition`
- `vitruvyan_core/core/orchestration/compose/response_formatter.py` — `ResponseFormatter`
- `vitruvyan_core/core/llm/prompts/registry.py` — `PromptRegistry`
- `vitruvyan_core/domains/base_domain.py` — `BaseDomain`, `EntitySchema`, `SignalSchema`

---

> **Nota finale**: La verticale *non modifica mai il core*. Se hai bisogno di una primitiva che non esiste nei contratti, apri una discussione per estendere le ABC — non fare workaround nel dominio.
