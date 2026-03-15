"""
Bootstrap — prerequisite checker, Docker installer, port configurator, .env generator.

Designed for fresh VPS installations (Ubuntu with nothing pre-installed).

Flow:
  1. Check Python ≥ 3.10 and git repo
  2. Check/install Docker + Docker Compose
  3. Configure infrastructure ports (standard defaults, user can customize)
  4. Collect API keys / passwords
  5. Generate .env file
  6. Start infrastructure containers
"""

import getpass
import os
import secrets
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


# ── Port configuration ───────────────────────────────────────────

@dataclass
class PortConfig:
    """Infrastructure host port configuration."""
    redis: int = 6379
    postgres: int = 5432
    qdrant_rest: int = 6333
    qdrant_grpc: int = 6334

    def as_env_dict(self) -> Dict[str, str]:
        """Return env vars for docker-compose.yml host port mapping."""
        return {
            "HOST_REDIS_PORT": str(self.redis),
            "HOST_POSTGRES_PORT": str(self.postgres),
            "HOST_QDRANT_REST_PORT": str(self.qdrant_rest),
            "HOST_QDRANT_GRPC_PORT": str(self.qdrant_grpc),
        }

    def items(self) -> list:
        """Return (name, port) pairs for iteration."""
        return [
            ("redis", self.redis),
            ("postgres", self.postgres),
            ("qdrant_rest", self.qdrant_rest),
            ("qdrant_grpc", self.qdrant_grpc),
        ]


DEFAULT_PORTS = PortConfig()


# ── LLM Provider catalog ─────────────────────────────────────────

LLM_PROVIDERS: List[Dict] = [
    {
        "name": "openai",
        "label": "OpenAI",
        "key_url": "https://platform.openai.com/api-keys",
        "requires_key": True,
        "models": [
            ("gpt-4o-mini",     "GPT-4o mini — fast, economical"),
            ("gpt-4o",          "GPT-4o — most capable, multimodal"),
            ("chatgpt-5.1",     "ChatGPT 5.1 — latest generation (recommended)"),
            ("chatgpt-5.3",     "ChatGPT 5.3 — advanced reasoning"),
            ("chatgpt-5.4",     "ChatGPT 5.4 — most capable GPT-5"),
            ("codex",           "Codex — code-optimized model"),
            ("o3",              "o3 — frontier reasoning"),
            ("o3-mini",         "o3-mini — fast reasoning"),
            ("o1",              "o1 — advanced reasoning"),
            ("gpt-4-turbo",     "GPT-4 Turbo — high capability"),
            ("gpt-3.5-turbo",   "GPT-3.5 Turbo — cheapest option"),
        ],
    },
    {
        "name": "anthropic",
        "label": "Anthropic (Claude)",
        "key_url": "https://console.anthropic.com/",
        "requires_key": True,
        "models": [
            ("claude-sonnet-4-6",           "Claude Sonnet 4.6 — latest, best balance (recommended)"),
            ("claude-sonnet-4-5",           "Claude Sonnet 4.5 — fast, high quality"),
            ("claude-opus-4-6",             "Claude Opus 4.6 — most capable, expensive"),
            ("claude-3-5-sonnet-20241022",  "Claude 3.5 Sonnet — proven, stable"),
            ("claude-3-5-haiku-20241022",   "Claude 3.5 Haiku — fast, economical"),
            ("claude-3-opus-20240229",      "Claude 3 Opus — legacy flagship"),
        ],
    },
    {
        "name": "gemini",
        "label": "Google Gemini",
        "key_url": "https://aistudio.google.com/app/apikey",
        "requires_key": True,
        "models": [
            ("gemini-3.5-pro",     "Gemini 3.5 Pro — most capable, latest generation (recommended)"),
            ("gemini-3.5",         "Gemini 3.5 — latest generation, balanced"),
            ("gemini-2.0-flash",   "Gemini 2.0 Flash — fast, free tier available"),
            ("gemini-1.5-pro",     "Gemini 1.5 Pro — long context (2M tokens)"),
            ("gemini-1.5-flash",   "Gemini 1.5 Flash — fast, economical"),
        ],
    },
    {
        "name": "deepseek",
        "label": "DeepSeek",
        "key_url": "https://platform.deepseek.com/",
        "requires_key": True,
        "models": [
            ("deepseek-chat",      "DeepSeek V3 — very economical (recommended)"),
            ("deepseek-reasoner",  "DeepSeek R1 — advanced reasoning"),
        ],
    },
    {
        "name": "qwen",
        "label": "Qwen (Alibaba Cloud)",
        "key_url": "https://dashscope.console.aliyun.com/",
        "requires_key": True,
        "models": [
            ("qwen-max",    "Qwen Max — most capable (recommended)"),
            ("qwen-plus",   "Qwen Plus — balanced"),
            ("qwen-turbo",  "Qwen Turbo — fast, economical"),
            ("qwen-long",   "Qwen Long — extended context"),
        ],
    },
    {
        "name": "mistral",
        "label": "Mistral AI",
        "key_url": "https://console.mistral.ai/",
        "requires_key": True,
        "models": [
            ("mistral-large-latest",  "Mistral Large — most capable (recommended)"),
            ("mistral-small-latest",  "Mistral Small — balanced"),
            ("open-mistral-nemo",     "Mistral Nemo — open, multilingual"),
            ("open-mistral-7b",       "Mistral 7B — smallest, fastest"),
        ],
    },
    {
        "name": "custom",
        "label": "Custom / On-Premise (Ollama, LM Studio, vLLM, Gemma...)",
        "key_url": "",
        "requires_key": False,
        "models": [],  # user types model name
    },
]

