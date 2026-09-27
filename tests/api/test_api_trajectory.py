"""Tests for end-to-end API trajectory endpoints (Section 35)."""

import httpx
import pytest
from researchforge.api.app import app


@pytest.mark.asyncio
async def test_api_full_reference_trajectory() -> None:
    """Execute reference research trajectory via REST API endpoints."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Trajectory execution endpoint
        resp = await client.post("/api/v1/trajectory/execute")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "SUCCESS"
        assert data["project_id"].startswith("proj_")
        assert data["thread_id"].startswith("th_")
        assert data["falsification_status"] == "SUPPORTED"
        assert data["events_count"] >= 10

        # 2. Individual entity API checks
        proj_resp = await client.post(
            "/api/v1/projects",
            json={"title": "API Test Project", "description": "Testing API creation"},
        )
        assert proj_resp.status_code == 200
        proj_id = proj_resp.json()["id"]

        thread_resp = await client.post(
            "/api/v1/threads",
            json={"project_id": proj_id, "title": "API Thread 1"},
        )
        assert thread_resp.status_code == 200
        assert thread_resp.json()["project_id"] == proj_id

        hyp_resp = await client.post(
            "/api/v1/hypotheses",
            json={
                "project_id": proj_id,
                "statement": "Parameter X drives Response Y",
                "falsification_metric": "p_value",
                "falsification_threshold": 0.05,
            },
        )
        assert hyp_resp.status_code == 200
        hyp_id = hyp_resp.json()["id"]

        exp_resp = await client.post(
            "/api/v1/experiments",
            json={
                "project_id": proj_id,
                "hypothesis_id": hyp_id,
                "name": "Exp API Test",
                "parameters": {"x": [0, 1, 2]},
            },
        )
        assert exp_resp.status_code == 200

        # Artifact endpoint
        art_resp = await client.post(
            "/api/v1/artifacts",
            json={
                "project_id": proj_id,
                "name": "test_artifact.json",
                "file_path": "./artifacts/test.json",
                "content": "{}",
            },
        )
        assert art_resp.status_code == 200
        assert art_resp.json()["status"] == "VERIFIED"
