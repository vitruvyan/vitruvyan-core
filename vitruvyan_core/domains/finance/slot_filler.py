# vitruvyan_core/domains/finance/slot_filler.py
"""
FinanceSlotFiller - Finance-specific slot filling questions.

Extracts finance-specific slot logic from compose_node.py:
- Risk tolerance
- Time horizon
- Asset class preferences
- Emotion-aware question generation
"""

from typing import Any, Dict, List, Optional

from core.orchestration.compose.slot_filler import (
    SlotFiller,
    SlotDefinition,
    SlotQuestion,
    SlotBundle,
)


# Finance-specific slot definitions
FINANCE_SLOTS = [
    SlotDefinition(
        name="time_horizon",
        display_name="Investment Horizon",
        description="How long the user plans to hold investments",
        valid_values=["short", "medium", "long"],
        required_for_intents=["allocation", "portfolio_summary", "screening"],
    ),
    SlotDefinition(
        name="risk_tolerance",
        display_name="Risk Profile",
        description="User's risk preference",
        valid_values=["conservative", "moderate", "aggressive"],
        required_for_intents=["allocation", "portfolio_summary", "screening"],
    ),
    SlotDefinition(
        name="asset_class",
        display_name="Asset Class",
        description="Preferred asset class (stocks, bonds, ETFs, etc.)",
        valid_values=["stocks", "bonds", "etf", "funds", "crypto", "mixed"],
        required_for_intents=["screening", "allocation"],
    ),
    SlotDefinition(
        name="sector",
        display_name="Sector",
        description="Industry sector preference",
        valid_values=["tech", "finance", "healthcare", "energy", "consumer", "industrial"],
        required_for_intents=["screening"],
    ),
    SlotDefinition(
        name="investment_amount",
        display_name="Investment Amount",
        description="Amount to invest",
        required_for_intents=["allocation"],
    ),
]


# Default questions for slot filling (extracted from compose_node.py)
DEFAULT_QUESTIONS = {
    "time_horizon": {
        "en": "What's your investment time horizon?",
        "it": "Qual è il tuo orizzonte temporale di investimento?",
        "es": "¿Cuál es tu horizonte temporal de inversión?",
        "fr": "Quel est votre horizon d'investissement?",
    },
    "risk_tolerance": {
        "en": "What's your risk tolerance?",
        "it": "Qual è la tua tolleranza al rischio?",
        "es": "¿Cuál es tu tolerancia al riesgo?",
        "fr": "Quelle est votre tolérance au risque?",
    },
    "asset_class": {
        "en": "What type of assets are you interested in?",
        "it": "Che tipo di asset ti interessano?",
        "es": "¿Qué tipo de activos te interesan?",
        "fr": "Quel type d'actifs vous intéresse?",
    },
    "sector": {
        "en": "Which sector interests you most?",
        "it": "Quale settore ti interessa di più?",
        "es": "¿Qué sector te interesa más?",
        "fr": "Quel secteur vous intéresse le plus?",
    },
    "investment_amount": {
        "en": "How much are you looking to invest?",
        "it": "Quanto vorresti investire?",
        "es": "¿Cuánto deseas invertir?",
        "fr": "Combien souhaitez-vous investir?",
    },
}


# Emotion-adapted question templates
EMOTION_QUESTIONS = {
    "anxious": {
        "prefix": {
            "en": "I understand this can feel overwhelming. ",
            "it": "Capisco che questo possa sembrare complicato. ",
            "es": "Entiendo que esto puede parecer abrumador. ",
        },
        "suffix": {
            "en": " Take your time, there's no pressure.",
            "it": " Prenditi il tuo tempo, non c'è fretta.",
            "es": " Tómate tu tiempo, no hay prisa.",
        },
    },
    "excited": {
        "prefix": {
            "en": "Great enthusiasm! ",
            "it": "Grande entusiasmo! ",
            "es": "¡Gran entusiasmo! ",
        },
        "suffix": {
            "en": " Let's make sure we get this right.",
            "it": " Assicuriamoci di fare le cose per bene.",
            "es": " Asegurémonos de hacerlo bien.",
        },
    },
    "frustrated": {
        "prefix": {
            "en": "I appreciate your patience. ",
            "it": "Apprezzo la tua pazienza. ",
            "es": "Aprecio tu paciencia. ",
        },
        "suffix": {
            "en": " This will help me give you better insights.",
            "it": " Questo mi aiuterà a darti informazioni migliori.",
            "es": " Esto me ayudará a darte mejores perspectivas.",
        },
    },
    "curious": {
        "prefix": {
            "en": "",
            "it": "",
            "es": "",
        },
        "suffix": {
            "en": " I'm here to help you explore.",
            "it": " Sono qui per aiutarti ad esplorare.",
            "es": " Estoy aquí para ayudarte a explorar.",
        },
    },
}


