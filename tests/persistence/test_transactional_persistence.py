"""Tests for transactional database persistence and rollback consistency (Section 24, 37)."""

from pathlib import Path

import pytest
from researchforge.domain.models.project import ResearchProject
from researchforge.domain.state_machine import ResearchLifecycleState
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.provenance.event_types import ProvenanceEventType
from researchforge.provenance.models import ProvenanceActor
from researchforge.provenance.tracker import ProvenanceTracker


def test_transactional_commit_atomicity(tmp_path: Path) -> None:
    """Proves that domain mutation and provenance event commit together atomically."""
    db_file = tmp_path / "test_tx_commit.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    with UnitOfWork(db_mgr) as uow:
        tracker = ProvenanceTracker(uow.ledger)
        project = ResearchProject(
            id="proj_tx_01",
            title="Atomic Transaction Study",
            state=ResearchLifecycleState.DRAFT,
        )
        uow.projects.save(project)

        event = tracker.track(
            actor=ProvenanceActor.HUMAN,
            actor_id="user_tx",
            operation=ProvenanceEventType.PROJECT_CREATED,
            entity_id=project.id,
            entity_type="ResearchProject",
        )
        uow.record_provenance(event)

    # Verify persistence in a new independent session
    with UnitOfWork(db_mgr) as uow:
        retrieved_proj = uow.projects.get("proj_tx_01")
        assert retrieved_proj is not None
        assert retrieved_proj.title == "Atomic Transaction Study"

        events = uow.provenance_repo.list_all()
        assert len(events) == 1
        assert events[0].entity_id == "proj_tx_01"


def test_transactional_rollback_on_failure(tmp_path: Path) -> None:
    """Proves that a failure mid-transaction rolls back both domain state and provenance events."""
    db_file = tmp_path / "test_tx_rollback.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    with pytest.raises(RuntimeError, match="Simulated mid-transaction failure"):
        with UnitOfWork(db_mgr) as uow:
            tracker = ProvenanceTracker(uow.ledger)
            project = ResearchProject(
                id="proj_fail_01",
                title="Doomed Project",
                state=ResearchLifecycleState.DRAFT,
            )
            uow.projects.save(project)

            event = tracker.track(
                actor=ProvenanceActor.HUMAN,
                actor_id="user_tx",
                operation=ProvenanceEventType.PROJECT_CREATED,
                entity_id=project.id,
                entity_type="ResearchProject",
            )
            uow.record_provenance(event)

            # Simulated unhandled crash
            raise RuntimeError("Simulated mid-transaction failure")

    # Verify that nothing was persisted to database
    with UnitOfWork(db_mgr) as uow:
        retrieved_proj = uow.projects.get("proj_fail_01")
        assert retrieved_proj is None

        events = uow.provenance_repo.list_all()
        assert len(events) == 0
