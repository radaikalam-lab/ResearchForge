"""End-to-End Reference Research Trajectory Integration Test (Phase 0.2)."""

import json
from pathlib import Path

import pytest
from researchforge.application.workflows.trajectory import ResearchTrajectoryService
from researchforge.domain.state_machine import HypothesisLifecycleState, ResearchLifecycleState
from researchforge.persistence.database import DatabaseManager


@pytest.mark.asyncio
async def test_end_to_end_reference_trajectory(tmp_path: Path) -> None:
    """Execute complete deterministic reference research trajectory and verify all stages."""
    db_file = tmp_path / "test_research.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    service = ResearchTrajectoryService(db_manager=db_mgr, artifacts_dir=artifacts_dir)
    res = await service.execute_reference_trajectory(
        title="Impact of Parameter X on Response Y under Condition Z",
        seed=42,
        secret_key="test_human_secret_42",
    )

    # 1. Verify Project State
    assert res.project.id.startswith("proj_")
    assert res.project.state == ResearchLifecycleState.PUBLISHABLE_ARTIFACT
    assert len(res.project.question_ids) == 1
    assert len(res.project.hypothesis_ids) == 1
    assert len(res.project.experiment_ids) == 1
    assert len(res.project.artifact_ids) == 1

    # 2. Verify Thread State
    assert res.thread.project_id == res.project.id
    assert res.thread.state == HypothesisLifecycleState.ACCEPTED
    assert res.thread.hypothesis_id == res.hypothesis.id
    assert res.thread.active_experiment_id == res.experiment.id
    assert res.thread.active_run_id == res.run.id

    # 3. Verify Question & Evidence Grounding
    assert res.question.primary_variable == "parameter_x"
    assert res.evidence.project_id == res.project.id
    assert len(res.evidence.fragments) >= 1

    # 4. Verify Gap Analysis
    assert res.gap.project_id == res.project.id
    assert "parameter_x" in res.gap.affected_variables

    # 5. Verify Hypothesis & Falsification Criteria
    assert res.hypothesis.statement != ""
    assert len(res.hypothesis.falsification_criteria) >= 1
    assert res.hypothesis.falsification_criteria[0].metric_name == "p_value"

    # 6. Verify Cognitia Critique (Advisory only)
    assert res.cognitia_critique.tier.value == "TIER_1_CRITIQUE"
    assert res.cognitia_critique.falsifiability_assessment != ""

    # 7. Verify Experiment & Run Results ($Y = 2X + 1$)
    assert res.run.status == "COMPLETED"
    assert res.run.random_seed == 42
    assert res.run.result is not None
    assert res.run.result.metrics.get("slope") == 2.0
    assert res.run.result.metrics.get("p_value") < 0.01

    # 8. Verify Statistical Analysis
    assert res.analysis.id.startswith("stat_")
    assert len(res.analysis.tests) >= 1
    assert res.analysis.tests[0].is_statistically_significant is True

    # 9. Verify Falsification Status (SUPPORTED, unrefuted)
    assert res.falsification.status.value == "SUPPORTED"
    assert len(res.falsification.evidence_refs) >= 2

    # 10. Verify Human Decision & Cryptographic Signature
    assert res.decision.decision.value == "APPROVE"
    assert res.decision.signature is not None
    assert res.decision.verify_signature(secret_key="test_human_secret_42") is True
    assert res.decision.verify_signature(secret_key="wrong_secret_key") is False

    # 11. Verify Scientific Conclusion
    assert res.conclusion.is_validated is True
    assert res.conclusion.human_decision_id == res.decision.id
    assert res.conclusion.status == "VALID"

    # 12. Verify Artifact File & Content Hash
    assert Path(res.artifact.file_path).exists()
    assert res.artifact.status in {"VALID", "VERIFIED"}
    assert len(res.artifact.content_sha256) == 64

    # Verify JSON content matches schema
    with open(res.artifact.file_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["project_id"] == res.project.id
    assert data["traceability"]["question_id"] == res.question.id
    assert data["traceability"]["conclusion_id"] == res.conclusion.id

    # 13. Verify Checkpoint and Provenance Chain
    assert res.checkpoint.event_count > 0
    assert res.checkpoint.event_count <= len(res.events)
    assert res.checkpoint.signature is not None
    assert len(res.events) >= 12
