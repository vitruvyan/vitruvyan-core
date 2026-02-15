"""
MkDocs KB Guardrails (Architectural)
====================================

These checks keep the official MkDocs knowledge base aligned with the repo state.

Scope:
  - MkDocs configs:
      - infrastructure/docker/mkdocs/mkdocs.docs.yml (PUBLIC docs)
      - infrastructure/docker/mkdocs/mkdocs.yml      (ADMIN docs)

Guardrails:
  1) Every file referenced in MkDocs `nav` exists in the repository.
  2) Nav pages (and their optional `.it.md` suffix translations) do not contain
     known-stale references that historically caused drift/broken guidance.

These checks are intentionally narrow to avoid false positives from historical
or non-nav markdown files.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Iterable

import pytest
import yaml

pytestmark = pytest.mark.architectural

PROJECT_ROOT = Path(__file__).resolve().parents[2]

_MKDOCS_CONFIGS = (
    PROJECT_ROOT / "infrastructure" / "docker" / "mkdocs" / "mkdocs.docs.yml",
    PROJECT_ROOT / "infrastructure" / "docker" / "mkdocs" / "mkdocs.yml",
)


class _MkDocsYamlLoader(yaml.SafeLoader):
    """Safe-ish loader that tolerates MkDocs' `!!python/name:` tags.

    We only need the `nav` section; those tags appear under markdown extensions.
    """


def _construct_python_name(loader: _MkDocsYamlLoader, suffix: str, node: Any) -> str:
    del loader, node
    return suffix


_MkDocsYamlLoader.add_multi_constructor("tag:yaml.org,2002:python/name:", _construct_python_name)


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_MkDocsYamlLoader)


def _iter_nav_paths(nav: Any) -> Iterable[str]:
    if nav is None:
        return

    if isinstance(nav, str):
        yield nav
        return

    if isinstance(nav, list):
        for item in nav:
            yield from _iter_nav_paths(item)
        return

    if isinstance(nav, dict):
        for _, value in nav.items():
            yield from _iter_nav_paths(value)
        return

    raise TypeError(f"Unexpected mkdocs nav node type: {type(nav)}")


def _strip_anchor(path: str) -> str:
    return path.split("#", 1)[0]


def _is_external(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")


def _iter_nav_markdown_files(config_path: Path) -> Iterable[Path]:
    config = _load_yaml(config_path)
    nav = config.get("nav")

    for raw in _iter_nav_paths(nav):
        if not isinstance(raw, str):
            continue

        if _is_external(raw):
            continue

        file_path = _strip_anchor(raw).lstrip("/")
        if not file_path:
            continue

        md_path = PROJECT_ROOT / file_path
        yield md_path


def test_mkdocs_nav_files_exist() -> None:
    missing: list[str] = []

    for config_path in _MKDOCS_CONFIGS:
        for md_path in _iter_nav_markdown_files(config_path):
            if not md_path.exists():
                missing.append(f"{config_path.relative_to(PROJECT_ROOT)} -> {md_path.relative_to(PROJECT_ROOT)}")

    assert not missing, "MkDocs nav references missing files:\n" + "\n".join(sorted(missing))


_BANNED_SUBSTRINGS = (
    "_ALBERATURA_FRAMEWORK_DA-IMPLEMENTARE_FEB12_2026.md",
    "finance_plugin.py",
    'route="ne_valid"',
    "(default: `finance`)",
    '(default "finance")',
    '(default `"finance"`)',
)

_BANNED_REGEXES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"os\.(?:getenv|environ\.get)\(\s*['\"]INTENT_DOMAIN['\"]\s*,\s*['\"]finance['\"]\s*\)"
    ),
)


def test_mkdocs_nav_pages_do_not_contain_known_stale_refs() -> None:
    violations: list[str] = []

    for config_path in _MKDOCS_CONFIGS:
        for md_path in _iter_nav_markdown_files(config_path):
            if md_path.suffix != ".md" or not md_path.exists():
                continue

            candidates = [md_path]
            it_path = md_path.with_suffix(".it.md")
            if it_path.exists():
                candidates.append(it_path)

            for candidate in candidates:
                text = candidate.read_text(encoding="utf-8", errors="ignore")

                for needle in _BANNED_SUBSTRINGS:
                    if needle in text:
                        violations.append(f"{candidate.relative_to(PROJECT_ROOT)} contains '{needle}'")

                for rx in _BANNED_REGEXES:
                    if rx.search(text):
                        violations.append(f"{candidate.relative_to(PROJECT_ROOT)} matches /{rx.pattern}/")

    assert not violations, "MkDocs nav pages contain stale references:\n" + "\n".join(sorted(violations))
