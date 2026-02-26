---
scope: core
source_repo: mercator
source_vps: 161.xxx.xxx.xxx
kb_section: core
updated_at: 2026-02-26T00:00:00Z
---

# Docs Federation Operations

> Last Updated: February 26, 2026

## Objective

Allow docs authored on any VPS to converge into the official core KB (MkDocs hub) while keeping clear separation between:
- core docs (domain-agnostic),
- vertical docs (domain-specific).

## Topology

- Producer VPS example: `161.xxx.xxx.xxx` (`mercator` + local core copy)
- Hub VPS example: `144.xxx.xxx.xxx` (official `vitruvyan-core` + MkDocs)

## Producer Setup (`161...`)

Set environment variables and publish:

```bash
export DOCS_SOURCE_REPO=mercator
export DOCS_SOURCE_VPS=161.xxx.xxx.xxx
export DOCS_DEFAULT_VERTICAL=mercator
export DOCS_DEFAULT_SCOPE=vertical
export DOCS_HUB_SSH_TARGET=docs-sync@144.xxx.xxx.xxx
export DOCS_HUB_DROP_DIR=/opt/vitruvyan-core/incoming_docs
export DOCS_HUB_INGEST_CMD=/opt/vitruvyan-core/scripts/docs/ingest_incoming_bundle.sh

./scripts/docs/publish_docs.sh
```

Optional:
- `DOCS_CHANGED_ONLY=false` to publish full markdown corpus.
- `DOCS_INCLUDE_UNCOMMITTED=true` for local unstaged drafts.

## Hub Setup (`144...`)

In official `vitruvyan-core` repo:

```bash
chmod +x scripts/docs/ingest_incoming_bundle.sh
chmod +x scripts/docs/publish_docs.sh
```

Ingestion call (normally invoked by producer via SSH):

```bash
./scripts/docs/ingest_incoming_bundle.sh /opt/vitruvyan-core/incoming_docs/<bundle>.tar.gz
```

What it does:
1. Routes docs to `docs/knowledge_base/federated/...`
2. Refreshes federated index pages
3. Ensures MkDocs nav block exists
4. Builds MkDocs (if command available)
5. Runs optional KB ingestion command (`DOCS_KB_INGEST_CMD`)

## Recommended Automation

- Producer cron every 5 minutes or post-merge hook:
  - publish only when `docs/**/*.md` changed.
- Hub systemd path/timer:
  - ingest new bundles from `incoming_docs/`.

## Contract

Use metadata rules from:
- `docs/contracts/platform/DOCS_FEDERATION_CONTRACT_V1.md`
