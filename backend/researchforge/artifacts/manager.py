"""Artifact management, checksum calculation, dependency DAG, and cascade invalidation (Section 22)."""

import hashlib
import uuid
from enum import StrEnum
from pathlib import Path

from researchforge.domain.models.artifact import ArtifactType, ResearchArtifact
from researchforge.provenance.ledger import ProvenanceLedger
from researchforge.provenance.models import ProvenanceActor, ProvenanceOperation
from researchforge.provenance.tracker import ProvenanceTracker


class ReproducibilityLevel(StrEnum):
    """Reproducibility fidelity levels (Section 21)."""

    BITWISE_REPRODUCIBLE = "BITWISE_REPRODUCIBLE"
    NUMERICALLY_REPRODUCIBLE = "NUMERICALLY_REPRODUCIBLE"
    SCIENTIFICALLY_REPRODUCIBLE = "SCIENTIFICALLY_REPRODUCIBLE"


class ArtifactManager:
    """Manages content-addressed artifacts, dependency DAGs, and cascade invalidation."""

    def __init__(
        self,
        base_dir: Path | None = None,
        ledger: ProvenanceLedger | None = None,
    ) -> None:
        self.base_dir = base_dir or Path("./artifacts")
        self.ledger = ledger
        self.tracker = ProvenanceTracker(ledger) if ledger else None
        self._artifacts: dict[str, ResearchArtifact] = {}
        self._dependency_dag: dict[str, list[str]] = {}  # artifact_id -> list of upstream artifact/dataset IDs

    def compute_file_sha256(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file on disk."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def register_artifact(
        self,
        project_id: str,
        name: str,
        artifact_type: ArtifactType,
        file_path: str,
        content_bytes: bytes | None = None,
        upstream_dataset_hashes: list[str] | None = None,
        upstream_artifact_ids: list[str] | None = None,
        upstream_code_hash: str | None = None,
        reproducibility_level: ReproducibilityLevel = ReproducibilityLevel.NUMERICALLY_REPRODUCIBLE,
    ) -> ResearchArtifact:
        """Register or write a reproducible artifact and record content hash."""
        target_path = Path(file_path)
        if content_bytes is not None:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(content_bytes)

        content_sha256 = (
            hashlib.sha256(content_bytes).hexdigest()
            if content_bytes is not None
            else (self.compute_file_sha256(target_path) if target_path.exists() else "")
        )

        artifact_id = f"art_{uuid.uuid4().hex[:12]}"
        artifact = ResearchArtifact(
            id=artifact_id,
            project_id=project_id,
            name=name,
            artifact_type=artifact_type,
            file_path=str(target_path),
            content_sha256=content_sha256,
            upstream_dataset_hashes=upstream_dataset_hashes or [],
            upstream_artifact_ids=upstream_artifact_ids or [],
            upstream_code_hash=upstream_code_hash,
            metadata={"reproducibility_level": reproducibility_level.value},
            status="VERIFIED",
        )
        self._artifacts[artifact_id] = artifact
        self._dependency_dag[artifact_id] = upstream_artifact_ids or []

        if self.tracker:
            self.tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id="artifact_manager",
                operation=ProvenanceOperation.ARTIFACT_GENERATED,
                entity_id=artifact_id,
                entity_type="ResearchArtifact",
                input_refs=upstream_artifact_ids or [],
                output_refs=[artifact_id],
                parameters={"content_sha256": content_sha256, "name": name},
            )

        return artifact

    def invalidate_artifact_and_descendants(
        self,
        target_id: str,
        reason: str = "Upstream mutation",
    ) -> list[str]:
        """Cascade invalidation: mark target and all downstream dependent artifacts as INVALIDATED (Section 22)."""
        invalidated_ids: list[str] = []

        def _invalidate_recursive(curr_id: str) -> None:
            if curr_id in self._artifacts:
                art = self._artifacts[curr_id]
                if art.status != "INVALIDATED":
                    art.status = "INVALIDATED"
                    invalidated_ids.append(curr_id)
                    if self.tracker:
                        self.tracker.track(
                            actor=ProvenanceActor.RESEARCHFORGE,
                            actor_id="artifact_manager",
                            operation=ProvenanceOperation.ARTIFACT_INVALIDATED,
                            entity_id=curr_id,
                            entity_type="ResearchArtifact",
                            parameters={"reason": reason},
                        )

            # Find all artifacts that depend on curr_id
            for child_id, upstreams in self._dependency_dag.items():
                if curr_id in upstreams:
                    _invalidate_recursive(child_id)

        _invalidate_recursive(target_id)
        return invalidated_ids

    def is_artifact_valid_for_datasets(
        self,
        artifact: ResearchArtifact,
        current_dataset_hashes: list[str],
    ) -> bool:
        """Verify that upstream dataset hashes match the artifact's recorded dependencies."""
        if artifact.status == "INVALIDATED":
            return False
        return set(artifact.upstream_dataset_hashes) == set(current_dataset_hashes)

    def get_artifact(self, artifact_id: str) -> ResearchArtifact | None:
        """Retrieve registered artifact by ID."""
        return self._artifacts.get(artifact_id)

    def evaluate_conclusion_validity(
        self,
        conclusion_artifact_ids: list[str],
        invalidated_ids: list[str] | None = None,
    ) -> str:
        """Return 'REQUIRES_REVIEW' if any dependent artifact is invalidated, else 'VALID'."""
        inv_set = set(invalidated_ids or [])
        for art_id in conclusion_artifact_ids:
            if art_id in inv_set:
                return "REQUIRES_REVIEW"
            art = self.get_artifact(art_id)
            if art and art.status == "INVALIDATED":
                return "REQUIRES_REVIEW"
        return "VALID"
