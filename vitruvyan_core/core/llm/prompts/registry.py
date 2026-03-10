# core/llm/prompts/registry.py
"""
🎯 Domain-Agnostic Prompt Registry

Allows domains to register their own prompts without hardcoding in core.
Core provides infrastructure; domains provide content.

Usage:
    # In domain module (e.g., domains/finance/__init__.py):
    from core.llm.prompts.registry import PromptRegistry
    
    PromptRegistry.register_domain("finance", {
        "identity": "You are a financial analyst...",
        "scenarios": {"analysis": "...", "recommendation": "..."}
    })
    
    # At runtime:
    prompt = PromptRegistry.get_prompt("finance", "analysis", "en")
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List, Callable
import logging

from vitruvyan_core.contracts.prompting import (
    PromptResolution,
    compute_prompt_hash,
    build_prompt_id,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PromptConfig:
    """Domain-agnostic prompt configuration."""
    
    domain: str
    version: str = "1.0"
    # Parametrized identity template
    identity_template: str = ""
    # Parametrized scenario templates
    scenario_templates: Dict[str, str] = field(default_factory=dict)
    # Language-specific overrides (lang -> section -> content)
    translations: Dict[str, Dict[str, str]] = field(default_factory=dict)
    # Template variables that the prompt expects
    template_vars: List[str] = field(default_factory=list)


class PromptRegistry:
    """
    Central registry for domain prompts.
    
    Domains register their prompts at startup; runtime code retrieves them.
    """
    
    _domains: Dict[str, PromptConfig] = {}
    _default_domain: Optional[str] = None
    
    @classmethod
    def register_domain(
        cls,
        domain: str,
        identity_template: str,
        scenario_templates: Dict[str, str],
        translations: Dict[str, Dict[str, str]] = None,
        template_vars: List[str] = None,
        version: str = "1.0",
        set_as_default: bool = False
    ) -> None:
        """
        Register a domain's prompts.
        
        Args:
            domain: Domain identifier (e.g., "finance", "healthcare", "legal")
            identity_template: Base identity prompt with {placeholders}
            scenario_templates: Dict of scenario_name -> prompt template
            translations: Optional lang -> section -> content overrides
            template_vars: List of expected template variable names
            version: Prompt version string
            set_as_default: If True, this becomes the fallback domain
        """
        config = PromptConfig(
            domain=domain,
            version=version,
            identity_template=identity_template,
            scenario_templates=scenario_templates or {},
            translations=translations or {},
            template_vars=template_vars or []
        )
        
        cls._domains[domain] = config
        logger.info(f"✅ Registered prompt domain: {domain} (v{version})")
        
        if set_as_default or cls._default_domain is None:
            cls._default_domain = domain
    
    @classmethod
    def get_identity(
        cls,
        domain: str,
        language: str = "en",
        **template_vars
    ) -> str:
        """
        Get identity prompt for a domain.
        
        Args:
            domain: Domain identifier
            language: Language code (en, it, es, etc.)
            **template_vars: Variables to substitute in template
            
        Returns:
            Formatted identity prompt
        """
        config = cls._get_config(domain)
        
        # Check for language-specific override
        if language in config.translations:
            if "identity" in config.translations[language]:
                template = config.translations[language]["identity"]
            else:
                template = config.identity_template
        else:
            template = config.identity_template
        
        # Substitute template variables
        try:
            return template.format(**template_vars)
        except KeyError as e:
            logger.warning(f"Missing template var {e} for domain {domain}")
            return template
    
    @classmethod
    def get_scenario(
        cls,
        domain: str,
        scenario: str,
        language: str = "en",
        **template_vars
    ) -> str:
        """
        Get scenario-specific prompt for a domain.
        
        Args:
            domain: Domain identifier
            scenario: Scenario name (e.g., "analysis", "recommendation")
            language: Language code
            **template_vars: Variables to substitute
            
        Returns:
            Formatted scenario prompt
        """
        config = cls._get_config(domain)
        
        # Check for language-specific override
        if language in config.translations:
            scenario_key = f"scenario_{scenario}"
            if scenario_key in config.translations[language]:
                template = config.translations[language][scenario_key]
            elif scenario in config.scenario_templates:
                template = config.scenario_templates[scenario]
            else:
                raise ValueError(f"Unknown scenario: {scenario}")
        elif scenario in config.scenario_templates:
            template = config.scenario_templates[scenario]
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
        
        try:
            return template.format(**template_vars)
        except KeyError as e:
            logger.warning(f"Missing template var {e} for scenario {scenario}")
            return template
    
    @classmethod
    def get_combined(
        cls,
        domain: str,
        scenario: str,
        language: str = "en",
        **template_vars
    ) -> str:
        """
        Get identity + scenario combined prompt.
        
        This is the typical usage pattern.
        """
        identity = cls.get_identity(domain, language, **template_vars)
        scenario_prompt = cls.get_scenario(domain, scenario, language, **template_vars)
        
        return f"""{identity}

