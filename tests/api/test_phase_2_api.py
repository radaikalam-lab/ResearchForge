"""API test suite for Phase 2 Graph and Experiment Planning endpoints."""

from pathlib import Path

import httpx
import pytest
from researchforge.api.app import app
from researchforge.application.workflows.literature_trajectory import LiteratureEvidenceWorkflowService
from researchforge.persistence.database import init_db


@pytest.mark.asyncio
async def test_phase_2_api_graph_and_experiment_endpoints(tmp_path: Path) -> None:
    """Validate graph retrieval, neighbor inspection, and experiment planning via REST API."""
    init_db()

    # Pre-populate project and hypothesis
    lit_service = LiteratureEvidenceWorkflowService(
        artifacts_dir=tmp_path / "artifacts",
    )
    res = await lit_service.execute_literature_trajectory()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Plan Experiment via API
        plan_resp = await client.post(
            "/api/v1/experiments/plan",
            json={
                "project_id": res.project.id,
                "hypothesis_id": res.hypotheses[0].id,
                "experiment_name": "API Experiment 1",
                "sample_count": 30,
            },
        )
        assert plan_resp.status_code == 200
        design_data = plan_resp.json()
        assert design_data["hypothesis_id"] == res.hypotheses[0].id
        assert design_data["name"] == "API Experiment 1 Design"

        # 2. Get Project Semantic Graph
        graph_resp = await client.get(f"/api/v1/graph/{res.project.id}")
        assert graph_resp.status_code == 200
        graph_json = graph_resp.json()
        assert "nodes" in graph_json
        assert "edges" in graph_json

        # 3. Get Node Neighbors
        neigh_resp = await client.get(f"/api/v1/graph/{res.project.id}/neighbors/{res.hypotheses[0].id}")
        assert neigh_resp.status_code == 200
        neigh_json = neigh_resp.json()
        assert "neighbors" in neigh_json
        assert "outgoing_edges" in neigh_json