class FinanceSlotFiller(SlotFiller):
    """
    Finance-specific slot filler.
    
    Implements SlotFiller ABC with finance-specific slots and
    emotion-aware question generation.
    """
    
    def __init__(self, slots: Optional[List[SlotDefinition]] = None):
        """
        Initialize the slot filler.
        
        Args:
            slots: Custom slot definitions (defaults to FINANCE_SLOTS)
        """
        self._slots = slots or FINANCE_SLOTS
        self._slot_map = {s.name: s for s in self._slots}
    
    def get_slot_definitions(self) -> List[SlotDefinition]:
        """Return all finance slot definitions."""
        return self._slots
    
    def check_missing_slots(
        self,
        current_slots: Dict[str, Any],
        intent: str,
    ) -> List[str]:
        """
        Check which required slots are missing for the given intent.
        """
        missing = []
        for slot in self._slots:
            if intent in slot.required_for_intents:
                value = current_slots.get(slot.name)
                if value is None or value == "":
                    missing.append(slot.name)
        return missing
    
    def generate_question(
        self,
        slot_name: str,
        language: str,
        state: Dict[str, Any],
    ) -> SlotQuestion:
        """
        Generate an emotion-aware question for a missing slot.
        """
        # Get base question
        questions = DEFAULT_QUESTIONS.get(slot_name, {})
        base_question = questions.get(language, questions.get("en", f"Please provide {slot_name}."))
        
        # Get slot definition for options
        slot_def = self._slot_map.get(slot_name)
        options = slot_def.valid_values if slot_def else None
        
        # Apply emotion adaptation
        emotion = state.get("emotion_detected", "neutral")
        question = self._adapt_for_emotion(base_question, emotion, language)
        
        return SlotQuestion(
            slot_name=slot_name,
            question=question,
            options=options,
            is_required=slot_def is not None and len(slot_def.required_for_intents) > 0,
        )
    
    def _adapt_for_emotion(
        self,
        question: str,
        emotion: str,
        language: str,
    ) -> str:
        """
        Adapt question text based on detected emotion.
        """
        emotion = emotion.lower() if emotion else "neutral"
        
        if emotion in EMOTION_QUESTIONS:
            templates = EMOTION_QUESTIONS[emotion]
            prefix = templates.get("prefix", {}).get(language, "")
            suffix = templates.get("suffix", {}).get(language, "")
            return f"{prefix}{question}{suffix}"
        
        return question
    
    def generate_bundled_questions(
        self,
        missing_slots: List[str],
        language: str,
        state: Dict[str, Any],
    ) -> SlotBundle:
        """
        Generate bundled questions for multiple missing slots.
        
        For finance, we create a natural-sounding combined question.
        """
        questions = [
            self.generate_question(slot, language, state)
            for slot in missing_slots
        ]
        
        # Create bundled question
        if len(missing_slots) == 1:
            bundled = questions[0].question
        elif len(missing_slots) == 2:
            connectors = {
                "en": " Also, ",
                "it": " Inoltre, ",
                "es": " Además, ",
                "fr": " De plus, ",
            }
            conn = connectors.get(language, connectors["en"])
            bundled = questions[0].question + conn.lower() + questions[1].question.lower()
        else:
            # For 3+ slots, use template
            intros = {
                "en": f"To help you better, I need a few details: ",
                "it": f"Per aiutarti meglio, ho bisogno di alcuni dettagli: ",
                "es": f"Para ayudarte mejor, necesito algunos detalles: ",
            }
            intro = intros.get(language, intros["en"])
            q_texts = [q.question for q in questions]
            bundled = intro + " ".join(q_texts)
        
        # Generate chain of thought
        cot = self.generate_chain_of_thought(
            state.get("slots", {}),
            missing_slots,
            state,
        )
        
        return SlotBundle(
            slots=missing_slots,
            questions=questions,
            bundled_question=bundled,
            chain_of_thought=cot,
        )
    
    def generate_chain_of_thought(
        self,
        current_slots: Dict[str, Any],
        missing_slots: List[str],
        state: Dict[str, Any],
    ) -> str:
        """
        Generate a chain-of-thought recap for finance context.
        
        Extracted from compose_node.py (_generate_chain_of_thought_clarification).
        """
        language = state.get("detected_language", "en")
        entity_ids = state.get("entity_ids", [])
        intent = state.get("intent", "")
        
        # Build what we know
        known_parts = []
        if entity_ids:
            known_parts.append(f"entities: {', '.join(entity_ids[:3])}" + 
                             ("..." if len(entity_ids) > 3 else ""))
        if intent:
            known_parts.append(f"intent: {intent}")
        for k, v in current_slots.items():
            if v is not None:
                known_parts.append(f"{k}: {v}")
        
        # Build templates
        templates = {
            "en": {
                "known": "Based on our conversation, I understand: ",
                "need": "To provide personalized advice, I still need to know: ",
            },
            "it": {
                "known": "In base alla nostra conversazione, ho capito: ",
                "need": "Per darti consigli personalizzati, ho ancora bisogno di sapere: ",
            },
            "es": {
                "known": "Basado en nuestra conversación, entiendo: ",
                "need": "Para darte consejos personalizados, todavía necesito saber: ",
            },
        }
        
        t = templates.get(language, templates["en"])
        
        if known_parts:
            cot = t["known"] + ", ".join(known_parts) + ". "
        else:
            cot = ""
        
        # Map slot names to friendly names
        slot_names = {
            "time_horizon": {"en": "investment horizon", "it": "orizzonte temporale", "es": "horizonte temporal"},
            "risk_tolerance": {"en": "risk tolerance", "it": "tolleranza al rischio", "es": "tolerancia al riesgo"},
            "asset_class": {"en": "preferred asset type", "it": "tipo di asset preferito", "es": "tipo de activo preferido"},
            "sector": {"en": "sector preference", "it": "preferenza settore", "es": "preferencia de sector"},
            "investment_amount": {"en": "investment amount", "it": "importo da investire", "es": "monto a invertir"},
        }
        
        friendly_missing = []
        for slot in missing_slots:
            names = slot_names.get(slot, {})
            friendly_missing.append(names.get(language, slot))
        
        cot += t["need"] + ", ".join(friendly_missing) + "."
        
        return cot
