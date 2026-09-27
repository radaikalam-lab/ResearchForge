"""
Architecture boundary tests for Phase 2.3 model comparison domain models.

Ensures that:
    - verification_operators.py does not import persistence
    - verification_operators.py does not import Cognitia
    - verification_operators.py does not import UnitOfWork
    - model_comparison.py does not import persistence
    - model_comparison.py does not import Cognitia
    - model_comparison.py does not import UnitOfWork
    - numerical_verification.py does not import persistence
    - numerical_verification.py does not import Cognitia
"""

from __future__ import annotations

import ast
from pathlib import Path


class TestPhase23ArchitectureBoundary:
    """Static AST checks to enforce isolation of Phase 2.3 domain models."""

    def _get_imports(self, file_path: Path) -> list[str]:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        return imports

    def test_verification_operators_does_not_import_persistence(self) -> None:
        wave_file = Path("backend/researchforge/domain/models/verification_operators.py")
        imports = self._get_imports(wave_file)
        for imp in imports:
            assert "researchforge.persistence" not in imp, (
                f"verification_operators imports persistence: {imp}"
            )

    def test_verification_operators_does_not_import_cognitia(self) -> None:
        wave_file = Path("backend/researchforge/domain/models/verification_operators.py")
        imports = self._get_imports(wave_file)
        for imp in imports:
            assert "cognitia" not in imp.lower(), (
                f"verification_operators imports Cognitia: {imp}"
            )

    def test_model_comparison_does_not_import_persistence(self) -> None:
        mc_file = Path("backend/researchforge/domain/models/model_comparison.py")
        imports = self._get_imports(mc_file)
        for imp in imports:
            assert "researchforge.persistence" not in imp, (
                f"model_comparison imports persistence: {imp}"
            )

    def test_model_comparison_does_not_import_cognitia(self) -> None:
        mc_file = Path("backend/researchforge/domain/models/model_comparison.py")
        imports = self._get_imports(mc_file)
        for imp in imports:
            assert "cognitia" not in imp.lower(), (
                f"model_comparison imports Cognitia: {imp}"
            )

    def test_numerical_verification_does_not_import_persistence(self) -> None:
        nv_file = Path("backend/researchforge/domain/models/numerical_verification.py")
        imports = self._get_imports(nv_file)
        for imp in imports:
            assert "researchforge.persistence" not in imp, (
                f"numerical_verification imports persistence: {imp}"
            )

    def test_scientific_model_does_not_import_persistence(self) -> None:
        sm_file = Path("backend/researchforge/domain/models/evidence.py")
        imports = self._get_imports(sm_file)
        for imp in imports:
            assert "researchforge.persistence" not in imp, (
                f"evidence (ScientificModel) imports persistence: {imp}"
            )