--- SCENARIO ---

{scenario_prompt}"""
    
    @classmethod
    def resolve(
        cls,
        domain: str,
        scenario: str = "",
        language: str = "en",
        **template_vars,
    ) -> PromptResolution:
        """
        Resolve a prompt with full metadata for audit trail.

        Combines identity + scenario (if provided) and returns a
        PromptResolution with prompt_id, hash, version, and token estimate.

        This is the preferred entry point for new code. Existing methods
        (get_identity, get_scenario, get_combined) remain for backward
        compatibility.
        """
        config = cls._get_config(domain)
        actual_domain = config.domain
        fallback_used = actual_domain != domain

        if scenario:
            prompt_text = cls.get_combined(actual_domain, scenario, language, **template_vars)
        else:
            prompt_text = cls.get_identity(actual_domain, language, **template_vars)

        version = config.version
        prompt_id = build_prompt_id(actual_domain, scenario, version)
        prompt_hash = compute_prompt_hash(prompt_text)
        estimated_tokens = max(1, int(len(prompt_text.split()) * 1.3))

        return PromptResolution(
            system_prompt=prompt_text,
            domain=actual_domain,
            scenario=scenario,
            language=language,
            version=version,
            prompt_id=prompt_id,
            prompt_hash=prompt_hash,
            estimated_tokens=estimated_tokens,
            fallback_used=fallback_used,
        )

    @classmethod
    def list_domains(cls) -> List[str]:
        """List all registered domains."""
        return list(cls._domains.keys())
    
    @classmethod
    def list_scenarios(cls, domain: str) -> List[str]:
        """List available scenarios for a domain."""
        config = cls._get_config(domain)
        return list(config.scenario_templates.keys())
    
    @classmethod
    def get_default_domain(cls) -> Optional[str]:
        """Get the default domain identifier."""
        return cls._default_domain
    
    @classmethod
    def _get_config(cls, domain: str) -> PromptConfig:
        """Internal: get config or raise error."""
        if domain not in cls._domains:
            if cls._default_domain and cls._default_domain in cls._domains:
                logger.warning(f"Domain {domain} not found, using default: {cls._default_domain}")
                return cls._domains[cls._default_domain]
            raise ValueError(f"Domain {domain} not registered. Available: {cls.list_domains()}")
        return cls._domains[domain]
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registrations (for testing)."""
        cls._domains.clear()
        cls._default_domain = None


# ============================================================================
# Generic OS Prompts (domain-agnostic baseline)
# ============================================================================

GENERIC_IDENTITY = """You are {assistant_name}, an AI assistant specialized in {domain_description}.

PERSONALITY:
- Expert with deep knowledge in your domain
- Clear, professional communication
- Transparent about limitations
- Evidence-based reasoning

CONSTRAINTS:
- Provide analysis and insights, not personalized advice
- Always highlight uncertainties and limitations
- Suggest consulting domain experts for critical decisions
- Base conclusions on available data

FOCUS:
If asked about topics outside your domain:
"I specialize in {domain_description}. For other topics, please consult an appropriate expert."
"""