# Keys managed exclusively by the LLM wizard step — skipped in generic collect_env_interactive()
LLM_MANAGED_KEYS = {
    "VITRUVYAN_LLM_PROVIDER",
    "VITRUVYAN_LLM_MODEL",
    "VITRUVYAN_LLM_API_KEY",
    "VITRUVYAN_LLM_BASE_URL",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
}

# (field_name, env_var, label, standard_port)
PORT_FIELDS = [
    ("redis",       "HOST_REDIS_PORT",       "Redis",       6379),
    ("postgres",    "HOST_POSTGRES_PORT",    "PostgreSQL",  5432),
    ("qdrant_rest", "HOST_QDRANT_REST_PORT", "Qdrant REST", 6333),
    ("qdrant_grpc", "HOST_QDRANT_GRPC_PORT", "Qdrant gRPC", 6334),
]


# ── Env template ─────────────────────────────────────────────────

# key: (default_value, description)
# Required vars are prompted interactively; optional vars get sensible defaults silently.
ENV_TEMPLATE: Dict[str, Tuple[str, str]] = {
    # ── LLM provider (written by the LLM wizard step, not prompted generically) ──
    "VITRUVYAN_LLM_PROVIDER": ("", "LLM provider (openai/anthropic/gemini/deepseek/qwen/mistral/custom)"),
    "VITRUVYAN_LLM_MODEL": ("", "LLM model identifier"),
    "VITRUVYAN_LLM_API_KEY": ("", "LLM provider API key"),
    "VITRUVYAN_LLM_BASE_URL": ("", "LLM base URL (on-premise only)"),
    # backward-compat alias — set automatically when provider=openai
    "OPENAI_API_KEY": ("", "OpenAI API key (backward-compat alias, set by LLM step)"),
    "OPENAI_MODEL": ("", "OpenAI model (backward-compat alias, set by LLM step)"),
    # ── Required ─────────────────────────────────────────────────
    "POSTGRES_USER": ("vitruvyan_core_user", "PostgreSQL username"),
    "POSTGRES_PASSWORD": ("", "PostgreSQL password"),
    "POSTGRES_DB": ("vitruvyan_core", "PostgreSQL database name"),
    # ── Internal service addresses (Docker network) ───────────────
    "POSTGRES_HOST": ("core_postgres", "PostgreSQL host (Docker service name)"),
    "POSTGRES_PORT": ("5432", "PostgreSQL internal port"),
    "REDIS_HOST": ("core_redis", "Redis host (Docker service name)"),
    "REDIS_PORT": ("6379", "Redis internal port"),
    "REDIS_URL": ("redis://core_redis:6379", "Redis URL"),
    "QDRANT_HOST": ("core_qdrant", "Qdrant host (Docker service name)"),
    "QDRANT_PORT": ("6333", "Qdrant internal port"),
    "QDRANT_URL": ("http://core_qdrant:6333", "Qdrant URL"),
    # ── Optional / feature flags ──────────────────────────────────
    "LOG_LEVEL": ("INFO", "Logging level"),
    "GRAFANA_ADMIN_USER": ("admin", "Grafana admin username"),
    "GRAFANA_ADMIN_PASSWORD": ("vitruvyan", "Grafana admin password"),
    "HUGGINGFACE_HUB_TOKEN": ("", "HuggingFace token (optional, for private models)"),
    "SLACK_WEBHOOK_URL": ("", "Slack webhook URL (optional, for notifications)"),
    # ── MCP service defaults ──────────────────────────────────────
    "MCP_LOG_LEVEL": ("INFO", "MCP service log level"),
    "MCP_OPENAI_MODEL": ("gpt-4o-mini", "MCP OpenAI model"),
    "MCP_Z_THRESHOLD": ("2.0", "MCP Z-score threshold"),
    "MCP_COMPOSITE_THRESHOLD": ("0.6", "MCP composite threshold"),
    "MCP_MIN_SUMMARY_WORDS": ("50", "MCP min summary words"),
    "MCP_MAX_SUMMARY_WORDS": ("200", "MCP max summary words"),
    "MCP_FACTOR_KEYS": ("", "MCP factor keys (optional)"),
    # ── VSGS defaults ─────────────────────────────────────────────
    "VSGS_ENABLED": ("true", "Enable VSGS semantic grounding"),
    "VSGS_STORE_EVERY_N": ("1", "VSGS store frequency"),
    "VSGS_PROMPT_BUDGET_CHARS": ("4000", "VSGS prompt budget chars"),
    "VSGS_GROUNDING_TOPK": ("5", "VSGS grounding top-k results"),
    # ── Edge / experimental ───────────────────────────────────────
    "OCULUS_PRIME_EVENT_MIGRATION_MODE": ("false", "Edge Oculus Prime migration mode"),
}


