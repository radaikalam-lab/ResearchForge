"""Tests for artifact DAG cascade invalidation and dependent conclusion status (Section 22, 29)."""

from pathlib import Path

from researchforge.artifacts.manager import ArtifactManager
from researchforge.domain.models.artifact import ArtifactType
from researchforge.domain.models.conclusion import Conclusion


def test_artifact_cascade_invalidation_and_conclusion_review(tmp_path: Path) -> None:
    """Proves that mutating upstream data invalidates descendants and marks conclusions for review."""
    manager = ArtifactManager(base_dir=tmp_path)

    # 1. Dataset Artifact
    dataset = manager.register_artifact(
        project_id="proj_inv",
        name="raw_experiment_data.csv",
        artifact_type=ArtifactType.DATASET_PARQUET,
        file_path=str(tmp_path / "data.csv"),
        content_bytes=b"x,y\n0,1\n1,3\n2,5\n3,7",
    )

    # 2. Figure Artifact depending on Dataset
    figure = manager.register_artifact(
        project_id="proj_inv",
        name="response_curve.png",
        artifact_type=ArtifactType.FIGURE_PNG,
        file_path=str(tmp_path / "fig.png"),
        content_bytes=b"png_bytes_fig",
        upstream_artifact_ids=[dataset.id],
    )

    # 3. Report Artifact depending on Figure
    report = manager.register_artifact(
        project_id="proj_inv",
        name="report.json",
        artifact_type=ArtifactType.MANUSCRIPT_JSON,
        file_path=str(tmp_path / "report.json"),
        content_bytes=b"json_report",
        upstream_artifact_ids=[figure.id],
    )

    # 4. Conclusion referencing Report Artifact
    conclusion = Conclusion(
        id="concl_inv",
        project_id="proj_inv",
        statement="Parameter X is verified to scale response Y.",
        human_decision_id="dec_01",
        artifact_ids=[report.id],
        status="VALID",
    )

    assert dataset.status == "VERIFIED"
    assert figure.status == "VERIFIED"
    assert report.status == "VERIFIED"
    assert conclusion.status == "VALID"
    assert manager.evaluate_conclusion_validity(conclusion.artifact_ids) == "VALID"

    # Invalidate root dataset (e.g. data corruption discovered)
    invalidated_ids = manager.invalidate_artifact_and_descendants(dataset.id, reason="Corrupted sensor reading")

    # Verify all artifacts in chain are INVALIDATED
    assert dataset.id in invalidated_ids
    assert figure.id in invalidated_ids
    assert report.id in invalidated_ids

    assert dataset.status == "INVALIDATED"
    assert figure.status == "INVALIDATED"
    assert report.status == "INVALIDATED"

    # Verify conclusion evaluation flags REQUIRES_REVIEW
    updated_conclusion_status = manager.evaluate_conclusion_validity(
        conclusion.artifact_ids, invalidated_ids=invalidated_ids
    )
    assert updated_conclusion_status == "REQUIRES_REVIEW"
