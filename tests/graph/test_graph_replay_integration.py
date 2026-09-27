"""Integration tests for Provenance Replay generating a verified SemanticGraph."""

from pathlib import Path

import pytest
from researchforge.application.workflows.literature_trajectory import LiteratureEvidenceWorkflowService
from researchforge.domain.graph import (
    GraphQueryEngine,
    ResearchNodeType,
    ResearchRelationType,
    compute_graph_content_hash,
    validate_graph,
)
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.provenance.replay import ProvenanceReplayEngine


@pytest.mark.asyncio
async def test_provenance_replay_reconstructs_validated_semantic_graph(tmp_path: Path) -> None:
    """Validate that provenance events from a Phase 1 trajectory deterministically rebuild a valid SemanticGraph."""
    db_file = tmp_path / "replay_graph.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    service = LiteratureEvidenceWorkflowService(
        db_manager=db_mgr,
        artifacts_dir=tmp_path / "artifacts",
    )

    await service.execute_literature_trajectory(
        question_text="What is the empirical effect of Parameter X on Response Y?",
        primary_variable="Parameter X",
        target_phenomenon="Response Y",
    )

    with UnitOfWork(db_mgr) as uow:
        assert uow.provenance_repo is not None
        events = uow.provenance_repo.list_all()

    # Replay 1
    reconstructed1 = ProvenanceReplayEngine.replay(events)
    graph1 = reconstructed1.semantic_graph

    # 1. Verify Node Population
    assert graph1.node_count >= 10
    assert len(GraphQueryEngine.find_nodes(graph1, ResearchNodeType.PROJECT)) == 1
    assert len(GraphQueryEngine.find_nodes(graph1, ResearchNodeType.QUESTION)) == 1
    assert len(GraphQueryEngine.find_nodes(graph1, ResearchNodeType.SOURCE)) == 4
    assert len(GraphQueryEngine.find_nodes(graph1, ResearchNodeType.CLAIM)) >= 4
    assert len(GraphQueryEngine.find_nodes(graph1, ResearchNodeType.EVIDENCE)) >= 1
    assert len(GraphQueryEngine.find_nodes(graph1, ResearchNodeType.CONTRADICTION)) >= 1
    assert len(GraphQueryEngine.find_nodes(graph1, ResearchNodeType.RESEARCH_GAP)) >= 1
    assert len(GraphQueryEngine.find_nodes(graph1, ResearchNodeType.HYPOTHESIS)) >= 1

    # 2. Verify Edge Population & Semantic Connections
    assert graph1.edge_count >= 10
    assert len(GraphQueryEngine.find_edges(graph1, ResearchRelationType.ASKS)) >= 1
    assert len(GraphQueryEngine.find_edges(graph1, ResearchRelationType.SUPPORTS)) >= 1
    assert len(GraphQueryEngine.find_edges(graph1, ResearchRelationType.CONTRADICTS)) >= 1
    assert len(GraphQueryEngine.find_edges(graph1, ResearchRelationType.MOTIVATES)) >= 1

    # 3. Contract & Invariant Validation
    validation_res = validate_graph(graph1)
    assert validation_res.is_valid is True
    assert len(validation_res.errors) == 0

    # 4. Deterministic Hash Reproducibility
    reconstructed2 = ProvenanceReplayEngine.replay(events)
    graph2 = reconstructed2.semantic_graph

    hash1 = compute_graph_content_hash(graph1)
    hash2 = compute_graph_content_hash(graph2)
    assert hash1 == hash2
    assert hash1 != ""
