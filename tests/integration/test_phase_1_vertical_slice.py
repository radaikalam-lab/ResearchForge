"""End-to-end integration test for Phase 1 Literature & Evidence vertical slice."""

from pathlib import Path

import pytest
from researchforge.application.workflows.literature_trajectory import LiteratureEvidenceWorkflowService
from researchforge.domain.state_machine import ResearchLifecycleState
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork


@pytest.mark.asyncio
async def test_complete_phase_1_literature_vertical_slice(tmp_path: Path) -> None:
    """Execute complete Phase 1 trajectory:
    Question -> Sources -> Evidence -> Claims -> Contradictions -> Gaps -> Hypothesis -> Bundle.
    """
    db_file = tmp_path / "phase1_trajectory.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    service = LiteratureEvidenceWorkflowService(
        db_manager=db_mgr,
        artifacts_dir=artifacts_dir,
    )

    res = await service.execute_literature_trajectory(
        question_text="How does Parameter X influence Response Y across low and high regimes under condition Z?",
        primary_variable="Parameter X",
        target_phenomenon="Response Y",
        idempotency_key="lit_idemp_key_01",
    )

    # 1. Verify Project State Machine
    assert res.project.state == ResearchLifecycleState.HYPOTHESIS_FORMED
    assert res.question.primary_variable == "Parameter X"

    # 2. Verify Ingested Sources
    assert len(res.sources) == 4
    for s in res.sources:
        assert s.raw_content_hash != ""
        assert s.metadata_hash != ""

    # 3. Verify Evidence & Fragments
    assert len(res.evidence_items) >= 4
    assert len(res.fragments) >= 4

    # 4. Verify Claims & Bindings
    assert len(res.claims) >= 4
    assert len(res.bindings) >= 4

    # 5. Verify Contradictions
    assert len(res.contradictions) >= 1
    assert res.contradictions[0].contradiction_type == "DIRECT_OPPOSITION"

    # 6. Verify Gaps & Hypotheses
    assert len(res.gaps) >= 1
    assert len(res.hypotheses) >= 1
    assert len(res.hypotheses[0].falsification_criteria) >= 2

    # 7. Verify Artifact & Reproducibility
    assert res.evidence_bundle_path.exists()
    assert res.evidence_bundle_hash != ""

    # 8. Verify Complete Database Persistence via UnitOfWork
    with UnitOfWork(db_mgr) as uow:
        assert uow.projects.get(res.project.id) is not None
        assert uow.questions.get(res.question.id) is not None
        assert len(uow.sources.list_by_project(res.project.id)) == 4
        assert len(uow.claims.list_by_project(res.project.id)) >= 4
        assert len(uow.contradictions.list_by_project(res.project.id)) >= 1
        assert len(uow.gaps.list_by_project(res.project.id)) >= 1
        assert uow.hypotheses.get(res.hypotheses[0].id) is not None

        # Verify Provenance Ledger Events
        events = uow.provenance_repo.list_all()
        assert len(events) >= 10
        op_names = [e.operation for e in events]
        assert "PROJECT_CREATED" in op_names
        assert "QUESTION_DEFINED" in op_names
        assert "SOURCE_INGESTED" in op_names
        assert "EVIDENCE_EXTRACTED" in op_names
        assert "CLAIM_CREATED" in op_names
        assert "CONTRADICTION_IDENTIFIED" in op_names
        assert "GAP_IDENTIFIED" in op_names
        assert "HYPOTHESIS_GENERATED" in op_names
        assert "ARTIFACT_GENERATED" in op_names
