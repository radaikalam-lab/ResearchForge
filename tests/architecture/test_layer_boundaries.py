"""Static architecture and boundary enforcement tests verifying strict separation of concerns."""

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


def test_api_layer_does_not_import_persistence_models_or_sqlalchemy() -> None:
    """Ensure API layer never imports physical persistence models, SQLAlchemy, or UnitOfWork directly."""
    api_dir = Path("backend/researchforge/api")
    for py_file in api_dir.rglob("*.py"):
        imports = _get_imports_from_file(py_file)
        for imp in imports:
            assert "persistence.models" not in imp, f"Forbidden import in {py_file}: {imp}"
            assert not imp.startswith("sqlalchemy"), f"Forbidden SQLAlchemy import in {py_file}: {imp}"
            assert "persistence.unit_of_work" not in imp, (
                f"Forbidden direct UnitOfWork import in API layer {py_file}: {imp} — "
                "use an application service instead"
            )


def test_domain_layer_does_not_import_persistence_or_sqlalchemy() -> None:
    """Ensure Domain layer never imports persistence modules or SQLAlchemy."""
    domain_dir = Path("backend/researchforge/domain")
    for py_file in domain_dir.rglob("*.py"):
        imports = _get_imports_from_file(py_file)
        for imp in imports:
            assert "researchforge.persistence" not in imp, f"Forbidden persistence import in {py_file}: {imp}"
            assert not imp.startswith("sqlalchemy"), f"Forbidden SQLAlchemy import in {py_file}: {imp}"


def test_cognitia_layer_does_not_import_persistence_or_execution() -> None:
    """Ensure Cognitia provider adapter never imports persistence or execution subsystems."""
    cognitia_dir = Path("backend/researchforge/providers/cognitia")
    for py_file in cognitia_dir.rglob("*.py"):
        imports = _get_imports_from_file(py_file)
        for imp in imports:
            assert "researchforge.persistence" not in imp, f"Forbidden persistence import in {py_file}: {imp}"
            assert "researchforge.execution" not in imp, f"Forbidden execution import in {py_file}: {imp}"
            assert not imp.startswith("sqlalchemy"), f"Forbidden SQLAlchemy import in {py_file}: {imp}"
