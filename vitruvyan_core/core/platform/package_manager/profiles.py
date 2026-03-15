"""
Installation Profiles — predefined package sets for 'vit setup'.

Profiles:
  - minimal:  Core only (graph + babel_gardens). ~2 GB.
  - standard: Core + neural engine. ~4 GB.
  - finance:  Standard + finance vertical + edge-dse. ~6 GB.
  - full:     Everything including beta packages. ~8 GB.
  - custom:   User picks individual packages.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class InstallProfile:
    """Definition of an installation profile."""
    name: str
    label: str
    description: str
    packages: List[str]  # Package CLI names to install (non-core only)
    size_estimate: str   # Human-readable disk estimate
    env_keys: List[str] = field(default_factory=list)  # Required env vars beyond defaults

    @property
    def summary(self) -> str:
        return f"{self.label} — {self.description} ({self.size_estimate})"


# ── Profile definitions ──────────────────────────────────────────

MINIMAL = InstallProfile(
    name="minimal",
    label="Minimal",
    description="Core kernel only (graph engine + sacred orders)",
    packages=[],
    size_estimate="~2 GB",
)

STANDARD = InstallProfile(
    name="standard",
    label="Standard",
    description="Core + Neural Engine for pattern analysis",
    packages=["neural_engine"],
    size_estimate="~4 GB",
)

FULL = InstallProfile(
    name="full",
    label="Full",
    description="All packages including beta (MCP, Edge DSE)",
    packages=["neural_engine", "mcp", "edge_dse"],
    size_estimate="~8 GB",
    env_keys=["POSTGRES_PASSWORD"],
)

CUSTOM = InstallProfile(
    name="custom",
    label="Custom",
    description="Choose individual packages to install",
    packages=[],
    size_estimate="varies",
)


# Ordered list for wizard display
ALL_PROFILES: List[InstallProfile] = [MINIMAL, STANDARD, FULL, CUSTOM]

PROFILES_BY_NAME: Dict[str, InstallProfile] = {p.name: p for p in ALL_PROFILES}



def get_profile(name: str) -> Optional[InstallProfile]:
    """Look up a profile by name."""
    return PROFILES_BY_NAME.get(name)


def list_profiles() -> List[InstallProfile]:
    """Return all available profiles in display order."""
    return list(ALL_PROFILES)
