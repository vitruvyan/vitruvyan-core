"""
LangGraph Orchestration Contract v1.0 - Pytest Enforcement
===========================================================

Automated tests to verify graph nodes comply with architectural contract.
These tests MUST pass before merge to main.

See: .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md
"""

import ast
import glob
import re
from pathlib import Path
from typing import List, Tuple

import pytest


# Forbidden operations in graph nodes
FORBIDDEN_FUNCTIONS = {"sum", "min", "max", "sorted"}
FORBIDDEN_ATTRIBUTES = {"mean", "median", "std", "var"}
DOMAIN_TERMS = ["confidence", "score", "quality", "rating", "priority", "threshold"]

NODE_DIR = Path("vitruvyan_core/core/orchestration/langgraph/node")


def get_graph_node_files() -> List[Path]:
    """Get all graph node Python files (excluding __init__.py)."""
    if not NODE_DIR.exists():
        pytest.skip(f"Node directory {NODE_DIR} not found")
    
    files = list(NODE_DIR.glob("*.py"))
    return [f for f in files if f.name != "__init__.py" and not f.name.startswith("_legacy")]


def test_graph_nodes_exist():
    """Verify graph node directory exists."""
    assert NODE_DIR.exists(), f"Graph node directory {NODE_DIR} not found"
    files = get_graph_node_files()
    assert len(files) > 0, "No graph node files found"


@pytest.mark.parametrize("node_file", get_graph_node_files())
def test_no_domain_arithmetic(node_file: Path):
    """
    Contract Section 3.1: Graph nodes MUST NOT perform domain arithmetic.
    
    Forbidden: sum(), min(), max(), .mean(), .median()
    """
    with open(node_file) as f:
        source = f.read()
        tree = ast.parse(source)
    
    violations = []
    
    # Check for forbidden function calls
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = None
            
            if hasattr(node.func, "id"):
                func_name = node.func.id
            elif hasattr(node.func, "attr"):
                func_name = node.func.attr
            
            if func_name in FORBIDDEN_FUNCTIONS:
                line_no = node.lineno
                violations.append(f"Line {line_no}: Forbidden function {func_name}()")
            
            if func_name in FORBIDDEN_ATTRIBUTES:
                line_no = node.lineno
                violations.append(f"Line {line_no}: Forbidden method .{func_name}()")
    
    if violations:
        msg = (
            f"\n❌ Contract Violation in {node_file.name}\n"
            f"Section 3.1: Domain arithmetic forbidden in orchestration\n\n"
            f"Violations:\n" + "\n".join(f"  • {v}" for v in violations) + "\n\n"
            f"Fix: Move calculations to Sacred Order service.\n"
            f"See: .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md section 4.1"
        )
        pytest.fail(msg)


@pytest.mark.parametrize("node_file", get_graph_node_files())
def test_no_average_calculations(node_file: Path):
    """
    Contract Section 3.1: Graph nodes MUST NOT calculate averages.
    
    Forbidden: / len(...)
    """
    with open(node_file) as f:
        source = f.read()
    
    # Check for average calculation pattern
    pattern = r"/ len\(|/len\("
    matches = re.finditer(pattern, source)
    
    violations = []
    for match in matches:
        # Get line number
        line_no = source[:match.start()].count('\n') + 1
        line_content = source.split('\n')[line_no - 1].strip()
        
        # Skip comments
        if line_content.startswith('#'):
            continue
        
        violations.append(f"Line {line_no}: Average calculation (/ len)")
    
    if violations:
        msg = (
            f"\n❌ Contract Violation in {node_file.name}\n"
            f"Section 3.1: Average calculations forbidden in orchestration\n\n"
            f"Violations:\n" + "\n".join(f"  • {v}" for v in violations) + "\n\n"
            f"Fix: Service must return pre-calculated average.\n"
            f"See: .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md section 4.1"
        )
        pytest.fail(msg)


