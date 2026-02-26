# Docs Federation Operations

Last Updated: February 26, 2026

This runbook describes producer publish and hub ingest flows for federated docs.

## 1. Prerequisites

- Repository root available on producer and hub.
- Python 3.10+ on both sides.
- `scripts/docs/federate_docs.py` present.
- SSH/scp access from producer to hub (if using remote transfer).

Optional:

- `DOCS_KB_INGEST_CMD` on hub to trigger indexing after ingest.

## 2. Producer: Build Bundle

Core scope:

```bash
python3 scripts/docs/federate_docs.py bundle \
  --scope core \
  --producer vitruvyan-core \
  --source docs \
  --output /tmp/core_docs_bundle.tar.gz
```

Vertical scope:

```bash
python3 scripts/docs/federate_docs.py bundle \
  --scope vertical \
  --producer mercator \
  --vertical mercator \
  --source docs \
  --output /tmp/mercator_docs_bundle.tar.gz
```

Wrapper script:

```bash
scripts/docs/publish_docs.sh --scope vertical --producer mercator --vertical mercator --source docs
```

## 3. Hub: Validate + Ingest

Validate:

```bash
python3 scripts/docs/federate_docs.py validate --bundle /tmp/mercator_docs_bundle.tar.gz
```

Ingest:

```bash
python3 scripts/docs/federate_docs.py ingest --bundle /tmp/mercator_docs_bundle.tar.gz --repo-root .
```

Wrapper script:

```bash
scripts/docs/ingest_incoming_bundle.sh --bundle /tmp/mercator_docs_bundle.tar.gz
```

## 4. Destination Routing

- `scope=core` routes to `docs/knowledge_base/federated/core/<producer>/...`
- `scope=vertical` routes to `docs/knowledge_base/federated/verticals/<vertical>/...`

## 5. KB Reindex Hook

Configure on hub:

```bash
export DOCS_KB_INGEST_CMD='python scripts/kb/reindex.py --scope {scope} --vertical {vertical} --path {target_dir}'
```

The hook runs only after successful ingest and is skipped in dry-run mode.

## 6. Dry-Run Commands

Bundle dry-run:

```bash
python3 scripts/docs/federate_docs.py bundle \
  --scope vertical \
  --producer mercator \
  --vertical mercator \
  --source docs \
  --output /tmp/mercator_docs_bundle.tar.gz \
  --dry-run
```

Ingest dry-run:

```bash
python3 scripts/docs/federate_docs.py ingest --bundle /tmp/mercator_docs_bundle.tar.gz --repo-root . --dry-run
```

## 7. Onboarding a New Producer VPS

1. Ensure producer can generate a valid bundle (`validate` passes).
2. Add secure transfer channel to hub (scp/rsync or CI artifact).
3. Run first ingest in dry-run mode.
4. Enable `DOCS_KB_INGEST_CMD` for indexing.
5. Verify MkDocs navigation under Federated KB.
