"""
Vitruvyan Core — Intent Registry
=================================

Domain-agnostic intent registry for configuring intent detection.

The IntentRegistry allows domains to:
- Register their domain-specific intents
- Provide synonym mappings for intent normalization
- Configure GPT prompt templates for classification
- Define screening filter extraction rules

Philosophy:
----------
Intent detection remains LLM-first (GPT-3.5) but the prompt and
intent vocabulary are now domain-configurable via plugins.

Author: Vitruvyan Core Team
Created: February 10, 2026
Status: PRODUCTION
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ===========================================================================
# DATA CLASSES
# ===========================================================================

@dataclass
class IntentDefinition:
    """
    Definition of a single intent.
    
    Attributes:
        name: Canonical intent name (e.g., "trend", "risk", "allocate")
        description: Human-readable description for GPT prompt
        examples: Example queries that match this intent
        synonyms: Alternative names that map to this intent
        requires_entities: Whether this intent requires entity_ids
        requires_amount: Whether this intent requires a budget/amount
    """
    name: str
    description: str
    examples: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    requires_entities: bool = False
    requires_amount: bool = False


@dataclass
class ScreeningFilter:
    """
    Definition of a screening filter that can be extracted from queries.
    
    Attributes:
        name: Filter name (e.g., "risk_tolerance", "momentum_breakout")
        description: Human-readable description for GPT prompt
        value_type: Type of value ("enum", "bool", "string")
        enum_values: If value_type is "enum", the allowed values
        keywords: Keywords that trigger this filter
    """
    name: str
    description: str
    value_type: str = "bool"  # "bool", "enum", "string"
    enum_values: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


# ===========================================================================
# INTENT REGISTRY
# ===========================================================================

class IntentRegistry:
    """
    Registry for domain-specific intents and filters.
    
    Usage:
    
        registry = IntentRegistry(domain_name="my_domain")
        
        # Register domain intents
        registry.register_intent(IntentDefinition(
            name="analyze",
            description="Entity analysis",
            examples=["Analyze entity_123", "How is item_456 doing?"],
            synonyms=["study", "review"],
        ))
        
        # Register screening filters
        registry.register_filter(ScreeningFilter(
            name="priority_level",
            description="User priority preference",
            value_type="enum",
            enum_values=["low", "medium", "high"],
            keywords=["urgent", "normal", "low-priority"],
        ))
        
        # Generate GPT prompt dynamically
        prompt = registry.build_classification_prompt(user_input)
    """
    
    def __init__(self, domain_name: str = "generic"):
        """
        Initialize registry for a domain.
        
        Args:
            domain_name: Name of the domain (for logging/debugging)
        """
        self.domain_name = domain_name
        self._intents: Dict[str, IntentDefinition] = {}
        self._filters: Dict[str, ScreeningFilter] = {}
        self._synonyms: Dict[str, str] = {}  # synonym → canonical intent
        
        # Register core intents that all domains need
        self._register_core_intents()
    
    def _register_core_intents(self) -> None:
        """Register core intents available in all domains."""
        core_intents = [
            IntentDefinition(
                name="soft",
                description="Emotional/psychological queries, greetings, non-actionable",
                examples=["Hello", "I'm nervous", "Thanks"],
                synonyms=["greeting", "emotion"],
            ),
            IntentDefinition(
                name="unknown",
                description="Unclear or unrecognized requests",
                examples=["...", "hmm", "xyz123"],
            ),
        ]
        for intent in core_intents:
            self.register_intent(intent)
    
    def register_intent(self, intent: IntentDefinition) -> None:
        """
        Register an intent definition.
        
        Args:
            intent: IntentDefinition to register
        """
        self._intents[intent.name] = intent
        
        # Index synonyms
        for synonym in intent.synonyms:
            self._synonyms[synonym.lower()] = intent.name
        
        logger.debug(f"[IntentRegistry:{self.domain_name}] Registered intent: {intent.name}")
    
    def register_filter(self, filter_def: ScreeningFilter) -> None:
        """
        Register a screening filter.
        
        Args:
            filter_def: ScreeningFilter to register
        """
        self._filters[filter_def.name] = filter_def
        logger.debug(f"[IntentRegistry:{self.domain_name}] Registered filter: {filter_def.name}")
    
    def get_intent(self, name: str) -> Optional[IntentDefinition]:
        """Get intent definition by name."""
        return self._intents.get(name)
    
    def get_filter(self, name: str) -> Optional[ScreeningFilter]:
        """Get filter definition by name."""
        return self._filters.get(name)
    
    def normalize_intent(self, raw_intent: str) -> str:
        """
        Normalize intent via synonym mapping.
        
        Args:
            raw_intent: Raw intent string from classification
            
        Returns:
            Canonical intent name (or "unknown" if not found)
        """
        intent_lower = raw_intent.lower().strip()
        
        # Direct match
        if intent_lower in self._intents:
            return intent_lower
        
        # Synonym match
        if intent_lower in self._synonyms:
            return self._synonyms[intent_lower]
        
        return "unknown"
    
    def get_intent_labels(self) -> List[str]:
        """Get list of all registered intent names."""
        return list(self._intents.keys())
    
    def get_filter_names(self) -> List[str]:
        """Get list of all registered filter names."""
        return list(self._filters.keys())
    
    def build_intent_list_for_prompt(self) -> str:
        """
        Build intent list section for GPT prompt.
        
        Returns:
            Formatted string for prompt (e.g., "- trend: Entity analysis...")
        """
        lines = []
        for intent in self._intents.values():
            lines.append(f"- {intent.name}: {intent.description}")
        return "\n".join(lines)
    
    def build_filter_list_for_prompt(self) -> str:
        """
        Build filter extraction section for GPT prompt.
        
        Returns:
            Formatted string for prompt
        """
        lines = []
        for f in self._filters.values():
            if f.value_type == "enum":
                values = ", ".join(f'"{v}"' for v in f.enum_values)
                lines.append(f"- {f.name}: {f.description} ({values})")
            elif f.value_type == "bool":
                keywords = ", ".join(f.keywords[:5])  # First 5 keywords
                lines.append(f"- {f.name}: true if ({keywords})")
            else:
                lines.append(f"- {f.name}: {f.description}")
        return "\n".join(lines)
    
    def build_examples_for_prompt(self) -> str:
        """
        Build examples section for GPT prompt.
        
        Returns:
            Formatted string with intent examples
        """
        lines = []
        for intent in self._intents.values():
            for example in intent.examples[:2]:  # First 2 examples per intent
                lines.append(f'"{example}" → {{"intent": "{intent.name}"}}')
        return "\n".join(lines)
    
    def build_classification_prompt(
        self,
        user_input: str,
        include_filters: bool = True,
        include_examples: bool = True,
    ) -> str:
        """
        Build complete GPT classification prompt.
        
        Args:
            user_input: User query to classify
            include_filters: Whether to include filter extraction
            include_examples: Whether to include examples
            
        Returns:
            Complete prompt string for GPT
        """
        intent_list = self.build_intent_list_for_prompt()
        
        prompt_parts = [
            f"You are {self.domain_name}'s intent classification engine.",
            "Analyze the user's query and classify the intent.",
            "",
            "INTENT CATEGORIES:",
            intent_list,
            "",
        ]
        
        if include_filters and self._filters:
            filter_list = self.build_filter_list_for_prompt()
            prompt_parts.extend([
                "EXTRACT FILTERS (if applicable):",
                filter_list,
                "",
            ])
        
        if include_examples:
            examples = self.build_examples_for_prompt()
            prompt_parts.extend([
                "EXAMPLES:",
                examples,
                "",
            ])
        
        # Output format
        filter_json = ""
        if include_filters and self._filters:
            filter_json = ",\n  " + ",\n  ".join(
                f'"{f.name}": {self._filter_json_type(f)}'
                for f in self._filters.values()
            )
        
        prompt_parts.extend([
            f'Query: "{user_input}"',
            "",
            "Return ONLY valid JSON:",
            "{",
            f'  "intent": "category"{filter_json}',
            "}",
        ])
        
        return "\n".join(prompt_parts)
    
    def _filter_json_type(self, f: ScreeningFilter) -> str:
        """Get JSON type representation for filter."""
        if f.value_type == "bool":
            return "true|false"
        elif f.value_type == "enum":
            return "|".join(f'"{v}"' for v in f.enum_values) + "|null"
        else:
            return '"value"|null'
    
    def parse_classification_response(
        self,
        response: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Parse GPT classification response.
        
        Args:
            response: Parsed JSON from GPT
            
        Returns:
            Tuple of (normalized_intent, extracted_filters)
        """
        # Extract and normalize intent
        raw_intent = response.get("intent", "unknown")
        intent = self.normalize_intent(raw_intent)
        
        # Extract filters
        filters = {}
        for filter_name in self._filters:
            value = response.get(filter_name)
            if value is not None and value != "null":
                filters[filter_name] = value
        
        return intent, filters


# ===========================================================================
# FACTORY FUNCTIONS
# ===========================================================================

def create_generic_registry() -> IntentRegistry:
    """
    Create a generic intent registry with minimal intents.
    
    Returns:
        IntentRegistry with core intents only
    """
    return IntentRegistry(domain_name="generic")


# ===========================================================================
# EXPORTS
# ===========================================================================

__all__ = [
    "IntentRegistry",
    "IntentDefinition",
    "ScreeningFilter",
    "create_generic_registry",
]
