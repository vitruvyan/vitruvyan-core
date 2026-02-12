# config/ — Configuration Files

> **Last Updated**: February 12, 2026  
> **Purpose**: Shared configuration files, API configs, settings  
> **Type**: Python config modules, YAML, JSON

---

## 🎯 Cosa Contiene

`config/` contiene **file di configurazione condivisi** usati da più componenti di Vitruvyan.

**Caratteristiche**:
- ✅ **Centralized Settings**: Configurazioni condivise (non duplicate)
- ✅ **Environment-Aware**: Dev vs. prod configs
- ✅ **Importable**: Usabile da `vitruvyan_core` e `services`
- ✅ **No Secrets**: Credenziali in `infrastructure/secrets/` (encrypted)

---

## 📂 Struttura

```
config/
├── api_config.py               # API-level configuration
├── settings.yaml               # Global settings (example)
└── ...
```

**File principali**:
- **api_config.py**: Configurazioni condivise per API (timeouts, retry logic, default ports)
- **settings.yaml**: Settings globali (se presenti)

---

## 🔧 api_config.py

### Purpose

Configurazioni API-level condivise tra servizi (evita duplicazione).

### Example Content

```python
# config/api_config.py
"""Shared API configuration for Vitruvyan services."""

import os
from typing import Optional

# Default ports
DEFAULT_PORTS = {
    "graph": 9004,
    "neural": 9003,
    "mcp": 8020,
    "memory_orders": 9008,
    "vault_keepers": 9007,
    "orthodoxy_wardens": 9006,
    "codex_hunters": 9005,
    "babel_gardens": 9009,
    "pattern_weavers": 9011,
}

# API timeouts (seconds)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
API_RETRY_COUNT = int(os.getenv("API_RETRY_COUNT", "3"))
API_RETRY_DELAY = float(os.getenv("API_RETRY_DELAY", "1.0"))

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Health check interval
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Usage in Services

```python
# services/api_memory_orders/config.py
from config.api_config import DEFAULT_PORTS, API_TIMEOUT, LOG_LEVEL

SERVICE_NAME = "api_memory_orders"
SERVICE_PORT = DEFAULT_PORTS["memory_orders"]
HTTP_TIMEOUT = API_TIMEOUT
```

---

## ⚙️ Environment Variables

### Where Secrets Live

**❌ NOT HERE**: Secrets non vanno mai in `config/`

**✅ In `infrastructure/secrets/`**: Encrypted con Ansible Vault
**✅ In `.env`**: Locale (gitignored)
**✅ In environment**: Docker Compose, K8s secrets

### Config vs. Secrets

| Type | Where | Example |
|------|-------|---------|
| **Config** (non-sensitive) | `config/` | Default ports, timeouts, retry logic |
| **Secrets** (sensitive) | `infrastructure/secrets/` | Passwords, API keys, tokens |
| **Environment** (runtime) | `.env`, Docker env | Host, port, log level overrides |

---

## 🎯 Usage Patterns

### Import from Services

```python
# From service config.py
from config.api_config import (
    DEFAULT_PORTS,
    API_TIMEOUT,
    LOG_LEVEL,
    CORS_ORIGINS
)

# Use in service
SERVICE_PORT = DEFAULT_PORTS["vault_keepers"]
```

### Import from Core

```python
# From vitruvyan_core module
from config.api_config import API_TIMEOUT

# Use in HTTP client
import httpx
client = httpx.Client(timeout=API_TIMEOUT)
```

---

## 📚 Documentazione

### Global Configs

Vedere:
- [Services README](../services/README_SERVICES.md) — Service-specific config.py patterns
- [Infrastructure README](../infrastructure/README_INFRASTRUCTURE.md) — .env templates, secrets management

### Module Configs

Ogni service ha il proprio `config.py` che importa da qui:
```
services/api_<service>/
└── config.py  → Imports from config/api_config.py
```

---

## 🎯 Design Principles

1. **DRY**: Configurazioni condivise qui, non duplicate in ogni service
2. **No Secrets**: Mai credenziali in plain text (usa infrastructure/secrets/)
3. **Environment-Aware**: Overridable via environment variables
4. **Typed**: Type hints per tutte le configurazioni
5. **Documented**: Ogni setting ha docstring

---

## 📖 Link Utili

- **[Services](../services/README_SERVICES.md)** — Come i servizi usano config
- **[Infrastructure](../infrastructure/README_INFRASTRUCTURE.md)** — .env templates, secrets management
- **[README Principale](../README.md)** — Repository overview

---

**Purpose**: Centralize shared configurations (non-sensitive).  
**Pattern**: Import from services/core, override via environment.  
**Status**: Minimal (api_config.py), expands as needed.
