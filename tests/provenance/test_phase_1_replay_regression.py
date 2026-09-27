"""Replay regression test for Phase 1 Literature & Evidence Trajectory."""

from pathlib import Path

import pytest
from researchforge.application.workflows.literature_trajectory import LiteratureEvidenceWorkflowService
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.provenance.replay import ProvenanceReplayEngine


@pytest.mark.asyncio
async def test_phase_1_literature_replay_regression(tmp_path: Path) -> None:
    """Validate that ProvenanceReplayEngine faithfully reconstructs the full Phase 1 entity graph."""
    db_file = tmp_path / "replay_test.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    service = LiteratureEvidenceWorkflowService(
        db_manager=db_mgr,
        artifacts_dir=artifacts_dir,
    )

    res = await service.execute_literature_trajectory(
        question_text="What is the empirical effect of Parameter X on Response Y?",
        primary_variable="Parameter X",
        target_phenomenon="Response Y",
    )

    with UnitOfWork(db_mgr) as uow:
        assert uow.provenance_repo is not None
        events = uow.provenance_repo.list_all()

    # Replay all events
    reconstructed = ProvenanceReplayEngine.replay(events)

    # Assert exact entity matching
    assert reconstructed.replayed_events_count == len(events)
    assert res.project.id in reconstructed.projects
    assert res.question.id in reconstructed.questions
    assert len(reconstructed.sources) >= 4
    assert len(reconstructed.claims) >= 4
    assert len(reconstructed.contradictions) >= 1
    assert len(reconstructed.gaps) >= 1
    assert len(reconstructed.hypotheses) >= 1


@pytest.mark.asyncio
async def test_replay_tamper_detection(tmp_path: Path) -> None:
    """Validate that modifying an event payload in the stream breaks hash verification."""
    db_file = tmp_path / "replay_tamper.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    service = LiteratureEvidenceWorkflowService(
        db_manager=db_mgr,
        artifacts_dir=tmp_path / "artifacts",
    )

    await service.execute_literature_trajectory()

    with UnitOfWork(db_mgr) as uow:
        assert uow.provenance_repo is not None
        events = uow.provenance_repo.list_all()
        assert uow.ledger is not None

        # Verify pristine chain
        is_valid, err = uow.ledger.verify_chain(events)
        assert is_valid is True
        assert err is None

        # Tamper with an event parameter
        tampered_events = [e.model_copy(deep=True) for e in events]
        tampered_events[2].parameters["malicious_param"] = "INJECTED_VALUE"

        is_tampered_valid, tamper_err = uow.ledger.verify_chain(tampered_events)
        assert is_tampered_valid is False
        assert tamper_err is not None
