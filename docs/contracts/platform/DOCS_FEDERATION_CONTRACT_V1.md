# DOCS_FEDERATION_CONTRACT_V1

Status: Active  
Version: V1  
Last Updated: February 26, 2026

## 1. Purpose

This contract defines how documentation bundles are produced by remote Core or Vertical deployments and ingested by the hub Knowledge Base.

The objective is deterministic routing, validation, and indexing without coupling Core to any domain-specific implementation.

## 2. Scope

This contract applies to:

- Producer-side bundle generation.
- Hub-side bundle validation and ingest.
- Routing under `docs/knowledge_base/federated/`.
- Optional post-ingest KB indexing hook.

This contract does not define:

- Domain logic for any vertical.
- Search/index implementation details.

## 3. Bundle Format

Each bundle MUST be a `.tar.gz` archive with:

- `manifest.json`
- `docs_payload/` (directory tree with markdown/assets)

`manifest.json` MUST include:

- `contract_version`: MUST be exactly `DOCS_FEDERATION_CONTRACT_V1`
- `bundle_schema_version`: integer, currently `1`
- `bundle_id`: unique string
- `generated_at_utc`: ISO-8601 UTC timestamp
- `producer`: producer id (slug-safe)
- `scope`: `core` or `vertical`
- `vertical`: required when `scope=vertical`, omitted/empty otherwise
- `payload_dir`: MUST be `docs_payload`
- `files`: list of objects `{path, sha256, size}`

Path safety invariants:

- No absolute paths in payload.
- No `..` segments.
- No files outside `docs_payload/`.

## 4. Hub Routing Rules

When ingesting on hub:

- `scope=core` -> `docs/knowledge_base/federated/core/<producer>/...`
- `scope=vertical` -> `docs/knowledge_base/federated/verticals/<vertical>/...`

Hub MUST preserve this separation.

## 5. Validation Rules

Validation MUST fail when:

- Contract version is unknown.
- Required manifest fields are missing.
- `scope=vertical` but `vertical` is missing.
- Payload files are missing from archive.
- SHA-256 mismatch against manifest.
- Payload contains unsafe paths.

## 6. Ingest Semantics

Ingest behavior:

- Copy payload files into routed destination path.
- Overwrite same-path files (idempotent updates).
- Do not delete unrelated files.
- Persist `_federation_manifest.json` in destination.

## 7. KB Index Hook

If `DOCS_KB_INGEST_CMD` is set, hub ingest MUST execute it after successful ingest (unless dry-run).

The command string may reference:

- `{scope}`
- `{vertical}`
- `{producer}`
- `{target_dir}`
- `{bundle}`

Example:

```bash
export DOCS_KB_INGEST_CMD='python scripts/kb/reindex.py --scope {scope} --vertical {vertical} --path {target_dir}'
```

## 8. Producer Requirements

Producers MUST:

- Generate bundles using this contract.
- Set `scope` correctly (`core` or `vertical`).
- Set `vertical` when `scope=vertical`.
- Keep documentation content domain-owned (no hub rewrites).

## 9. Compatibility

Backward compatibility policy:

- New required fields require `bundle_schema_version` bump.
- Hub MAY ignore unknown manifest fields.
- Contract id (`DOCS_FEDERATION_CONTRACT_V1`) is the primary compatibility gate.
