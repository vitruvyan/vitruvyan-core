"""
Bootstrap — prerequisite checker and .env generator for first-run setup.

Checks:
  - Docker daemon running
  - Docker Compose available
  - Python version ≥ 3.10
  - Infrastructure containers (redis, postgres, qdrant) reachable
  - Required ports available
  - .env file exists with required keys
"""

import os
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class PrereqResult:
    """Result of a single prerequisite check."""
    name: str
    passed: bool
    message: str
    required: bool = True


@dataclass
class BootstrapReport:
    """Aggregated prerequisite check results."""
    checks: List[PrereqResult] = field(default_factory=list)

    @property
    def all_required_passed(self) -> bool:
        return all(c.passed for c in self.checks if c.required)

    @property
    def summary_lines(self) -> List[str]:
        lines = []
        for c in self.checks:
            icon = "✅" if c.passed else ("❌" if c.required else "⚠️")
            lines.append(f"  {icon} {c.name}: {c.message}")
        return lines


# Default ports (fallback if docker-compose.yml cannot be parsed)
DEFAULT_INFRA_PORTS = {
    "redis": 6379,
    "postgres": 5432,
    "qdrant_rest": 6333,
    "qdrant_grpc": 6334,
}

# Map compose service names to our check names + internal ports
_COMPOSE_SERVICE_MAP = {
    "redis":   {"check_name": "redis",       "internal_port": 6379},
    "postgres":{"check_name": "postgres",    "internal_port": 5432},
    "qdrant":  {"check_name": "qdrant_rest", "internal_port": 6333, "extra": {"qdrant_grpc": 6334}},
}

# Default env template for first-run
ENV_TEMPLATE: Dict[str, Tuple[str, str]] = {
    # key: (default_value, description)
    "OPENAI_API_KEY": ("", "OpenAI API key (required for LLM features)"),
    "POSTGRES_USER": ("vitruvyan", "PostgreSQL username"),
    "POSTGRES_PASSWORD": ("", "PostgreSQL password"),
    "POSTGRES_DB": ("vitruvyan_db", "PostgreSQL database name"),
    "POSTGRES_HOST": ("localhost", "PostgreSQL host"),
    "POSTGRES_PORT": ("5432", "PostgreSQL port"),
    "REDIS_HOST": ("localhost", "Redis host"),
    "REDIS_PORT": ("6379", "Redis port"),
    "QDRANT_HOST": ("localhost", "Qdrant host"),
    "QDRANT_PORT": ("6333", "Qdrant REST port"),
    "LOG_LEVEL": ("INFO", "Logging level"),
}


def check_docker() -> PrereqResult:
    """Check if Docker daemon is running."""
    if not shutil.which("docker"):
        return PrereqResult("Docker", False, "docker not found in PATH", required=True)
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return PrereqResult("Docker", True, "daemon running")
        return PrereqResult("Docker", False, "daemon not responding", required=True)
    except Exception as e:
        return PrereqResult("Docker", False, str(e), required=True)


def check_docker_compose() -> PrereqResult:
    """Check Docker Compose v2 availability."""
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            version = result.stdout.strip().split()[-1] if result.stdout else "unknown"
            return PrereqResult("Docker Compose", True, f"v{version}")
        return PrereqResult("Docker Compose", False, "not available", required=True)
    except Exception:
        return PrereqResult("Docker Compose", False, "command failed", required=True)


def check_python() -> PrereqResult:
    """Check Python version ≥ 3.10."""
    major, minor = sys.version_info[:2]
    version_str = f"{major}.{minor}.{sys.version_info[2]}"
    if major >= 3 and minor >= 10:
        return PrereqResult("Python", True, version_str)
    return PrereqResult("Python", False, f"{version_str} (need ≥ 3.10)", required=True)


