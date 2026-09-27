"""Reproducibility bundle generator and machine-verifiable research manifest."""

import hashlib
import platform
import sys
from enum import StrEnum
from pathlib import Path
from typing import Any

from researchforge.domain.base import canonical_json_dumps, current_iso_timestamp
from researchforge.domain.models.artifact import ResearchArtifact
from researchforge.domain.models.experiment import ExperimentRun
from researchforge.domain.models.project import ResearchProject


class ReproducibilityLevel(StrEnum):
    """Categorization of research trajectory reproducibility."""

    LEVEL_0_PROVENANCE = "LEVEL_0_PROVENANCE"  # Complete audit trail and DAG lineage
    LEVEL_1_COMPUTATIONAL = "LEVEL_1_COMPUTATIONAL"  # Deterministic execution and seed reproducibility
    LEVEL_2_ENVIRONMENT = "LEVEL_2_ENVIRONMENT"  # Pinned OS, Python, and dependency versions
    LEVEL_3_BITWISE = "LEVEL_3_BITWISE"  # Bitwise bit-exact floating-point and container digest matching


class ReproducibilityManifest:
    """Structured research reproducibility manifest."""

    def __init__(
        self,
        project_id: str,
        run_id: str,
        level: ReproducibilityLevel = ReproducibilityLevel.LEVEL_1_COMPUTATIONAL,
        random_seed: int = 42,
        parameter_hash: str = "",
        input_hash: str = "",
        output_hash: str = "",
        provenance_head_hash: str = "",
        checkpoint_hash: str = "",
        artifact_hashes: dict[str, str] | None = None,
        execution_backend: str = "ReferenceExecutionBackend_v1",
        container_image_digest: str | None = None,
    ) -> None:
        self.project_id = project_id
        self.run_id = run_id
        self.level = level
        self.created_at = current_iso_timestamp()
        self.researchforge_version = "0.3.0"
        self.python_version = sys.version.split()[0]
        self.os = platform.system()
        self.architecture = platform.machine()
        self.random_seed = random_seed
        self.parameter_hash = parameter_hash
        self.input_hash = input_hash
        self.output_hash = output_hash
        self.provenance_head_hash = provenance_head_hash
        self.checkpoint_hash = checkpoint_hash
        self.artifact_hashes = artifact_hashes or {}
        self.execution_backend = execution_backend
        self.container_image_digest = container_image_digest

    def to_dict(self) -> dict[str, Any]:
        """Convert manifest to serializable dictionary."""
        return {
            "project_id": self.project_id,
            "run_id": self.run_id,
            "reproducibility_level": self.level.value,
            "created_at": self.created_at,
            "researchforge_version": self.researchforge_version,
            "runtime_environment": {
                "python_version": self.python_version,
                "os": self.os,
                "architecture": self.architecture,
                "execution_backend": self.execution_backend,
                "container_image_digest": self.container_image_digest,
            },
            "cryptographic_hashes": {
                "random_seed": self.random_seed,
                "parameter_hash": self.parameter_hash,
                "input_hash": self.input_hash,
                "output_hash": self.output_hash,
                "provenance_head_hash": self.provenance_head_hash,
                "checkpoint_hash": self.checkpoint_hash,
                "artifact_hashes": self.artifact_hashes,
            },
        }

    def compute_manifest_hash(self) -> str:
        """Compute deterministic SHA-256 hash of the canonical manifest."""
        canonical = canonical_json_dumps(self.to_dict())
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ReproducibilityBundleGenerator:
    """Creates structured, verifiable reproducibility bundles for completed research runs."""

    def __init__(self, base_output_dir: Path | None = None) -> None:
        self.base_output_dir = base_output_dir or Path("artifacts/reproducibility")

    def build_bundle(
        self,
        project: ResearchProject,
        run: ExperimentRun,
        artifacts: list[ResearchArtifact],
        provenance_events_jsonl: str = "",
        checkpoint_hash: str = "",
        level: ReproducibilityLevel = ReproducibilityLevel.LEVEL_1_COMPUTATIONAL,
    ) -> Path:
        """Generate structured directory bundle with manifest.json and component payloads."""
        bundle_dir = self.base_output_dir / f"{project.id}_{run.id}"
        bundle_dir.mkdir(parents=True, exist_ok=True)

        artifact_hashes = {a.name: a.content_sha256 for a in artifacts}
        manifest = ReproducibilityManifest(
            project_id=project.id,
            run_id=run.id,
            level=level,
            random_seed=run.random_seed,
            parameter_hash=run.parameter_hash,
            input_hash=run.input_hash,
            output_hash=run.output_hash,
            checkpoint_hash=checkpoint_hash,
            artifact_hashes=artifact_hashes,
        )

        # 1. Write manifest.json
        manifest_path = bundle_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(canonical_json_dumps(manifest.to_dict()))

        # 2. Write provenance log if present
        if provenance_events_jsonl:
            prov_path = bundle_dir / "provenance.jsonl"
            with open(prov_path, "w", encoding="utf-8") as f:
                f.write(provenance_events_jsonl)

        # 3. Write results snapshot
        results_path = bundle_dir / "results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            f.write(canonical_json_dumps(run.results or (run.result.model_dump(mode="json") if run.result else {})))

        return bundle_dir
