#!/usr/bin/env python3
"""
Docs Federation tooling.

Commands:
- bundle: produce a tar.gz with markdown files + manifest metadata
- ingest: route bundled docs into federated KB folders and refresh indexes
- validate: check front matter contract for markdown files
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
from typing import Any


VALID_SCOPES = {"core", "vertical"}
DEFAULT_SCAN_ROOTS = ("docs", "vitruvyan_core", "services", "infrastructure", "examples", "config")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def as_posix(path: Path) -> str:
    return path.as_posix()


def safe_rel_path(raw: str) -> PurePosixPath:
    rel = PurePosixPath(raw)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe relative path: {raw}")
    return rel


def parse_front_matter(text: str) -> tuple[dict[str, str], bool, str]:
    """
    Parse minimal YAML-like front matter.
    Supports only flat `key: value` lines.
    """
    if not text.startswith("---\n"):
        return {}, False, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, False, text

    block = text[4:end]
    body = text[end + len("\n---\n") :]
    data: dict[str, str] = {}
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip().lower()] = value.strip().strip("'\"")
    return data, True, body


def extract_title(text_without_front_matter: str, fallback: str) -> str:
    for raw_line in text_without_front_matter.splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(8192)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def run_git(repo_root: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git command failed: {' '.join(args)}")
    return proc.stdout


def discover_markdown_files(
    repo_root: Path,
    roots: tuple[str, ...],
    changed_only: bool,
    base_ref: str,
    include_uncommitted: bool,
) -> list[PurePosixPath]:
    if changed_only:
        rels: set[str] = set()
        try:
            out = run_git(repo_root, ["diff", "--name-only", "--diff-filter=ACMRTUXB", f"{base_ref}...HEAD"])
            rels.update(line.strip() for line in out.splitlines() if line.strip())
        except RuntimeError:
            # Fallback when base ref is missing in shallow/isolated checkouts.
            out = run_git(repo_root, ["diff", "--name-only", "--diff-filter=ACMRTUXB", "HEAD~1...HEAD"])
            rels.update(line.strip() for line in out.splitlines() if line.strip())

        if include_uncommitted:
            for git_args in (["diff", "--name-only"], ["diff", "--name-only", "--cached"]):
                out = run_git(repo_root, git_args)
                rels.update(line.strip() for line in out.splitlines() if line.strip())

        files: list[PurePosixPath] = []
        for rel in sorted(rels):
            if not rel.lower().endswith(".md"):
                continue
            rel_path = safe_rel_path(rel)
            if (repo_root / rel_path).is_file():
                files.append(rel_path)
        return files

    files: list[PurePosixPath] = []
    for root in roots:
        base = repo_root / root
        if not base.exists():
            continue
        for candidate in sorted(base.rglob("*.md")):
            if candidate.is_file():
                files.append(safe_rel_path(as_posix(candidate.relative_to(repo_root))))
    return files


def normalize_entry(
    rel_path: PurePosixPath,
    abs_path: Path,
    default_scope: str,
    default_vertical: str,
    source_repo: str,
    source_vps: str,
) -> dict[str, Any]:
    text = abs_path.read_text(encoding="utf-8")
    front_matter, has_front_matter, body = parse_front_matter(text)

    warnings: list[str] = []
    scope = front_matter.get("scope", default_scope).strip().lower()
    if scope not in VALID_SCOPES:
        warnings.append(f"invalid scope '{scope}' -> fallback '{default_scope}'")
        scope = default_scope

    vertical = front_matter.get("vertical", default_vertical if scope == "vertical" else "").strip().lower()
    if scope == "vertical" and not vertical:
        vertical = default_vertical
        warnings.append(f"missing vertical -> fallback '{default_vertical}'")
    if scope == "core":
        vertical = ""

    title = extract_title(body, rel_path.stem.replace("_", " ").replace("-", " "))
    kb_section = "core" if scope == "core" else f"verticals/{vertical}"

    return {
        "path": rel_path.as_posix(),
        "title": title,
        "scope": scope,
        "vertical": vertical,
        "kb_section": kb_section,
        "sha256": sha256_file(abs_path),
        "size_bytes": abs_path.stat().st_size,
        "has_front_matter": has_front_matter,
        "warnings": warnings,
        "source_repo": front_matter.get("source_repo", source_repo),
        "source_vps": front_matter.get("source_vps", source_vps),
        "source_commit": front_matter.get("source_commit", ""),
        "updated_at": front_matter.get("updated_at", ""),
    }


def cmd_bundle(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    files = discover_markdown_files(
        repo_root=repo_root,
        roots=tuple(args.roots),
        changed_only=args.changed_only,
        base_ref=args.base_ref,
        include_uncommitted=args.include_uncommitted,
    )

    source_repo = args.source_repo or repo_root.name
    source_vps = args.source_vps or os.uname().nodename

    entries: list[dict[str, Any]] = []
    for rel in files:
        entry = normalize_entry(
            rel_path=rel,
            abs_path=repo_root / rel,
            default_scope=args.default_scope,
            default_vertical=args.default_vertical,
            source_repo=source_repo,
            source_vps=source_vps,
        )
        entries.append(entry)

    manifest = {
        "schema_version": "1.0",
        "generated_at": now_iso(),
        "base_ref": args.base_ref,
        "changed_only": bool(args.changed_only),
        "source_repo": source_repo,
        "source_vps": source_vps,
        "default_scope": args.default_scope,
        "default_vertical": args.default_vertical,
        "files_count": len(entries),
        "files": entries,
    }

    with tarfile.open(output, "w:gz") as tar:
        for entry in entries:
            rel = safe_rel_path(entry["path"])
            tar.add(
                str(repo_root / rel),
                arcname=f"payload/{rel.as_posix()}",
                recursive=False,
            )

        payload = json.dumps(manifest, indent=2, ensure_ascii=True).encode("utf-8")
        info = tarfile.TarInfo("manifest.json")
        info.size = len(payload)
        info.mtime = int(dt.datetime.now().timestamp())
        tar.addfile(info, io.BytesIO(payload))

    print(f"bundle_created={output}")
    print(f"files_count={len(entries)}")
    return 0


def extract_manifest(tar: tarfile.TarFile) -> dict[str, Any]:
    try:
        member = tar.getmember("manifest.json")
    except KeyError as exc:
        raise RuntimeError("bundle missing manifest.json") from exc
    fh = tar.extractfile(member)
    if fh is None:
        raise RuntimeError("cannot read manifest.json from bundle")
    return json.loads(fh.read().decode("utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def list_markdown(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        p for p in root.rglob("*.md") if p.is_file() and p.name.lower() != "readme.md"
    )


def build_root_readme(federated_root: Path) -> None:
    content = [
        "# Federated Documentation Hub",
        "",
        "Aggregated documentation published by multiple Vitruvyan VPS nodes.",
        "",
        f"- Last refresh: `{now_iso()}`",
        "",
        "## Sections",
        "",
        "- [Core Contributions](core/README.md)",
        "- [Vertical Contributions](verticals/README.md)",
        "",
    ]
    write_text(federated_root / "README.md", "\n".join(content))


def build_core_readme(core_root: Path) -> None:
    lines = [
        "# Core Federated Contributions",
        "",
        "Core-scoped documentation pushed from vertical/core nodes.",
        "",
    ]
    if not core_root.exists():
        lines.append("_No core contributions yet._")
        lines.append("")
        write_text(core_root / "README.md", "\n".join(lines))
        return

    repo_dirs = sorted(p for p in core_root.iterdir() if p.is_dir())
    if not repo_dirs:
        lines.append("_No core contributions yet._")
        lines.append("")
        write_text(core_root / "README.md", "\n".join(lines))
        return

    for repo_dir in repo_dirs:
        lines.append(f"## {repo_dir.name}")
        lines.append("")
        docs = list_markdown(repo_dir)
        if not docs:
            lines.append("- _No documents_")
            lines.append("")
            continue
        for doc in docs:
            rel = doc.relative_to(core_root).as_posix()
            label = doc.stem.replace("_", " ")
            lines.append(f"- [{label}]({rel})")
        lines.append("")

    write_text(core_root / "README.md", "\n".join(lines))


def build_vertical_readmes(verticals_root: Path) -> None:
    lines = [
        "# Vertical Federated Contributions",
        "",
        "Vertical/domain documentation grouped by vertical name.",
        "",
    ]
    if not verticals_root.exists():
        lines.append("_No vertical contributions yet._")
        lines.append("")
        write_text(verticals_root / "README.md", "\n".join(lines))
        return

    vertical_dirs = sorted(p for p in verticals_root.iterdir() if p.is_dir())
    if not vertical_dirs:
        lines.append("_No vertical contributions yet._")
        lines.append("")
        write_text(verticals_root / "README.md", "\n".join(lines))
        return

    for vertical_dir in vertical_dirs:
        vertical_readme = vertical_dir / "README.md"
        lines.append(f"- [{vertical_dir.name}]({vertical_dir.name}/README.md)")

        v_lines = [
            f"# Vertical: {vertical_dir.name}",
            "",
            f"Last refresh: `{now_iso()}`",
            "",
        ]
        repo_dirs = sorted(p for p in vertical_dir.iterdir() if p.is_dir())
        if not repo_dirs:
            v_lines.append("_No documents yet._")
            v_lines.append("")
            write_text(vertical_readme, "\n".join(v_lines))
            continue
        for repo_dir in repo_dirs:
            v_lines.append(f"## {repo_dir.name}")
            v_lines.append("")
            docs = list_markdown(repo_dir)
            if not docs:
                v_lines.append("- _No documents_")
                v_lines.append("")
                continue
            for doc in docs:
                rel = doc.relative_to(vertical_dir).as_posix()
                label = doc.stem.replace("_", " ")
                v_lines.append(f"- [{label}]({rel})")
            v_lines.append("")
        write_text(vertical_readme, "\n".join(v_lines))

    lines.append("")
    write_text(verticals_root / "README.md", "\n".join(lines))


def update_mkdocs_nav(mkdocs_config: Path) -> None:
    block = [
        "    # FEDERATED_DOCS_NAV_START",
        "    - Federated Docs:",
        "      - Overview: docs/knowledge_base/federated/README.md",
        "      - Core Contributions: docs/knowledge_base/federated/core/README.md",
        "      - Vertical Contributions: docs/knowledge_base/federated/verticals/README.md",
        "    # FEDERATED_DOCS_NAV_END",
    ]
    lines = mkdocs_config.read_text(encoding="utf-8").splitlines()
    start_idx = next((i for i, line in enumerate(lines) if line.strip() == "# FEDERATED_DOCS_NAV_START"), None)
    end_idx = next((i for i, line in enumerate(lines) if line.strip() == "# FEDERATED_DOCS_NAV_END"), None)

    if start_idx is not None and end_idx is not None and end_idx >= start_idx:
        new_lines = lines[:start_idx] + block + lines[end_idx + 1 :]
    else:
        insert_idx = next((i for i, line in enumerate(lines) if line.startswith("    - Examples:")), None)
        if insert_idx is None:
            insert_idx = next((i for i, line in enumerate(lines) if line.startswith("  # - Planning:")), None)
        if insert_idx is None:
            insert_idx = len(lines)
        new_lines = lines[:insert_idx] + block + [""] + lines[insert_idx:]

    mkdocs_config.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")


def cmd_ingest(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    bundle_path = Path(args.bundle).resolve()
    federated_root = (repo_root / args.federated_root).resolve()
    mkdocs_config = (repo_root / args.mkdocs_config).resolve()

    if not bundle_path.exists():
        raise FileNotFoundError(f"bundle not found: {bundle_path}")

    with tarfile.open(bundle_path, "r:gz") as tar:
        manifest = extract_manifest(tar)
        members = {
            m.name[len("payload/") :]: m
            for m in tar.getmembers()
            if m.isfile() and m.name.startswith("payload/")
        }

        written = 0
        for entry in manifest.get("files", []):
            rel = safe_rel_path(entry["path"]).as_posix()
            member = members.get(rel)
            if member is None:
                continue
            fh = tar.extractfile(member)
            if fh is None:
                continue
            data = fh.read()

            scope = str(entry.get("scope", "vertical")).lower()
            source_repo = str(entry.get("source_repo", manifest.get("source_repo", "unknown"))).strip() or "unknown"
            vertical = str(entry.get("vertical", "")).strip().lower()
            if scope == "core":
                target = federated_root / "core" / source_repo / rel
            else:
                if not vertical:
                    vertical = "unspecified"
                target = federated_root / "verticals" / vertical / source_repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            written += 1

    build_root_readme(federated_root)
    build_core_readme(federated_root / "core")
    build_vertical_readmes(federated_root / "verticals")

    if args.update_mkdocs_nav and mkdocs_config.exists():
        update_mkdocs_nav(mkdocs_config)

    print(f"bundle_ingested={bundle_path}")
    print(f"files_written={written}")
    print(f"federated_root={federated_root}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    files = discover_markdown_files(
        repo_root=repo_root,
        roots=tuple(args.roots),
        changed_only=args.changed_only,
        base_ref=args.base_ref,
        include_uncommitted=args.include_uncommitted,
    )
    source_repo = args.source_repo or repo_root.name
    source_vps = args.source_vps or os.uname().nodename

    issues = 0
    checked = 0
    for rel in files:
        entry = normalize_entry(
            rel_path=rel,
            abs_path=repo_root / rel,
            default_scope=args.default_scope,
            default_vertical=args.default_vertical,
            source_repo=source_repo,
            source_vps=source_vps,
        )
        checked += 1
        if not entry["has_front_matter"]:
            issues += 1
            print(f"[WARN] missing front matter: {entry['path']}")
        if entry["scope"] == "vertical" and not entry["vertical"]:
            issues += 1
            print(f"[WARN] missing vertical field: {entry['path']}")
        for warning in entry["warnings"]:
            issues += 1
            print(f"[WARN] {entry['path']}: {warning}")

    print(f"checked_files={checked}")
    print(f"issues={issues}")
    if args.strict and issues > 0:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Federated docs tooling")
    sub = parser.add_subparsers(dest="command", required=True)

    bundle = sub.add_parser("bundle", help="Create docs bundle tar.gz")
    bundle.add_argument("--repo-root", default=".")
    bundle.add_argument("--output", required=True)
    bundle.add_argument("--roots", nargs="+", default=list(DEFAULT_SCAN_ROOTS))
    bundle.add_argument("--changed-only", action="store_true", default=False)
    bundle.add_argument("--base-ref", default="origin/main")
    bundle.add_argument("--include-uncommitted", action="store_true", default=False)
    bundle.add_argument("--default-scope", choices=sorted(VALID_SCOPES), default="vertical")
    bundle.add_argument("--default-vertical", default="mercator")
    bundle.add_argument("--source-repo", default="")
    bundle.add_argument("--source-vps", default="")
    bundle.set_defaults(func=cmd_bundle)

    ingest = sub.add_parser("ingest", help="Ingest docs bundle into federated KB")
    ingest.add_argument("--repo-root", default=".")
    ingest.add_argument("--bundle", required=True)
    ingest.add_argument("--federated-root", default="docs/knowledge_base/federated")
    ingest.add_argument("--mkdocs-config", default="infrastructure/docker/mkdocs/mkdocs.yml")
    ingest.add_argument("--update-mkdocs-nav", action="store_true", default=False)
    ingest.set_defaults(func=cmd_ingest)

    validate = sub.add_parser("validate", help="Validate docs front matter contract")
    validate.add_argument("--repo-root", default=".")
    validate.add_argument("--roots", nargs="+", default=list(DEFAULT_SCAN_ROOTS))
    validate.add_argument("--changed-only", action="store_true", default=False)
    validate.add_argument("--base-ref", default="origin/main")
    validate.add_argument("--include-uncommitted", action="store_true", default=False)
    validate.add_argument("--default-scope", choices=sorted(VALID_SCOPES), default="vertical")
    validate.add_argument("--default-vertical", default="mercator")
    validate.add_argument("--source-repo", default="")
    validate.add_argument("--source-vps", default="")
    validate.add_argument("--strict", action="store_true", default=False)
    validate.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