def check_port(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (ConnectionRefusedError, OSError, TimeoutError):
        return False


def check_infra_service(name: str, port: int) -> PrereqResult:
    """Check if an infrastructure service is reachable on its port."""
    if check_port(port):
        return PrereqResult(name, True, f"reachable on port {port}", required=False)
    return PrereqResult(
        name, False,
        f"not reachable on port {port} (will be started by docker compose)",
        required=False,
    )


def check_git_repo() -> PrereqResult:
    """Check if we're inside the vitruvyan-core git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            root = Path(result.stdout.strip())
            if (root / "vitruvyan_core").is_dir():
                return PrereqResult("Git repo", True, str(root))
            return PrereqResult("Git repo", False, "not vitruvyan-core repo", required=True)
        return PrereqResult("Git repo", False, "not a git repository", required=True)
    except Exception:
        return PrereqResult("Git repo", False, "git not available", required=True)


def _parse_compose_ports(repo_root: Optional[Path] = None) -> Dict[str, int]:
    """Parse host ports from docker-compose.yml, falling back to defaults."""
    root = repo_root or find_repo_root()
    if not root:
        return dict(DEFAULT_INFRA_PORTS)

    compose_path = root / "infrastructure" / "docker" / "docker-compose.yml"
    if not compose_path.exists():
        return dict(DEFAULT_INFRA_PORTS)

    try:
        import yaml
        with open(compose_path) as f:
            data = yaml.safe_load(f)
    except Exception:
        return dict(DEFAULT_INFRA_PORTS)

    services = data.get("services", {}) if data else {}
    ports: Dict[str, int] = dict(DEFAULT_INFRA_PORTS)

    for svc_name, mapping in _COMPOSE_SERVICE_MAP.items():
        svc = services.get(svc_name, {})
        svc_ports = svc.get("ports", [])
        for port_str in svc_ports:
            port_str = str(port_str)
            # Parse "9379:6379" → host=9379, container=6379
            m = re.match(r"(\d+):(\d+)", port_str)
            if not m:
                continue
            host_port, container_port = int(m.group(1)), int(m.group(2))
            if container_port == mapping["internal_port"]:
                ports[mapping["check_name"]] = host_port
            # Handle extra ports (e.g. qdrant gRPC)
            for extra_name, extra_internal in mapping.get("extra", {}).items():
                if container_port == extra_internal:
                    ports[extra_name] = host_port

    return ports


def run_all_checks() -> BootstrapReport:
    """Run all prerequisite checks and return a report."""
    report = BootstrapReport()
    report.checks.append(check_git_repo())
    report.checks.append(check_python())
    report.checks.append(check_docker())
    report.checks.append(check_docker_compose())
    infra_ports = _parse_compose_ports()
    for name, port in infra_ports.items():
        report.checks.append(check_infra_service(name, port))
    return report


def find_repo_root() -> Optional[Path]:
    """Find the vitruvyan-core repository root."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, timeout=5,
        )
        return Path(result.stdout.strip())
    except Exception:
        return None


def read_existing_env(env_path: Path) -> Dict[str, str]:
    """Read existing .env file into a dict."""
    values: Dict[str, str] = {}
    if not env_path.exists():
        return values
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def generate_env_file(
    env_path: Path,
    overrides: Optional[Dict[str, str]] = None,
) -> Path:
    """
    Generate or update .env file with required variables.

    Preserves existing values; only fills in missing keys.
    Returns path to the .env file.
    """
    existing = read_existing_env(env_path)
    overrides = overrides or {}

    lines = ["# Vitruvyan OS — Environment Configuration", "# Generated by 'vit setup'", ""]

    for key, (default, description) in ENV_TEMPLATE.items():
        # Priority: override > existing > default
        value = overrides.get(key, existing.get(key, default))
        lines.append(f"# {description}")
        lines.append(f"{key}={value}")
        lines.append("")

    # Preserve any extra keys from existing .env
    template_keys = set(ENV_TEMPLATE.keys())
    for key, value in existing.items():
        if key not in template_keys:
            lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n")
    return env_path


def collect_env_interactive() -> Dict[str, str]:
    """Interactively collect required environment variables from user."""
    values: Dict[str, str] = {}
    print("\n  Environment configuration:")
    print("  (press Enter to accept defaults shown in brackets)\n")

    for key, (default, description) in ENV_TEMPLATE.items():
        # Check if already set in environment
        env_val = os.environ.get(key)
        if env_val:
            values[key] = env_val
            continue

        display_default = default if default else "(empty)"
        is_secret = "KEY" in key or "PASSWORD" in key

        if is_secret and not default:
            prompt = f"  {key} ({description}): "
        else:
            prompt = f"  {key} [{display_default}]: "

        try:
            user_input = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Aborted.")
            return values

        values[key] = user_input if user_input else default

    return values
