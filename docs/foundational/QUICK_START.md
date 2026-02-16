---
tags:
  - getting-started
  - installation
  - public
---

# Quick Start

This is a minimal “get productive fast” path for Vitruvyan Core.

## 1) Run the stack (Docker)

From the repo root:

```bash
docker compose -f infrastructure/docker/docker-compose.yml up -d
```

Reference:
- `infrastructure/docker/README.md`

## 2) Open the Knowledge Base

- Public landing: `https://kb.vitruvyan.com/`
- Internal docs (protected): `https://kb.vitruvyan.com/docs/`

Access control reference:
- `infrastructure/docker/mkdocs/ACCESS_CONTROL.md`

## 3) Find the right docs

- Sacred Orders index: `docs/orders/README.md`
- Services index: `services/README_SERVICES.md`
- Cognitive Bus docs: `vitruvyan_core/core/synaptic_conclave/docs/README.md`