# ── Prerequisite checks ─────────────────────────────────────────

def check_docker() -> PrereqResult:
    """Check if Docker daemon is running."""
    if not shutil.which("docker"):
        return PrereqResult("Docker", False, "not installed", required=True)
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
        return PrereqResult("Docker Compose", False, "not available", required=True)


def check_python() -> PrereqResult:
    """Check Python version ≥ 3.10."""
    major, minor = sys.version_info[:2]
    version_str = f"{major}.{minor}.{sys.version_info[2]}"
    if major >= 3 and minor >= 10:
        return PrereqResult("Python", True, version_str)
    return PrereqResult("Python", False, f"{version_str} (need ≥ 3.10)", required=True)


def check_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is FREE (not in use). Returns True if available."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return False  # Something is listening → port is taken
    except (ConnectionRefusedError, OSError, TimeoutError):
        return True  # Nothing listening → port is free


def check_port_reachable(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is accepting connections (service is running)."""
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (ConnectionRefusedError, OSError, TimeoutError):
        return False


def check_infra_service(name: str, port: int) -> PrereqResult:
    """Check if an infrastructure service is reachable on its host port."""
    if check_port_reachable(port):
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


def run_all_checks(port_config: Optional[PortConfig] = None) -> BootstrapReport:
    """Run all prerequisite checks and return a report."""
    report = BootstrapReport()
    report.checks.append(check_git_repo())
    report.checks.append(check_python())
    report.checks.append(check_docker())
    report.checks.append(check_docker_compose())
    ports = port_config or _read_configured_ports()
    for name, port in ports.items():
        report.checks.append(check_infra_service(name, port))
    return report


# ── Docker installation ─────────────────────────────────────────

def can_install_docker() -> bool:
    """Check if we can install Docker (Ubuntu/Debian with apt)."""
    return shutil.which("apt-get") is not None


def install_docker() -> bool:
    """
    Install Docker Engine + Compose on Ubuntu/Debian.

    Uses the official Docker convenience script.
    Returns True if installation succeeded.
    """
    print("  Installing Docker Engine...")
    try:
        result = subprocess.run(
            ["bash", "-c", "curl -fsSL https://get.docker.com | sh"],
            timeout=300,
        )
        if result.returncode != 0:
            return False

        # Add current user to docker group
        user = os.environ.get("USER", "")
        if user and user != "root":
            subprocess.run(
                ["sudo", "usermod", "-aG", "docker", user],
                timeout=10,
            )
            print(f"  Added '{user}' to docker group.")
            print("  Note: you may need to log out and back in for group changes to take effect.")

        # Start Docker service
        subprocess.run(["sudo", "systemctl", "start", "docker"], timeout=30)
        subprocess.run(["sudo", "systemctl", "enable", "docker"], timeout=10)

        return True
    except Exception as e:
        print(f"  Docker installation failed: {e}")
        return False


# ── Port configuration ───────────────────────────────────────────

def _read_configured_ports() -> PortConfig:
    """Read port configuration from .env file or use defaults."""
    root = find_repo_root()
    if not root:
        return PortConfig()

    env_path = root / "infrastructure" / "docker" / ".env"
    existing = read_existing_env(env_path)

    return PortConfig(
        redis=int(existing.get("HOST_REDIS_PORT", "6379")),
        postgres=int(existing.get("HOST_POSTGRES_PORT", "5432")),
        qdrant_rest=int(existing.get("HOST_QDRANT_REST_PORT", "6333")),
        qdrant_grpc=int(existing.get("HOST_QDRANT_GRPC_PORT", "6334")),
    )


def collect_ports_interactive() -> PortConfig:
    """Ask user to configure infrastructure ports."""
    print("\n  Port configuration:")
    print("  Standard ports will be used unless you specify alternatives.")
    print("  (press Enter to accept defaults shown in brackets)\n")

    # First ask if they want standard or custom
    try:
        choice = input("  Use standard ports? [Y/n]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  Using standard ports.")
        return PortConfig()

    if choice in ("", "y", "yes"):
        # Verify standard ports are available
        conflicts = []
        for field_name, _, label, std_port in PORT_FIELDS:
            if not check_port_available(std_port):
                conflicts.append((label, std_port))
        if conflicts:
            print("\n  ⚠️  Port conflicts detected:")
            for label, port in conflicts:
                print(f"    - {label} port {port} is already in use")
            print("  Switching to custom port configuration.\n")
        else:
            print("  ✅ All standard ports available.\n")
            return PortConfig()

    # Custom port selection
    config = PortConfig()
    for field_name, _env_var, label, std_port in PORT_FIELDS:
        while True:
            try:
                raw = input(f"  {label} port [{std_port}]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\n  Using default {std_port}.")
                break

            if not raw:
                port = std_port
            else:
                try:
                    port = int(raw)
                    if not (1024 <= port <= 65535):
                        print(f"    Port must be between 1024 and 65535.")
                        continue
                except ValueError:
                    print(f"    Invalid port number.")
                    continue

            if not check_port_available(port):
                print(f"    ⚠️  Port {port} is already in use. Choose another.")
                continue

            setattr(config, field_name, port)
            break

    return config


# ── Repository root ──────────────────────────────────────────────

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


# ── .env file management ─────────────────────────────────────────

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
    port_config: Optional[PortConfig] = None,
) -> Path:
    """
    Generate or update .env file with required variables and port config.

    Preserves existing values; only fills in missing keys.
    Returns path to the .env file.
    """
    existing = read_existing_env(env_path)
    overrides = overrides or {}

    lines = ["# Vitruvyan OS — Environment Configuration", "# Generated by 'vit setup'", ""]

    # Port configuration section
    if port_config:
        lines.append("# === Host Port Mapping (docker-compose) ===")
        for field_name, env_var, label, _std_port in PORT_FIELDS:
            port_val = getattr(port_config, field_name)
            lines.append(f"{env_var}={port_val}")
        lines.append("")

    # Standard env vars
    for key, (default, description) in ENV_TEMPLATE.items():
        value = overrides.get(key, existing.get(key, default))
        lines.append(f"# {description}")
        lines.append(f"{key}={value}")
        lines.append("")

    # Preserve any extra keys from existing .env not in template or port vars
    template_keys = set(ENV_TEMPLATE.keys())
    port_keys = {pf[1] for pf in PORT_FIELDS}
    for key, value in existing.items():
        if key not in template_keys and key not in port_keys:
            lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n")
    return env_path


def collect_credentials_interactive(existing_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Ask user for DB credentials (Postgres password). Hidden input, auto-generate option.

    Returns a dict with at minimum ``POSTGRES_PASSWORD`` set to a non-empty value.
    Safe to call on re-runs: if password is already in existing_env it is kept.
    """
    existing_env = existing_env or {}
    values: Dict[str, str] = {}

    # ----- PostgreSQL password -----
    existing_pg_pwd = existing_env.get("POSTGRES_PASSWORD", "").strip()
    if existing_pg_pwd:
        print("  PostgreSQL password: already set (keeping existing)")
        values["POSTGRES_PASSWORD"] = existing_pg_pwd
    else:
        print("  PostgreSQL password")
        print("  (press Enter to auto-generate a secure random password)")
        while True:
            try:
                pwd = getpass.getpass("  Password: ").strip()
            except (EOFError, KeyboardInterrupt):
                pwd = ""
            if not pwd:
                pwd = secrets.token_hex(16)
                print(f"  Generated password: {pwd}")
                print("  ⚠️  Save this password — you will need it to access the database directly.")
                break
            try:
                confirm = getpass.getpass("  Confirm password: ").strip()
            except (EOFError, KeyboardInterrupt):
                confirm = ""
            if pwd == confirm:
                break
            print("  ❌ Passwords do not match — try again.\n")
        values["POSTGRES_PASSWORD"] = pwd

    return values


def _test_llm_connection(provider_name: str, model_id: str, api_key: str, base_url: str = "") -> tuple:
    """
    Send a minimal test request to verify the LLM API key and endpoint are reachable.
    Returns (success: bool, message: str).
    """
    import urllib.request
    import urllib.error
    import json as _json

    _COMPAT_URLS = {
        "openai":   "https://api.openai.com/v1/chat/completions",
        "gemini":   "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "deepseek": "https://api.deepseek.com/v1/chat/completions",
        "qwen":     "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "mistral":  "https://api.mistral.ai/v1/chat/completions",
    }

    try:
        if provider_name == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            payload = {
                "model": model_id,
                "max_tokens": 5,
                "messages": [{"role": "user", "content": "Reply OK"}],
            }
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            }
        else:
            if base_url:
                url = base_url.rstrip("/") + "/chat/completions"
            else:
                url = _COMPAT_URLS.get(provider_name, _COMPAT_URLS["openai"])
            payload = {
                "model": model_id,
                "max_tokens": 5,
                "messages": [{"role": "user", "content": "Reply OK"}],
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }

        req = urllib.request.Request(
            url,
            data=_json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=12):
            return True, "API key and endpoint verified"

    except urllib.error.HTTPError as e:
        if e.code in (400, 422):   # bad request but auth passed
            return True, f"Endpoint reachable, auth OK (HTTP {e.code})"
        if e.code == 401:
            return False, "Invalid API key (401 Unauthorized)"
        if e.code == 403:
            return False, "Access denied (403 Forbidden)"
        return False, f"HTTP {e.code}: {e.reason}"
    except Exception as exc:
        return False, f"Connection failed: {exc}"


