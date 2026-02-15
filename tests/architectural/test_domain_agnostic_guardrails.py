"""
Domain-Agnostic Guardrails (Architectural)
==========================================

Static checks to prevent vertical-specific leakage into the core.

Scope:
  - vitruvyan_core/core/**.py
  - excludes: _legacy/, tests/, examples/, __pycache__/, neural_engine/domain_examples/

Guardrails:
  1) No direct imports of vertical packages (e.g., domains.finance.*) from core
  2) No hard-coded branching on a specific vertical string (e.g., if domain == "finance")
  3) INTENT_DOMAIN default remains "generic" in graph_flow.py

These checks are intentionally narrow to avoid false positives from docs/examples.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, Optional

import pytest

pytestmark = pytest.mark.architectural

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "vitruvyan_core" / "core"

_EXCLUDE_PATH_SNIPPETS = (
    "/_legacy/",
    "/tests/",
    "/examples/",
    "/__pycache__/",
    "/domain_examples/",
)


def _iter_core_py_files() -> Iterable[Path]:
    for py_file in CORE_ROOT.rglob("*.py"):
        p = str(py_file)
        if any(snippet in p for snippet in _EXCLUDE_PATH_SNIPPETS):
            continue
        yield py_file


def _parse_ast(py_file: Path) -> Optional[ast.AST]:
    try:
        return ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return None


def _is_vertical_module(module: str) -> bool:
    return module.startswith("domains.finance") or module.startswith("vitruvyan_core.domains.finance")


def test_no_direct_finance_imports_in_core() -> None:
    violations: list[str] = []

    for py_file in _iter_core_py_files():
        tree = _parse_ast(py_file)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_vertical_module(alias.name):
                        violations.append(
                            f"{py_file.relative_to(PROJECT_ROOT)}:{node.lineno} import {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module and _is_vertical_module(node.module):
                    violations.append(
                        f"{py_file.relative_to(PROJECT_ROOT)}:{node.lineno} from {node.module} import ..."
                    )

    assert not violations, (
        "Vertical-specific imports found in core (must be plugin-loaded via importlib):\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


def test_no_hardcoded_finance_branching_in_core() -> None:
    violations: list[str] = []
    finance_value = "finance"
    branch_ops = (ast.Eq, ast.NotEq, ast.In, ast.NotIn)

    for py_file in _iter_core_py_files():
        tree = _parse_ast(py_file)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue

            if not any(isinstance(op, branch_ops) for op in node.ops):
                continue

            # Compare sides include: left + comparators (handles `x in ("finance", ...)`)
            sides = [node.left, *node.comparators]
            if any(
                isinstance(side, ast.Constant) and side.value == finance_value
                for side in sides
            ):
                violations.append(f"{py_file.relative_to(PROJECT_ROOT)}:{node.lineno} compares to 'finance'")

    assert not violations, (
        "Hard-coded branching on vertical 'finance' found in core. "
        "Use dynamic plugin loading and string-based domain selection:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


def test_no_constant_importlib_import_module_finance_in_core() -> None:
    violations: list[str] = []

    for py_file in _iter_core_py_files():
        tree = _parse_ast(py_file)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if not (isinstance(node.func, ast.Attribute) and node.func.attr == "import_module"):
                continue

            module_name = None
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                module_name = node.args[0].value
            if module_name is None:
                for kw in node.keywords or []:
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        module_name = kw.value.value

            if module_name and _is_vertical_module(module_name):
                violations.append(
                    f"{py_file.relative_to(PROJECT_ROOT)}:{node.lineno} importlib.import_module({module_name!r})"
                )

    assert not violations, (
        "Hard-coded importlib.import_module() of vertical package found in core. "
        "Use dynamic module paths (domains.{domain}.*):\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


def test_graph_flow_intent_domain_default_is_generic() -> None:
    graph_flow = CORE_ROOT / "orchestration" / "langgraph" / "graph_flow.py"
    assert graph_flow.is_file(), "graph_flow.py not found"

    tree = _parse_ast(graph_flow)
    assert tree is not None, "graph_flow.py could not be parsed"

    getenv_defaults: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        # _os.getenv("INTENT_DOMAIN", "generic")
        if isinstance(node.func, ast.Attribute) and node.func.attr == "getenv":
            if not node.args:
                continue
            if not (isinstance(node.args[0], ast.Constant) and node.args[0].value == "INTENT_DOMAIN"):
                continue

            if len(node.args) < 2:
                pytest.fail("INTENT_DOMAIN getenv() call has no default (must default to 'generic').")

            default = node.args[1]
            if isinstance(default, ast.Constant) and isinstance(default.value, str):
                getenv_defaults.append(default.value)

        # os.environ.get("INTENT_DOMAIN", "generic")
        if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            if not (isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "environ"):
                continue
            if not node.args:
                continue
            if not (isinstance(node.args[0], ast.Constant) and node.args[0].value == "INTENT_DOMAIN"):
                continue
            if len(node.args) < 2:
                pytest.fail("INTENT_DOMAIN environ.get() call has no default (must default to 'generic').")
            default = node.args[1]
            if isinstance(default, ast.Constant) and isinstance(default.value, str):
                getenv_defaults.append(default.value)

    assert getenv_defaults, "No INTENT_DOMAIN getenv() default found in graph_flow.py"
    assert all(d == "generic" for d in getenv_defaults), (
        f"INTENT_DOMAIN default must be 'generic' in graph_flow.py; found: {sorted(set(getenv_defaults))}"
    )
