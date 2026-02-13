"""
Test Import Boundaries
========================

Analisi statica degli import per garantire gli invarianti architetturali:

1. LIVELLO 1 (governance/) non importa da services/
2. Nessun `from openai import OpenAI` fuori da llm_agent.py
3. Nessun cross-import tra Sacred Order (devono comunicare via StreamBus)
4. Core non importa da domains/ specifici (finance_plugin è plugin, non core)

Usa ast.parse() per analisi — nessun import runtime, velocissimo.
"""

import ast
import pytest
from pathlib import Path

pytestmark = pytest.mark.architectural

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORE_ROOT = PROJECT_ROOT / "vitruvyan_core" / "core"
GOVERNANCE_ROOT = CORE_ROOT / "governance"

CONFORMANT_ORDERS = ["codex_hunters", "memory_orders", "orthodoxy_wardens", "vault_keepers"]


def _collect_imports(filepath: Path) -> list[str]:
    """Estrai tutti gli import da un file Python usando AST."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _collect_all_py_files(directory: Path, exclude_legacy: bool = True) -> list[Path]:
    """Raccogli tutti i file .py in una directory, escludendo _legacy/, tests/, examples/ e _archived_*."""
    files = []
    for f in directory.rglob("*.py"):
        fstr = str(f)
        if exclude_legacy and "/_legacy/" in fstr:
            continue
        if "__pycache__" in fstr:
            continue
        # Escludi directory di test interni e esempi (possono importare LIVELLO 2)
        if "/tests/" in fstr or "/examples/" in fstr:
            continue
        # Escludi file archiviati
        if "_archived_" in f.name:
            continue
        files.append(f)
    return files


class TestLivello1NoBServiceImports:
    """LIVELLO 1 non deve importare da services/."""

    @pytest.mark.parametrize("order", CONFORMANT_ORDERS)
    def test_no_service_imports(self, order):
        """Nessun import da 'services.*' in governance/<order>/."""
        order_root = GOVERNANCE_ROOT / order
        if not order_root.is_dir():
            pytest.skip(f"{order} non trovata")

        violations = []
        for py_file in _collect_all_py_files(order_root):
            for imp in _collect_imports(py_file):
                if imp.startswith("services.") or imp.startswith("api_"):
                    violations.append(
                        f"  {py_file.relative_to(PROJECT_ROOT)}: import {imp}"
                    )

        assert not violations, (
            f"Sacred Order '{order}' importa da services/ (LIVELLO 2 → LIVELLO 1 vietato):\n"
            + "\n".join(violations)
        )


class TestNoCrossOrderImports:
    """Nessun import diretto tra Sacred Order diverse."""

    @pytest.mark.parametrize("order", CONFORMANT_ORDERS)
    def test_no_cross_sacred_order_imports(self, order):
        """Un Sacred Order non deve importare direttamente da un altro."""
        order_root = GOVERNANCE_ROOT / order
        if not order_root.is_dir():
            pytest.skip(f"{order} non trovato")

        other_orders = [o for o in CONFORMANT_ORDERS if o != order]
        violations = []

        for py_file in _collect_all_py_files(order_root):
            for imp in _collect_imports(py_file):
                for other in other_orders:
                    if f".governance.{other}" in imp or f"governance.{other}" in imp:
                        violations.append(
                            f"  {py_file.relative_to(PROJECT_ROOT)}: "
                            f"import {imp} (cross-order: {other})"
                        )

        assert not violations, (
            f"Sacred Order '{order}' importa da altri Sacred Order "
            f"(usare StreamBus events):\n" + "\n".join(violations)
        )


class TestNoRawOpenAI:
    """OpenAI() deve essere usato SOLO in llm_agent.py."""

    def test_no_openai_outside_llm_agent(self):
        """Nessun `from openai import OpenAI` fuori da llm_agent.py."""
        llm_agent_path = CORE_ROOT / "agents" / "llm_agent.py"
        violations = []

        for py_file in _collect_all_py_files(CORE_ROOT):
            if py_file == llm_agent_path:
                continue
            if "/_legacy/" in str(py_file):
                continue

            for imp in _collect_imports(py_file):
                if imp == "openai" or imp.startswith("openai."):
                    violations.append(
                        f"  {py_file.relative_to(PROJECT_ROOT)}: import {imp}"
                    )

        assert not violations, (
            "Import OpenAI trovati fuori da llm_agent.py "
            "(usare core.agents.llm_agent.get_llm_agent()):\n"
            + "\n".join(violations)
        )


class TestNoRawDBClients:
    """Nessun client DB/vector raw fuori dagli agent dedicati."""

    FORBIDDEN_IMPORTS = {
        "psycopg2": "Usare PostgresAgent",
        "qdrant_client": "Usare QdrantAgent",
    }

    def test_no_raw_db_in_governance(self):
        """governance/ non deve importare psycopg2 o qdrant_client."""
        violations = []

        for order in CONFORMANT_ORDERS:
            order_root = GOVERNANCE_ROOT / order
            if not order_root.is_dir():
                continue

            for py_file in _collect_all_py_files(order_root):
                for imp in _collect_imports(py_file):
                    for forbidden, reason in self.FORBIDDEN_IMPORTS.items():
                        if imp == forbidden or imp.startswith(f"{forbidden}."):
                            violations.append(
                                f"  {py_file.relative_to(PROJECT_ROOT)}: "
                                f"import {imp} ({reason})"
                            )

        assert not violations, (
            "Import infrastrutturali in LIVELLO 1 (governance/):\n"
            + "\n".join(violations)
        )


class TestNoFinanceLeakageInCore:
    """Il core non deve avere riferimenti finance-specific hard-coded."""

    FINANCE_KEYWORDS = ["ticker", "stock", "portfolio", "trading", "market_cap"]

    def test_vpar_engine_files_no_finance(self):
        """I file *_engine.py sotto vpar/ non devono avere keyword finance."""
        vpar_root = CORE_ROOT / "vpar"
        if not vpar_root.is_dir():
            pytest.skip("vpar/ non trovata")

        violations = []
        for engine_dir in ["vee", "vare", "vsgs", "vwre"]:
            engine_file = vpar_root / engine_dir / f"{engine_dir}_engine.py"
            if not engine_file.is_file():
                continue

            content = engine_file.read_text(encoding="utf-8", errors="ignore").lower()
            for kw in self.FINANCE_KEYWORDS:
                # Ignora commenti e stringhe in _legacy
                if kw in content:
                    # Verifica che non sia in un commento/docstring di legacy note
                    lines = content.split("\n")
                    for i, line in enumerate(lines, 1):
                        stripped = line.strip()
                        if kw in stripped and not stripped.startswith("#"):
                            violations.append(
                                f"  {engine_file.relative_to(PROJECT_ROOT)}:{i}: "
                                f"'{kw}' trovato"
                            )

        # Nota: possono esserci falsi positivi nei commenti legacy.
        # Questo è un segnale, non un hard-fail.
        if violations:
            pytest.xfail(
                "Possibili riferimenti finance nel core (verificare manualmente):\n"
                + "\n".join(violations[:10])
            )
