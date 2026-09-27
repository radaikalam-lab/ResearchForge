"""Tests for idempotency deduplication and concurrent research threads (Section 30, 31)."""

from pathlib import Path

from researchforge.domain.models.project import ResearchProject
from researchforge.domain.models.thread import ResearchThread
from researchforge.domain.state_machine import HypothesisLifecycleState, ResearchLifecycleState
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork


def test_idempotent_operation_deduplication(tmp_path: Path) -> None:
    """Proves that repeated commands with identical idempotency keys do not duplicate entities."""
    db_file = tmp_path / "test_idempotency.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    idempotency_key = "idemp_create_proj_42"

    with UnitOfWork(db_mgr) as uow:
        existing = uow.idempotency.get_record(idempotency_key)
        assert existing is None

        # First execution
        project = ResearchProject(
            id="proj_idemp_01",
            title="Idempotent Project",
            state=ResearchLifecycleState.DRAFT,
        )
        uow.projects.save(project)
        uow.idempotency.save_record(
            key=idempotency_key,
            operation="create_project",
            entity_id=project.id,
            response_payload={"project_id": project.id, "title": project.title},
        )

    # Second execution with same key
    with UnitOfWork(db_mgr) as uow:
        existing = uow.idempotency.get_record(idempotency_key)
        assert existing is not None
        assert existing["entity_id"] == "proj_idemp_01"
        assert existing["operation"] == "create_project"

        # No duplicate project created
        all_projs = uow.projects.list_all()
        assert len(all_projs) == 1


def test_concurrent_research_threads_isolation(tmp_path: Path) -> None:
    """Proves that multiple research threads under one project advance independently."""
    db_file = tmp_path / "test_concurrency.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    with UnitOfWork(db_mgr) as uow:
        project = ResearchProject(
            id="proj_concurrent",
            title="Multi-thread Concurrent Investigation",
            state=ResearchLifecycleState.HYPOTHESIS_FORMED,
        )
        uow.projects.save(project)

        thread_a = ResearchThread(
            id="th_a",
            project_id=project.id,
            title="Thread A: Regime X in [0, 3]",
            state=HypothesisLifecycleState.UNDER_TEST,
        )
        thread_b = ResearchThread(
            id="th_b",
            project_id=project.id,
            title="Thread B: Regime X in [4, 7]",
            state=HypothesisLifecycleState.DRAFT,
        )
        uow.threads.save(thread_a)
        uow.threads.save(thread_b)

    # Advance Thread A to ACCEPTED while Thread B is REJECTED
    with UnitOfWork(db_mgr) as uow:
        t_a = uow.threads.get("th_a")
        t_b = uow.threads.get("th_b")
        assert t_a is not None and t_b is not None

        t_a.state = HypothesisLifecycleState.ACCEPTED
        t_b.state = HypothesisLifecycleState.REJECTED

        uow.threads.save(t_a)
        uow.threads.save(t_b)

    # Verify independent states persisted without cross-contamination
    with UnitOfWork(db_mgr) as uow:
        threads = uow.threads.list_for_project("proj_concurrent")
        states = {t.id: t.state for t in threads}
        assert states["th_a"] == HypothesisLifecycleState.ACCEPTED
        assert states["th_b"] == HypothesisLifecycleState.REJECTED

        proj = uow.projects.get("proj_concurrent")
        assert proj is not None
        # Aggregate project state recognizes completion / accepted findings
        derived_state = proj.derive_aggregate_state([t.state.value for t in threads])
        assert derived_state == ResearchLifecycleState.CONCLUSION_ACCEPTED
