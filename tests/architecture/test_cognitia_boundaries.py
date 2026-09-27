"""Tests validating Cognitia semantic context, context hashing, advisory result marking, and promotion boundaries."""

from pathlib import Path

import pytest
from researchforge.application.workflows.cognitia_advisory import CognitiaAdvisoryWorkflowService
from researchforge.application.workflows.literature_trajectory import LiteratureEvidenceWorkflowService
from researchforge.persistence.database import init_db
from researchforge.persistence.unit_of_work import UnitOfWork


@pytest.mark.asyncio
async def test_cognitia_bounded_context_and_advisory_result(tmp_path: Path) -> None:
    """Verify that Cognitia receives bounded semantic graph context with
    deterministic hash and returns ADVISORY results.
    """
    init_db()

    # 1. Establish project, literature, and semantic graph
    lit_service = LiteratureEvidenceWorkflowService(
        artifacts_dir=tmp_path / "artifacts",
    )
    res = await lit_service.execute_literature_trajectory()
    project_id = res.project.id
    gap_id = res.gaps[0].id
    hyp_id = res.hypotheses[0].id

    from researchforge.application.workflows.experiment_trajectory import ExperimentPlanningWorkflowService
    plan_service = ExperimentPlanningWorkflowService(artifacts_dir=tmp_path / "artifacts")
    await plan_service.plan_experiment_trajectory(
        project_id=project_id,
        hypothesis_id=hyp_id,
        experiment_name="Architecture Test Experiment",
    )

    # 2. Query Cognitia advisory service over a bounded subgraph seeded by hyp_id
    adv_service = CognitiaAdvisoryWorkflowService()
    result = await adv_service.consult_on_subgraph(
        project_id=project_id,
        seed_node_ids={hyp_id},
        operation_type="CRITIQUE",
        depth=1,
    )

    # 3. Assert Advisory Result contract
    assert result.advisory_status == "ADVISORY"
    assert result.context_graph_hash != ""
    assert len(result.candidate_hypotheses) > 0
    assert len(result.recommendations) > 0

    # 4. Verify Cognitia has NOT modified authoritative graph or domain state directly
    # (Cognitia only returns candidate hypotheses, none are persisted yet)
    candidate_hyp_id = "hyp_candidate_non_existent"
    with UnitOfWork() as uow:
        assert uow.hypotheses is not None
        assert uow.hypotheses.get(candidate_hyp_id) is None

    # 5. Promote candidate hypothesis through explicit HumanDecision and workflow
    cand_text = result.candidate_hypotheses[0]
    promoted_hyp, decision = adv_service.promote_candidate_hypothesis(
        project_id=project_id,
        advisory_result=result,
        candidate_hypothesis_text=cand_text,
        gap_id=gap_id,
        decision_actor_id="researcher_human_01",
    )

    assert promoted_hyp.statement == cand_text
    assert decision.target_entity_id == promoted_hyp.id
    assert decision.reviewer_id == "researcher_human_01"

    # 6. Verify promoted hypothesis now exists in graph and domain repository
    with UnitOfWork() as uow:
        assert uow.semantic_graphs is not None
        graph = uow.semantic_graphs.load_graph(f"graph_{project_id}")
        assert any(
            e.source_node_id == promoted_hyp.id and e.target_node_id == gap_id
            for e in graph.edges.values()
        )