@pytest.mark.parametrize("node_file", get_graph_node_files())
def test_no_semantic_thresholds(node_file: Path):
    """
    Contract Section 3.1: Graph nodes MUST NOT apply semantic thresholds.
    
    Forbidden: if confidence > 0.7, if score < threshold, etc.
    """
    with open(node_file) as f:
        source = f.read()
    
    violations = []
    
    for term in DOMAIN_TERMS:
        # Pattern: domain_term <comparison> number OR number <comparison> domain_term
        # Only match comparison operators (< > <= >= == !=), NOT assignment (=)
        pattern = f"({term}\\s*(?:[<>]=?|[!=]=)\\s*[0-9.]+|[0-9.]+\\s*(?:[<>]=?|[!=]=)\\s*{term})"
        matches = re.finditer(pattern, source, re.IGNORECASE)
        
        for match in matches:
            line_no = source[:match.start()].count('\n') + 1
            line_content = source.split('\n')[line_no - 1].strip()
            
            # Skip comments
            if line_content.startswith('#'):
                continue
            
            violations.append(f"Line {line_no}: Threshold comparison on '{term}'")
    
    if violations:
        msg = (
            f"\n❌ Contract Violation in {node_file.name}\n"
            f"Section 3.1: Semantic thresholds forbidden in orchestration\n\n"
            f"Violations:\n" + "\n".join(f"  • {v}" for v in violations) + "\n\n"
            f"Fix: Service must return semantic status ('quality': 'high'/'low').\n"
            f"Node routes based on status, not numeric threshold.\n"
            f"See: .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md section 4.4"
        )
        pytest.fail(msg)


@pytest.mark.parametrize("node_file", get_graph_node_files())
def test_no_semantic_filtering(node_file: Path):
    """
    Contract Section 3.1: Graph nodes MUST NOT filter by semantic criteria.
    
    Forbidden: [x for x in results if x.confidence > 0.5]
    """
    with open(node_file) as f:
        source = f.read()
    
    violations = []
    
    # Pattern: list comprehension with semantic filtering
    for term in DOMAIN_TERMS:
        pattern = f"\\[.*for.*if.*{term}.*[<>!=]"
        matches = re.finditer(pattern, source, re.IGNORECASE)
        
        for match in matches:
            line_no = source[:match.start()].count('\n') + 1
            line_content = source.split('\n')[line_no - 1].strip()
            
            if line_content.startswith('#'):
                continue
            
            violations.append(f"Line {line_no}: Semantic filtering in list comprehension")
    
    if violations:
        msg = (
            f"\n❌ Contract Violation in {node_file.name}\n"
            f"Section 3.1: Semantic filtering forbidden in orchestration\n\n"
            f"Violations:\n" + "\n".join(f"  • {v}" for v in violations) + "\n\n"
            f"Fix: Service must return pre-filtered results.\n"
            f"See: .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md section 3.1"
        )
        pytest.fail(msg)


@pytest.mark.parametrize("node_file", get_graph_node_files())
def test_no_domain_sorting(node_file: Path):
    """
    Contract Section 3.1: Graph nodes MUST NOT sort by domain criteria.
    
    Forbidden: sorted(results, key=lambda x: x.score)
    """
    with open(node_file) as f:
        source = f.read()
    
    violations = []
    
    for term in DOMAIN_TERMS:
        pattern = f"sorted\\(.*key=lambda.*{term}"
        matches = re.finditer(pattern, source, re.IGNORECASE)
        
        for match in matches:
            line_no = source[:match.start()].count('\n') + 1
            violations.append(f"Line {line_no}: Sorting by domain criterion '{term}'")
    
    if violations:
        msg = (
            f"\n❌ Contract Violation in {node_file.name}\n"
            f"Section 3.1: Domain sorting forbidden in orchestration\n\n"
            f"Violations:\n" + "\n".join(f"  • {v}" for v in violations) + "\n\n"
            f"Fix: Service must return pre-sorted results.\n"
            f"See: .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md section 3.1"
        )
        pytest.fail(msg)


@pytest.mark.parametrize("node_file", get_graph_node_files())
def test_node_is_thin_adapter(node_file: Path):
    """
    Contract Section 2: Graph nodes should be thin adapters (<80 lines).
    
    This is a soft recommendation, not a hard failure.
    """
    with open(node_file) as f:
        lines = f.readlines()
    
    # Count non-empty, non-comment lines
    code_lines = [
        line for line in lines
        if line.strip() and not line.strip().startswith('#')
    ]
    
    if len(code_lines) > 100:
        pytest.skip(
            f"⚠️  {node_file.name} has {len(code_lines)} code lines (target: <80)\n"
            f"Consider refactoring to be a thinner adapter.\n"
            f"See: .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md section 4"
        )


def test_contract_document_exists():
    """Verify the contract document is present."""
    contract_path = Path(".github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md")
    assert contract_path.exists(), (
        "Contract document not found at .github/LANGGRAPH_ORCHESTRATION_CONTRACT_v1.md"
    )


def test_enforcement_script_exists():
    """Verify the enforcement script is present."""
    script_path = Path(".github/scripts/enforce_orchestration_contract.sh")
    assert script_path.exists(), (
        "Enforcement script not found at .github/scripts/enforce_orchestration_contract.sh"
    )
    
    # Check if executable
    assert script_path.stat().st_mode & 0o111, (
        "Enforcement script is not executable. Run: chmod +x .github/scripts/enforce_orchestration_contract.sh"
    )
