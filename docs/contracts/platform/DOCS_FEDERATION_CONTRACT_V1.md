---
scope: core
source_repo: mercator
source_vps: 161.xxx.xxx.xxx
kb_section: core
updated_at: 2026-02-26T00:00:00Z
---

# Docs Federation Contract V1

> Last Updated: February 26, 2026  
> Scope: Cross-VPS documentation federation (producer nodes -> core hub)  
> Status: Active

## Purpose

Define a single contract for documentation produced on any VPS so it can be:
- routed to the correct KB section (core or vertical),
- indexed consistently,
- published by MkDocs on the core hub node.

## Federation Model

- **Producer nodes**: any vertical/core VPS where docs are authored.
- **Hub node**: official `vitruvyan-core` installation (MkDocs + KB ingestion).
- **Flow**: producer creates bundle -> hub ingests bundle -> MkDocs rebuild -> KB indexing refresh.

## Required Front Matter

Each Markdown document SHOULD include front matter:

```yaml
---
scope: core | vertical
vertical: mercator            # required when scope=vertical
source_repo: mercator
source_vps: 161.xxx.xxx.xxx
source_commit: 18cd1ca
updated_at: 2026-02-26T10:30:00Z
kb_section: core | verticals/<name>
---
```

Notes:
- `scope=core` means the document belongs to shared domain-agnostic core knowledge.
- `scope=vertical` means domain-specific knowledge; `vertical` is mandatory.
- Missing fields can be backfilled by bundling scripts, but explicit metadata is preferred.

## Routing Rules

- `scope=core` -> `docs/knowledge_base/federated/core/<source_repo>/<original_path>.md`
- `scope=vertical` -> `docs/knowledge_base/federated/verticals/<vertical>/<source_repo>/<original_path>.md`

## Hub Index Pages

The ingestion step maintains:
- `docs/knowledge_base/federated/README.md`
- `docs/knowledge_base/federated/core/README.md`
- `docs/knowledge_base/federated/verticals/README.md`
- `docs/knowledge_base/federated/verticals/<vertical>/README.md`

These pages are the stable MkDocs navigation targets.

## MkDocs Contract

`infrastructure/docker/mkdocs/mkdocs.yml` must contain a federated nav block:

```yaml
# FEDERATED_DOCS_NAV_START
- Federated Docs:
  - Overview: docs/knowledge_base/federated/README.md
  - Core Contributions: docs/knowledge_base/federated/core/README.md
  - Vertical Contributions: docs/knowledge_base/federated/verticals/README.md
# FEDERATED_DOCS_NAV_END
```

The ingest script owns this block and updates it idempotently.

## Operational Scripts

- Producer:
  - `scripts/docs/publish_docs.sh`
  - `scripts/docs/federate_docs.py bundle`
- Hub:
  - `scripts/docs/ingest_incoming_bundle.sh`
  - `scripts/docs/federate_docs.py ingest`

## Non-Goals

- No bidirectional merge between hubs.
- No direct edits on generated federated paths.
- No hidden routing logic outside this contract.
