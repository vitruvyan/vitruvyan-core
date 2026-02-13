"""
Test Sacred Order Structure
==============================

Verifica statica che ogni Sacred Order conforme segua il
SACRED_ORDER_PATTERN: 10 directory obbligatorie, nessun .py
in root (tranne __init__.py), charter.md presente.

Non importa moduli runtime — usa solo pathlib.
"""

import pytest
from pathlib import Path

pytestmark = pytest.mark.architectural

GOVERNANCE_ROOT = Path(__file__).resolve().parents[2] / "vitruvyan_core" / "core" / "governance"

# Sacred Order che devono essere conformi (esclude semantic_sync che è stub)
CONFORMANT_ORDERS = ["codex_hunters", "memory_orders", "orthodoxy_wardens", "vault_keepers"]

REQUIRED_DIRS = [
    "domain",
    "consumers",
    "governance",
    "events",
    "monitoring",
    "philosophy",
    "docs",
    "examples",
    "tests",
    "_legacy",
]


class TestSacredOrderDirectories:
    """Verifica che le 10 directory obbligatorie esistano."""

    @pytest.mark.parametrize("order", CONFORMANT_ORDERS)
    def test_required_directories_exist(self, order):
        """Ogni Sacred Order deve avere tutte e 10 le directory."""
        order_root = GOVERNANCE_ROOT / order
        assert order_root.is_dir(), f"Sacred Order {order} non trovata"

        missing = []
        for d in REQUIRED_DIRS:
            if not (order_root / d).is_dir():
                missing.append(d)

        assert not missing, (
            f"Sacred Order '{order}' manca delle directory: {missing}"
        )

    @pytest.mark.parametrize("order", CONFORMANT_ORDERS)
    def test_no_root_python_files(self, order):
        """Nessun .py in root (tranne __init__.py)."""
        order_root = GOVERNANCE_ROOT / order
        violations = [
            f.name
            for f in order_root.glob("*.py")
            if f.name != "__init__.py"
        ]
        assert not violations, (
            f"Sacred Order '{order}' ha file .py in root: {violations}. "
            "Spostali in consumers/, governance/ o _legacy/"
        )

    @pytest.mark.parametrize("order", CONFORMANT_ORDERS)
    def test_charter_exists(self, order):
        """philosophy/charter.md deve esistere."""
        charter = GOVERNANCE_ROOT / order / "philosophy" / "charter.md"
        assert charter.is_file(), (
            f"Sacred Order '{order}': manca philosophy/charter.md"
        )

    @pytest.mark.parametrize("order", CONFORMANT_ORDERS)
    def test_init_files_in_python_dirs(self, order):
        """Le directory Python devono avere __init__.py."""
        order_root = GOVERNANCE_ROOT / order
        python_dirs = ["domain", "consumers", "governance", "events", "monitoring"]
        missing_init = []
        for d in python_dirs:
            dir_path = order_root / d
            if dir_path.is_dir() and not (dir_path / "__init__.py").is_file():
                missing_init.append(d)

        assert not missing_init, (
            f"Sacred Order '{order}': __init__.py mancante in: {missing_init}"
        )


class TestGovernanceRoot:
    """Verifica la root di governance/."""

    def test_governance_root_exists(self):
        assert GOVERNANCE_ROOT.is_dir(), "vitruvyan_core/core/governance/ non trovata"

    def test_pattern_doc_exists(self):
        """SACRED_ORDER_PATTERN.md deve esistere."""
        pattern_doc = GOVERNANCE_ROOT / "SACRED_ORDER_PATTERN.md"
        assert pattern_doc.is_file(), "SACRED_ORDER_PATTERN.md mancante"

    def test_known_orders_present(self):
        """Tutti gli ordini conformi devono essere presenti come directory."""
        for order in CONFORMANT_ORDERS:
            assert (GOVERNANCE_ROOT / order).is_dir(), f"{order} mancante"


class TestVPARStructure:
    """Verifica struttura del modulo VPAR."""

    VPAR_ROOT = Path(__file__).resolve().parents[2] / "vitruvyan_core" / "core" / "vpar"
    EXPECTED_ENGINES = ["vee", "vare", "vsgs", "vwre"]

    def test_vpar_root_exists(self):
        assert self.VPAR_ROOT.is_dir(), "vitruvyan_core/core/vpar/ non trovata"

    @pytest.mark.parametrize("engine", EXPECTED_ENGINES)
    def test_engine_directory_exists(self, engine):
        """Ogni motore VPAR deve avere la propria directory."""
        assert (self.VPAR_ROOT / engine).is_dir(), f"vpar/{engine}/ mancante"

    @pytest.mark.parametrize("engine", EXPECTED_ENGINES)
    def test_engine_has_main_file(self, engine):
        """Ogni motore VPAR deve avere il file <engine>_engine.py."""
        engine_file = self.VPAR_ROOT / engine / f"{engine}_engine.py"
        assert engine_file.is_file(), f"vpar/{engine}/{engine}_engine.py mancante"


class TestDomainContracts:
    """Verifica che i contratti di dominio esistano."""

    DOMAINS_ROOT = Path(__file__).resolve().parents[2] / "vitruvyan_core" / "domains"
    REQUIRED_CONTRACTS = [
        "explainability_contract.py",
        "risk_contract.py",
        "aggregation_contract.py",
    ]

    def test_domains_root_exists(self):
        assert self.DOMAINS_ROOT.is_dir(), "vitruvyan_core/domains/ non trovata"

    @pytest.mark.parametrize("contract", REQUIRED_CONTRACTS)
    def test_contract_exists(self, contract):
        assert (self.DOMAINS_ROOT / contract).is_file(), f"domains/{contract} mancante"
