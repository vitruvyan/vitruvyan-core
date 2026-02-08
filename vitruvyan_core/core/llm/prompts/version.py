# core/prompts/version.py
"""
🎯 Prompt Version Management

Gestisce versioning dei prompt per:
- A/B testing
- Rollback rapidi
- Tracking evoluzione nel tempo

Usage:
    from core.prompts.version import ACTIVE_PROMPT_VERSION
    
    # Per testare nuova versione:
    # ACTIVE_PROMPT_VERSION = "1.1"
    
    # Per rollback:
    # git revert <commit-hash>

Version History:
- 1.0 (2025-10-31): Initial release with base + scenario prompts
"""

ACTIVE_PROMPT_VERSION = "1.0"

AVAILABLE_VERSIONS = {
    "1.0": {
        "release_date": "2025-10-31",
        "description": "Initial prompt system with base + 6 scenario types",
        "changes": [
            "Base identity prompt (Vitruvyan personality)",
            "6 scenario prompts (analysis, recommendation, market, collection, comparison, onboarding)",
            "Multi-language support (IT, EN, ES)"
        ],
        "performance": {
            "avg_tokens": 450,
            "quality_score": None,  # To be measured
            "cost_per_call": 0.00034  # GPT-4o-mini estimate
        }
    }
}


def get_prompt_version() -> str:
    """Get currently active prompt version."""
    return ACTIVE_PROMPT_VERSION


def list_available_versions() -> list[str]:
    """List all available prompt versions."""
    return list(AVAILABLE_VERSIONS.keys())


def get_version_info(version: str) -> dict:
    """
    Get detailed information about a prompt version.
    
    Args:
        version: Version string (e.g., "1.0")
        
    Returns:
        Dict with version metadata
        
    Raises:
        ValueError: If version not found
    """
    if version not in AVAILABLE_VERSIONS:
        raise ValueError(f"Version {version} not found. Available: {list_available_versions()}")
    
    return AVAILABLE_VERSIONS[version]


def compare_versions(v1: str, v2: str) -> dict:
    """
    Compare two prompt versions.
    
    Useful for understanding changes between versions.
    """
    info1 = get_version_info(v1)
    info2 = get_version_info(v2)
    
    return {
        "v1": {
            "version": v1,
            "date": info1["release_date"],
            "changes": info1["changes"]
        },
        "v2": {
            "version": v2,
            "date": info2["release_date"],
            "changes": info2["changes"]
        },
        "token_diff": info2["performance"]["avg_tokens"] - info1["performance"]["avg_tokens"],
        "cost_diff": info2["performance"]["cost_per_call"] - info1["performance"]["cost_per_call"]
    }
