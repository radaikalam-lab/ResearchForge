"""Tests validating API layer adherence to application services, graph boundaries, and DTO projections."""

from pathlib import Path

import httpx
import pytest
from researchforge.api.app import app
from researchforge.application.workflows.literature_trajectory import LiteratureEvidenceWorkflowService
from researchforge.persistence.database import init_db


@pytest.mark.asyncio
async def test_api_graph_and_cognitia_endpoints(tmp_path: Path) -> None:
    """Verify graph query, path search, cognitia advisory, and hypothesis promotion endpoints."""
    init_db()

    lit_service = LiteratureEvidenceWorkflowService(
        artifacts_dir=tmp_path / "artifacts",
    )
    res = await lit_service.execute_literature_trajectory()
    project_id = res.project.id
    hyp_id = res.hypotheses[0].id

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 0. Plan Experiment to create graph
        plan_resp = await client.post(
            "/api/v1/experiments/plan",
            json={
                "project_id": project_id,
                "hypothesis_id": hyp_id,
                "experiment_name": "API Bound Experiment",
                "sample_count": 25,
            },
        )
        assert plan_resp.status_code == 200
        design_data = plan_resp.json()
        design_id = design_data["id"]
        ps_id = design_data["parameter_space"]["id"]

        # 1. Graph inspection
        resp_graph = await client.get(f"/api/v1/graph/{project_id}")
        assert resp_graph.status_code == 200
        graph_data = resp_graph.json()
        assert graph_data["schema_version"] == "0.4.0"
        assert len(graph_data["nodes"]) > 0

        # 2. Neighbors query
        resp_neigh = await client.get(f"/api/v1/graph/{project_id}/neighbors/{hyp_id}")
        assert resp_neigh.status_code == 200
        neigh_data = resp_neigh.json()
        assert neigh_data["node_id"] == hyp_id

        # 3. Path query
        resp_path = await client.get(
            f"/api/v1/graph/{project_id}/path",
            params={"source_node_id": design_id, "target_node_id": ps_id},
        )
        assert resp_path.status_code == 200
        path_data = resp_path.json()
        assert path_data["project_id"] == project_id
        # Directed path from Design to ParameterSpace exists
        assert path_data["path"] is not None

        # 4. Cognitia Advisory Consult
        resp_cog = await client.post(
            "/api/v1/cognitia/consult",
            json={
                "project_id": project_id,
                "seed_node_ids": [hyp_id],
                "operation_type": "CRITIQUE",
                "depth": 1,
            },
        )
        assert resp_cog.status_code == 200
        cog_data = resp_cog.json()
        assert cog_data["advisory_status"] == "ADVISORY"
        assert len(cog_data["candidate_hypotheses"]) > 0

        # 5. Cognitia Hypothesis Promotion
        cand_text = cog_data["candidate_hypotheses"][0]
        resp_promote = await client.post(
            "/api/v1/cognitia/promote-hypothesis",
            json={
                "project_id": project_id,
                "advisory_result_id": cog_data["result_id"],
                "candidate_hypothesis_text": cand_text,
                "gap_id": res.gaps[0].id,
                "actor_id": "human_tester",
            },
        )
        assert resp_promote.status_code == 200
        promote_data = resp_promote.json()
        assert promote_data["hypothesis"]["statement"] == cand_text
        assert promote_data["decision"]["reviewer_id"] == "human_tester"
