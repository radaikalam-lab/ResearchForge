"""
Static architecture and boundary enforcement tests for Experimental Design Candidate subsystems (Phase 2.4).
"""

import ast
from pathlib import Path


def _get_imports_from_file(file_path: Path) -> list[str]:
    """Parse python AST and return all imported module paths."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def test_design_operators_are_pure_and_isolated() -> None:
    """Ensure design_exploration_operators.py contains zero persistence, DB, or Cognitia imports."""
    operator_file = Path("backend/researchforge/domain/models/design_exploration_operators.py")
    assert operator_file.exists(), f"File {operator_file} not found"

    imports = _get_imports_from_file(operator_file)
    for imp in imports:
        assert "persistence" not in imp, f"Forbidden persistence import in pure operator: {imp}"
        assert "cognitia" not in imp, f"Forbidden cognitia import in pure operator: {imp}"
        assert not imp.startswith("sqlalchemy"), f"Forbidden SQLAlchemy import in pure operator: {imp}"


def test_experimental_design_candidate_model_has_no_persistence() -> None:
    """Ensure experimental_design_candidate.py domain models have zero persistence imports."""
    model_file = Path("backend/researchforge/domain/models/experimental_design_candidate.py")
    assert model_file.exists(), f"File {model_file} not found"

    imports = _get_imports_from_file(model_file)
    for imp in imports:
        assert "persistence" not in imp, f"Forbidden persistence import in domain model: {imp}"
        assert not imp.startswith("sqlalchemy"), f"Forbidden SQLAlchemy import in domain model: {imp}"
