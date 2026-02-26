#!/usr/bin/env python3
"""Federated documentation bundle tooling.

Commands:
  - bundle: create producer-side archive
  - validate: verify bundle integrity + contract compliance
  - ingest: copy bundle payload into hub routing paths
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

CONTRACT_VERSION = "DOCS_FEDERATION_CONTRACT_V1"
PAYLOAD_DIR = "docs_payload"
BUNDLE_SCHEMA_VERSION = 1
DEFAULT_CORE_ROOT = Path("docs/knowledge_base/federated/core")
DEFAULT_VERTICAL_ROOT = Path("docs/knowledge_base/federated/verticals")
ALLOWED_SUFFIXES = {
    ".md",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".gif",
    ".webp",
    ".css",
    ".js",
    ".json",
    ".yaml",
    ".yml",
    ".txt",
}


def _utc_now_iso() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _slugify(raw: str) -> str:
    value = raw.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if not value:
        raise ValueError(f"Invalid identifier: {raw!r}")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_rel_path(path: Path) -> bool:
    if path.is_absolute():
        return False
    parts = path.parts
    return all(part not in ("", ".", "..") for part in parts)


def _collect_payload_files(source_dir: Path) -> list[Path]:
    files: list[Path] = []
    for item in source_dir.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(source_dir)
        if not _safe_rel_path(rel):
            continue
        if item.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        files.append(rel)
    files.sort(key=lambda p: p.as_posix())
    return files


def _render_hook(template: str, context: dict[str, str]) -> str:
    class _SafeDict(dict):
        def __missing__(self, key: str) -> str:
            return "{" + key + "}"

    return template.format_map(_SafeDict(context))


def _validate_manifest(manifest: dict) -> None:
    required_fields = {
        "contract_version",
        "bundle_schema_version",
        "bundle_id",
        "generated_at_utc",
        "producer",
        "scope",
        "payload_dir",
        "files",
    }
    missing = sorted(required_fields - set(manifest))
    if missing:
        raise ValueError(f"Manifest missing fields: {', '.join(missing)}")

    if manifest["contract_version"] != CONTRACT_VERSION:
        raise ValueError(
            f"Unsupported contract_version={manifest['contract_version']!r}, expected {CONTRACT_VERSION}"
        )
    if manifest["bundle_schema_version"] != BUNDLE_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported bundle_schema_version={manifest['bundle_schema_version']!r}, "
            f"expected {BUNDLE_SCHEMA_VERSION}"
        )
    if manifest["scope"] not in {"core", "vertical"}:
        raise ValueError("Manifest scope must be 'core' or 'vertical'")
    if manifest["scope"] == "vertical" and not manifest.get("vertical"):
        raise ValueError("Manifest vertical is required when scope=vertical")
    if manifest["payload_dir"] != PAYLOAD_DIR:
        raise ValueError(f"Manifest payload_dir must be {PAYLOAD_DIR!r}")
    if not isinstance(manifest.get("files"), list) or len(manifest["files"]) == 0:
        raise ValueError("Manifest files must be a non-empty list")


def _load_bundle(bundle_path: Path) -> tuple[dict, dict[str, tarfile.TarInfo]]:
    if not bundle_path.exists():
        raise FileNotFoundError(f"Bundle not found: {bundle_path}")

    with tarfile.open(bundle_path, mode="r:gz") as tar:
        members = {m.name: m for m in tar.getmembers()}
        if "manifest.json" not in members:
            raise ValueError("Bundle missing manifest.json")

        manifest_file = tar.extractfile("manifest.json")
        if manifest_file is None:
            raise ValueError("Unable to read manifest.json from bundle")
        manifest = json.load(manifest_file)
        _validate_manifest(manifest)

        payload_members = {
            name: member
            for name, member in members.items()
            if name.startswith(PAYLOAD_DIR + "/") and member.isfile()
        }
        if not payload_members:
            raise ValueError("Bundle has no files under docs_payload/")

        for spec in manifest["files"]:
            if not isinstance(spec, dict):
                raise ValueError("Manifest files entry must be an object")
            rel_str = spec.get("path")
            if not isinstance(rel_str, str) or not rel_str:
                raise ValueError("Manifest files[].path must be a non-empty string")
            rel_path = Path(rel_str)
            if not _safe_rel_path(rel_path):
                raise ValueError(f"Unsafe path in manifest files: {rel_str!r}")
            archive_path = f"{PAYLOAD_DIR}/{rel_path.as_posix()}"
            if archive_path not in payload_members:
                raise ValueError(f"Manifest file not found in bundle: {archive_path}")

        return manifest, payload_members


def cmd_bundle(args: argparse.Namespace) -> int:
    source_dir = Path(args.source).resolve()
    output = Path(args.output).resolve()
    producer = _slugify(args.producer)
    scope = args.scope
    vertical = _slugify(args.vertical) if args.vertical else ""

    if scope == "vertical" and not vertical:
        raise ValueError("--vertical is required when --scope=vertical")
    if scope == "core":
        vertical = ""

    if not source_dir.exists() or not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    files = _collect_payload_files(source_dir)
    if not files:
        raise ValueError(f"No allowed files found in source directory: {source_dir}")

    payload_specs = []
    for rel in files:
        src = source_dir / rel
        payload_specs.append(
            {
                "path": rel.as_posix(),
                "sha256": _sha256_file(src),
                "size": src.stat().st_size,
            }
        )

    bundle_id = args.bundle_id or f"{producer}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    source_commit = args.source_commit or os.environ.get("DOCS_SOURCE_COMMIT", "")
    manifest = {
        "contract_version": CONTRACT_VERSION,
        "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
        "bundle_id": bundle_id,
        "generated_at_utc": _utc_now_iso(),
        "producer": producer,
        "scope": scope,
        "vertical": vertical,
        "payload_dir": PAYLOAD_DIR,
        "source_relative_path": str(source_dir),
        "source_commit": source_commit,
        "files": payload_specs,
    }

    if args.dry_run:
        print(json.dumps({"mode": "bundle-dry-run", "manifest": manifest}, indent=2))
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_bytes = json.dumps(manifest, sort_keys=True, indent=2).encode("utf-8")

    with tarfile.open(output, mode="w:gz") as tar:
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(manifest_bytes)
        info.mtime = int(time.time())
        tar.addfile(info, io.BytesIO(manifest_bytes))

        for rel in files:
            src = source_dir / rel
            arcname = f"{PAYLOAD_DIR}/{rel.as_posix()}"
            tar.add(src, arcname=arcname, recursive=False)

    print(
        json.dumps(
            {
                "status": "ok",
                "command": "bundle",
                "bundle": str(output),
                "file_count": len(files),
                "scope": scope,
                "producer": producer,
                "vertical": vertical or None,
            },
            indent=2,
        )
    )
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    bundle_path = Path(args.bundle).resolve()
    manifest, payload_members = _load_bundle(bundle_path)

    with tarfile.open(bundle_path, mode="r:gz") as tar:
        for spec in manifest["files"]:
            rel = Path(spec["path"])
            archive_path = f"{PAYLOAD_DIR}/{rel.as_posix()}"
            extracted = tar.extractfile(archive_path)
            if extracted is None:
                raise ValueError(f"Could not extract {archive_path}")
            digest = hashlib.sha256(extracted.read()).hexdigest()
            if digest != spec["sha256"]:
                raise ValueError(f"SHA256 mismatch for {archive_path}")

    print(
        json.dumps(
            {
                "status": "ok",
                "command": "validate",
                "bundle": str(bundle_path),
                "scope": manifest["scope"],
                "producer": manifest["producer"],
                "vertical": manifest.get("vertical") or None,
                "file_count": len(payload_members),
            },
            indent=2,
        )
    )
    return 0


def _resolve_target_dir(repo_root: Path, manifest: dict, core_root: Path, vertical_root: Path) -> Path:
    scope = manifest["scope"]
    if scope == "core":
        producer = _slugify(manifest["producer"])
        return repo_root / core_root / producer

    vertical = _slugify(manifest["vertical"])
    return repo_root / vertical_root / vertical


def cmd_ingest(args: argparse.Namespace) -> int:
    bundle_path = Path(args.bundle).resolve()
    repo_root = Path(args.repo_root).resolve()
    core_root = Path(args.core_root)
    vertical_root = Path(args.vertical_root)

    manifest, _payload_members = _load_bundle(bundle_path)
    target_dir = _resolve_target_dir(repo_root, manifest, core_root=core_root, vertical_root=vertical_root)

    context = {
        "scope": manifest["scope"],
        "vertical": manifest.get("vertical", ""),
        "producer": manifest["producer"],
        "target_dir": str(target_dir),
        "bundle": str(bundle_path),
    }

    with tempfile.TemporaryDirectory(prefix="docs_federation_ingest_") as tmp:
        tmp_dir = Path(tmp)
        extracted_payload = tmp_dir / PAYLOAD_DIR
        extracted_payload.mkdir(parents=True, exist_ok=True)

        with tarfile.open(bundle_path, mode="r:gz") as tar:
            for spec in manifest["files"]:
                rel = Path(spec["path"])
                if not _safe_rel_path(rel):
                    raise ValueError(f"Unsafe payload path in manifest: {rel!s}")

                arcname = f"{PAYLOAD_DIR}/{rel.as_posix()}"
                extracted = tar.extractfile(arcname)
                if extracted is None:
                    raise ValueError(f"Could not extract {arcname} from bundle")

                dst = extracted_payload / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                with dst.open("wb") as out:
                    shutil.copyfileobj(extracted, out)

        copied_files = 0
        for src in extracted_payload.rglob("*"):
            if not src.is_file():
                continue
            rel = src.relative_to(extracted_payload)
            if not _safe_rel_path(rel):
                raise ValueError(f"Unsafe extracted payload path: {rel!s}")
            dst = target_dir / rel
            if not args.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            copied_files += 1

    metadata = dict(manifest)
    metadata["ingested_at_utc"] = _utc_now_iso()

    if not args.dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = target_dir / "_federation_manifest.json"
        metadata_file.write_text(json.dumps(metadata, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    hook_template = os.environ.get("DOCS_KB_INGEST_CMD", "").strip()
    hook_cmd = ""
    if hook_template:
        hook_cmd = _render_hook(hook_template, context)
        if not args.dry_run:
            subprocess.run(hook_cmd, shell=True, check=True, cwd=str(repo_root))

    print(
        json.dumps(
            {
                "status": "ok",
                "command": "ingest",
                "bundle": str(bundle_path),
                "scope": manifest["scope"],
                "producer": manifest["producer"],
                "vertical": manifest.get("vertical") or None,
                "target_dir": str(target_dir),
                "copied_files": copied_files,
                "dry_run": args.dry_run,
                "kb_hook_executed": bool(hook_cmd) and not args.dry_run,
                "kb_hook_command": hook_cmd or None,
            },
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Federated docs bundle tooling")
    sub = parser.add_subparsers(dest="command", required=True)

    bundle = sub.add_parser("bundle", help="Build docs bundle")
    bundle.add_argument("--scope", required=True, choices=("core", "vertical"))
    bundle.add_argument("--producer", required=True)
    bundle.add_argument("--vertical")
    bundle.add_argument("--source", default="docs")
    bundle.add_argument("--output", required=True)
    bundle.add_argument("--source-commit")
    bundle.add_argument("--bundle-id")
    bundle.add_argument("--dry-run", action="store_true")
    bundle.set_defaults(func=cmd_bundle)

    validate = sub.add_parser("validate", help="Validate docs bundle")
    validate.add_argument("--bundle", required=True)
    validate.set_defaults(func=cmd_validate)

    ingest = sub.add_parser("ingest", help="Ingest docs bundle into repo")
    ingest.add_argument("--bundle", required=True)
    ingest.add_argument("--repo-root", default=".")
    ingest.add_argument("--core-root", default=str(DEFAULT_CORE_ROOT))
    ingest.add_argument("--vertical-root", default=str(DEFAULT_VERTICAL_ROOT))
    ingest.add_argument("--dry-run", action="store_true")
    ingest.set_defaults(func=cmd_ingest)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