def collect_llm_interactive(existing_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Interactively collect LLM provider, model, and API key.

    Flow: choose provider → choose model → enter API key (or base URL for on-premise).

    Returns a dict of env vars to write.  LLM_MANAGED_KEYS are all set here;
    the generic collect_env_interactive() skips them.
    """
    existing_env = existing_env or {}

    # If already configured, offer to keep
    existing_provider = existing_env.get("VITRUVYAN_LLM_PROVIDER", "").strip()
    existing_model = existing_env.get("VITRUVYAN_LLM_MODEL", "").strip()
    existing_key = (
        existing_env.get("VITRUVYAN_LLM_API_KEY", "").strip()
        or existing_env.get("OPENAI_API_KEY", "").strip()
    )

    if existing_provider and (existing_key or existing_provider == "custom"):
        model_label = f" / {existing_model}" if existing_model else ""
        print(f"  LLM already configured: {existing_provider}{model_label}")
        try:
            keep = input("  Keep existing configuration? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            keep = "y"
        if keep in ("", "y", "yes"):
            return {}

    # ── Step A: choose provider ──────────────────────────────────
    print("\n  Available LLM providers:\n")
    for i, p in enumerate(LLM_PROVIDERS, 1):
        print(f"    {i}) {p['label']}")

    while True:
        try:
            raw = input(f"\n  Select provider [1-{len(LLM_PROVIDERS)}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Aborted.")
            return {}

        try:
            provider = LLM_PROVIDERS[int(raw) - 1]
            break
        except (ValueError, IndexError):
            print(f"  Invalid selection — enter a number between 1 and {len(LLM_PROVIDERS)}.")

    values: Dict[str, str] = {"VITRUVYAN_LLM_PROVIDER": provider["name"]}

    # ── Step B: choose model ─────────────────────────────────────
    if provider["models"]:
        print(f"\n  Available models for {provider['label']}:\n")
        for i, (model_id, label) in enumerate(provider["models"], 1):
            rec = " ← recommended" if i == 1 else ""
            print(f"    {i}) {model_id}  —  {label}{rec}")

        while True:
            try:
                raw = input(f"\n  Select model [1-{len(provider['models'])}]: ").strip()
            except (EOFError, KeyboardInterrupt):
                raw = "1"

            if not raw:
                model_id = provider["models"][0][0]
                break
            try:
                model_id = provider["models"][int(raw) - 1][0]
                break
            except (ValueError, IndexError):
                print(f"  Invalid selection.")
    else:
        # Custom / on-premise: user types the model name
        common_examples = "llama3.2, mistral, gemma2:9b, phi3, deepseek-r1:7b"
        print(f"\n  On-premise model name (examples: {common_examples}):")
        try:
            model_id = input("  Model name [llama3.2]: ").strip() or "llama3.2"
        except (EOFError, KeyboardInterrupt):
            model_id = "llama3.2"

    values["VITRUVYAN_LLM_MODEL"] = model_id

    # ── Step C: API key or base URL ──────────────────────────────
    if provider["requires_key"]:
        if provider["key_url"]:
            print(f"\n  Get your API key at: {provider['key_url']}")
        print(f"  {provider['label']} API key (input is hidden):")
        try:
            key = getpass.getpass("  API key: ").strip()
        except (EOFError, KeyboardInterrupt):
            key = ""

        if not key:
            print("  ⚠️  No key provided — set VITRUVYAN_LLM_API_KEY in .env before starting.")
        values["VITRUVYAN_LLM_API_KEY"] = key
        values["VITRUVYAN_LLM_BASE_URL"] = ""

        # Backward-compat aliases: OPENAI_API_KEY / OPENAI_MODEL always mirror the active
        # LLM config so any service or script that reads those vars continues to work.
        values["OPENAI_API_KEY"] = key
        values["OPENAI_MODEL"] = model_id

        # Live connection test
        if key:
            print(f"\n  Testing connection to {provider['label']}...")
            ok, msg = _test_llm_connection(provider["name"], model_id, key)
            if ok:
                print(f"  ✅ {msg}")
            else:
                print(f"  ⚠️  {msg}")
                print(f"     Proceeding anyway — verify the key in .env before starting.")
    else:
        # On-premise: ask for base URL only
        default_url = "http://localhost:11434/v1"
        print(f"\n  API base URL (leave blank for Ollama default: {default_url}):")
        try:
            base_url = input(f"  Base URL [{default_url}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            base_url = ""
        resolved_url = base_url or default_url
        values["VITRUVYAN_LLM_BASE_URL"] = resolved_url
        values["VITRUVYAN_LLM_API_KEY"] = ""
        # Backward-compat aliases for on-premise
        values["OPENAI_API_KEY"] = "local"
        values["OPENAI_MODEL"] = model_id

        # Live connection test (no auth required for local)
        print(f"\n  Testing connection to {resolved_url}...")
        ok, msg = _test_llm_connection("custom", model_id, "local", base_url=resolved_url)
        if ok:
            print(f"  ✅ {msg}")
        else:
            print(f"  ⚠️  {msg}")
            print(f"     Make sure the on-premise server is running before starting.")

    print(f"\n  ✅ LLM configured: {provider['label']} / {model_id}")
    return values


def collect_env_interactive() -> Dict[str, str]:
    """Interactively collect required environment variables from user."""
    values: Dict[str, str] = {}
    print("\n  Environment configuration:")
    print("  (press Enter to accept defaults shown in brackets)\n")

    for key, (default, description) in ENV_TEMPLATE.items():
        # LLM keys are handled by collect_llm_interactive() — skip here
        if key in LLM_MANAGED_KEYS:
            continue

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


# ── Infrastructure startup ───────────────────────────────────────

# Network and volume names declared as `external: true` in docker-compose.yml.
# On a fresh install they don't exist yet — we create them before compose up.
_DOCKER_NETWORK = "vitruvyan_core_net"
_DOCKER_VOLUMES = [
    "docker_redis_data_core",
    "docker_postgres_data_core",
    "docker_qdrant_data_core",
    "docker_babel_gardens_models",
    "docker_babel_gardens_logs",
    "docker_vault_keeper_data",
    "docker_prometheus_data",
    "docker_grafana_data",
]

# Core services that must always be running for Vitruvyan to function.
_INFRA_SERVICES = ["redis", "postgres", "qdrant"]
_CORE_SERVICES = [
    "graph", "embedding",
    "babel_gardens", "babel_listener",
    "memory_orders", "memory_orders_listener",
    "codex_hunters", "codex_listener",
    "pattern_weavers",
    "vault_keepers", "vault_listener",
    "orthodoxy_wardens", "orthodoxy_listener",
    "conclave", "conclave_listener",
    "mcp",
]


def ensure_docker_prerequisites() -> None:
    """
    Create Docker network and volumes declared as external in docker-compose.yml.

    Safe to call multiple times — `docker network/volume create` is idempotent
    (exits 0 if resource already exists on most Docker versions, or exits 1 with
    a 'already exists' message which we ignore).

    Works on: VPS bare metal, VM, WSL2 + Docker Desktop, macOS Docker Desktop.
    """
    # Create network
    try:
        result = subprocess.run(
            ["docker", "network", "create", _DOCKER_NETWORK],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            print(f"  Created Docker network: {_DOCKER_NETWORK}")
        # returncode != 0 means it already exists — that's fine
    except Exception as e:
        print(f"  ⚠️  Could not create network {_DOCKER_NETWORK}: {e}")

    # Create volumes
    for vol in _DOCKER_VOLUMES:
        try:
            subprocess.run(
                ["docker", "volume", "create", vol],
                capture_output=True, text=True, timeout=15,
            )
        except Exception:
            pass  # Already exists or Docker unavailable — compose will catch it


def start_infrastructure(repo_root: Path) -> bool:
    """Ensure Docker prerequisites, then start infrastructure and core services."""
    compose_file = repo_root / "infrastructure" / "docker" / "docker-compose.yml"
    if not compose_file.exists():
        print(f"  Compose file not found: {compose_file}")
        return False

    # Create network + volumes before compose (they are declared external)
    ensure_docker_prerequisites()

    def _run(services: list, timeout: int | None = None) -> bool:
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "-d"] + services,
                cwd=str(compose_file.parent),
                timeout=timeout,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"  docker compose timed out after {timeout}s.")
            return False
        except Exception as e:
            print(f"  Failed to start services: {e}")
            return False

    # Phase 1: infra (fast — pre-built images)
    print("  Starting infrastructure (redis, postgres, qdrant)...")
    if not _run(_INFRA_SERVICES, timeout=120):
        return False

    # Phase 2: core services — no timeout: first-run builds download torch/CUDA
    # packages (~1 GB per service) and may take 20-60+ min depending on bandwidth.
    print("  Starting core services (this may take several minutes on first run)...")
    if not _run(_CORE_SERVICES):
        print("  ⚠️  Some core services failed to start. Run: cd infrastructure/docker && docker compose up -d")
        return True

    return True
