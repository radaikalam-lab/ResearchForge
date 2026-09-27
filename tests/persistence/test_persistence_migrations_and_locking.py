"""Tests for schema migrations, optimistic concurrency locking,
and idempotency conflict handling (Workstreams B, C, D, E).
"""

from pathlib import Path

import pytest
from researchforge.domain.models.project import ResearchProject
from researchforge.domain.models.thread import ResearchThread
from researchforge.domain.state_machine import HypothesisLifecycleState, ResearchLifecycleState
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.exceptions import IdempotencyConflict, OptimisticConcurrencyError
from researchforge.persistence.migrations import MigrationManager
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.provenance.models import ProvenanceEvent, ProvenanceEventType


def test_migration_manager_lifecycle(tmp_path: Path) -> None:
    """Validate MigrationManager applies migrations and records versions."""
    db_file = tmp_path / "migration_test.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")

    migrator = MigrationManager(db_mgr.engine)
    applied = migrator.upgrade()
    assert len(applied) >= 1
    assert migrator.get_current_version() >= 1


def test_optimistic_concurrency_locking(tmp_path: Path) -> None:
    """Validate that saving a thread with a stale version raises OptimisticConcurrencyError."""
    db_file = tmp_path / "locking_test.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    # 1. Create and save initial thread (version 1)
    thread = ResearchThread(
        id="th_lock_01",
        project_id="proj_lock_01",
        title="Concurrent Thread",
        state=HypothesisLifecycleState.DRAFT,
        version=1,
    )
    with UnitOfWork(db_mgr) as uow:
        uow.threads.save(thread)

    # 2. Worker 1 loads thread and updates it (version becomes 2)
    with UnitOfWork(db_mgr) as uow1:
        t1 = uow1.threads.get("th_lock_01")
        assert t1 is not None
        assert t1.version == 1
        t1.title = "Updated by Worker 1"
        uow1.threads.save(t1, check_optimistic_lock=True)

    # 3. Worker 2 attempts to save stale thread with version 1
    stale_thread = ResearchThread(
        id="th_lock_01",
        project_id="proj_lock_01",
        title="Conflicting Update by Worker 2",
        state=HypothesisLifecycleState.DRAFT,
        version=1,  # stale version!
    )
    with pytest.raises(OptimisticConcurrencyError) as exc_info:
        with UnitOfWork(db_mgr) as uow2:
            uow2.threads.save(stale_thread, check_optimistic_lock=True)

    assert "Optimistic concurrency violation" in str(exc_info.value)
    assert exc_info.value.expected_version == 1
    assert exc_info.value.current_version == 2


def test_idempotency_conflict_detection(tmp_path: Path) -> None:
    """Validate that re-using an idempotency key with conflicting parameters raises IdempotencyConflict."""
    db_file = tmp_path / "idempotency_test.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    with UnitOfWork(db_mgr) as uow:
        # Save initial record with request payload
        uow.idempotency.save_record(
            key="idem_key_100",
            operation="create_project",
            entity_id="proj_100",
            response_payload={"project_id": "proj_100", "state": "DRAFT"},
            request_payload={"title": "Project Alpha", "seed": 42},
            actor_id="researcher_1",
        )

    # Identical retry -> returns cached response
    with UnitOfWork(db_mgr) as uow:
        res = uow.idempotency.check_and_validate(
            key="idem_key_100",
            operation="create_project",
            request_payload={"title": "Project Alpha", "seed": 42},
            actor_id="researcher_1",
        )
        assert res is not None
        assert res["entity_id"] == "proj_100"

    # Conflicting operation -> raises IdempotencyConflict
    with pytest.raises(IdempotencyConflict, match="previously registered for operation"):
        with UnitOfWork(db_mgr) as uow:
            uow.idempotency.check_and_validate(
                key="idem_key_100",
                operation="delete_project",
                request_payload={"title": "Project Alpha", "seed": 42},
                actor_id="researcher_1",
            )

    # Conflicting payload parameters -> raises IdempotencyConflict
    with pytest.raises(IdempotencyConflict, match="different request parameters"):
        with UnitOfWork(db_mgr) as uow:
            uow.idempotency.check_and_validate(
                key="idem_key_100",
                operation="create_project",
                request_payload={"title": "Project Beta (DIFFERENT)", "seed": 99},
                actor_id="researcher_1",
            )


def test_atomic_rollback_across_domain_and_provenance(tmp_path: Path) -> None:
    """Validate that exceptions during transaction roll back both domain state and provenance entries."""
    db_file = tmp_path / "rollback_test.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    # Attempt failing transaction
    with pytest.raises(RuntimeError, match="Simulated crash"):
        with UnitOfWork(db_mgr) as uow:
            proj = ResearchProject(id="proj_abort_01", title="Aborted Project", state=ResearchLifecycleState.DRAFT)
            uow.projects.save(proj)
            e = ProvenanceEvent(
                event_id="prov_abort_01",
                event_type=ProvenanceEventType.PROJECT_CREATED,
                entity_id="proj_abort_01",
                entity_type="ResearchProject",
            )
            uow.record_provenance(e)
            raise RuntimeError("Simulated crash before commit")

    # Assert neither domain project nor provenance event remained in database
    with UnitOfWork(db_mgr) as uow:
        assert uow.projects.get("proj_abort_01") is None
        events = uow.provenance_repo.get_for_entity("proj_abort_01")
        assert len(events) == 0
