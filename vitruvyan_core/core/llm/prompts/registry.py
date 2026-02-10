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
🎯 NEXT STEPS: [how to learn more]"""
}


def register_generic_domain() -> None:
    """Register the generic OS-level prompts as fallback domain."""
    PromptRegistry.register_domain(
        domain="generic",
        identity_template=GENERIC_IDENTITY,
        scenario_templates=GENERIC_SCENARIOS,
        template_vars=["assistant_name", "domain_description"],
        version="1.0",
        set_as_default=True
    )