GENERIC_SCENARIOS = {
    "analysis": """OBJECTIVE: Provide comprehensive analysis.

FOCUS:
- Key metrics and indicators
- Patterns and trends
- Context and implications
- Risks and opportunities

FORMAT:
📊 KEY FINDINGS: [main observations]
🔍 ANALYSIS: [detailed breakdown]
📈 OUTLOOK: [expectations]
⚠️ CONSIDERATIONS: [risks and limitations]""",

    "recommendation": """OBJECTIVE: Transform analysis into actionable insights.

FOCUS:
- Prioritized options
- Trade-offs for each option
- Implementation considerations
- Risk mitigation

FORMAT:
✅ RECOMMENDATION: [primary suggestion]
💡 RATIONALE: [key supporting points]
⚖️ ALTERNATIVES: [other options]
⚠️ CONSIDERATIONS: [risks]""",

    "comparison": """OBJECTIVE: Compare options objectively.

FOCUS:
- Key differentiating factors
- Strengths and weaknesses
- Context-dependent trade-offs
- Suitability for different needs

FORMAT:
🏆 SUMMARY: [key differences]
📊 COMPARISON: [structured breakdown]
💡 CONTEXT: [situational considerations]
⚖️ TRADE-OFFS: [what you sacrifice with each choice]""",

    "overview": """OBJECTIVE: Provide big-picture understanding.

FOCUS:
- Current state and trends
- Key drivers and factors
- Emerging developments
- Important considerations

FORMAT:
🌍 CONTEXT: [current situation]
📊 KEY FACTORS: [main influences]
💡 DEVELOPMENTS: [what to watch]
⚠️ CONSIDERATIONS: [important caveats]""",

    "education": """OBJECTIVE: Explain concepts clearly for learning.

FOCUS:
- Core principles and concepts
- Practical examples
- Common misconceptions
- Next steps for learning

FORMAT:
📚 CONCEPTS: [foundational knowledge]
💡 EXAMPLES: [practical illustrations]
❓ MISCONCEPTIONS: [things often misunderstood]
🎯 NEXT STEPS: [how to learn more]""",

    "conversational": """You are an intelligent and friendly AI assistant. Respond naturally and professionally.
Adapt your tone and style to the user's language and emotional state.
Keep responses helpful, concise, and human.""",

    "synthesis": """You are synthesizing analysis results into natural language.
DO NOT calculate anything. Only explain pre-calculated results.
Present findings clearly and accessibly in the user's language.""",

    "mcp_tool_selection": """You are an epistemic reasoning assistant.
You MUST select and call the most appropriate tool to answer the user's question.
ALWAYS prefer calling a tool over answering directly — tools have access to live data that you don't.
When calling tools, only include tenant_id if the user explicitly mentions a specific tenant/client.
If the user asks about data for a LOCATION without specifying a tenant, do NOT include tenant_id — let the tool search across all tenants.
Note: Entity type and domain are deployment-configured.""",

    "early_exit": """You are a helpful conversational assistant.
Reply in 1-2 sentences, warm and professional.
Do NOT add any analysis, data, or suggestions.""",
}


def register_generic_domain() -> None:
    """Register the generic OS-level prompts as fallback domain."""
    PromptRegistry.register_domain(
        domain="generic",
        identity_template=GENERIC_IDENTITY,
        scenario_templates=GENERIC_SCENARIOS,
        translations={
            "it": {
                "scenario_conversational": (
                    "Sei un assistente AI intelligente e cordiale. "
                    "Rispondi in modo naturale e professionale. "
                    "Adatta il tono e lo stile alla lingua e allo stato emotivo dell'utente."
                ),
                "scenario_early_exit": (
                    "Sei un assistente conversazionale cordiale. "
                    "Rispondi in 1-2 frasi, in modo caloroso e professionale. "
                    "NON aggiungere analisi, dati o suggerimenti."
                ),
                "scenario_synthesis": (
                    "Stai sintetizzando risultati di analisi in linguaggio naturale. "
                    "NON calcolare nulla. Spiega solo risultati pre-calcolati. "
                    "Presenta i risultati in modo chiaro e accessibile."
                ),
            },
            "es": {
                "scenario_conversational": (
                    "Eres un asistente de IA inteligente y amigable. "
                    "Responde de forma natural y profesional. "
                    "Adapta tu tono y estilo al idioma y estado emocional del usuario."
                ),
                "scenario_early_exit": (
                    "Eres un asistente conversacional amigable. "
                    "Responde en 1-2 oraciones, cálido y profesional. "
                    "NO agregues análisis, datos o sugerencias."
                ),
            },
            "fr": {
                "scenario_conversational": (
                    "Tu es un assistant IA intelligent et amical. "
                    "Réponds naturellement et professionnellement. "
                    "Adapte ton ton et ton style à la langue et à l'état émotionnel de l'utilisateur."
                ),
            },
        },
        template_vars=["assistant_name", "domain_description"],
        version="1.0",
        set_as_default=True
    )
