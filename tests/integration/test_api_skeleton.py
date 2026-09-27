"""Tests for FastAPI skeleton endpoints using httpx AsyncClient."""

import httpx
import pytest
from researchforge.api.app import app


@pytest.fixture
def anyio_backend() -> str:
    """Backend for async tests."""
    return "asyncio"


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    """Verify healthz endpoint."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_project_lifecycle_api_flow() -> None:
    """Verify creating and listing projects via REST API."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Create project
        create_resp = await client.post(
            "/api/v1/projects",
            json={
                "title": "High-Pressure Synthesis Study",
                "description": "Investigating lattice constants",
            },
        )
        assert create_resp.status_code == 200
        proj_data = create_resp.json()
        assert proj_data["state"] == "DRAFT"
        proj_id = proj_data["id"]

        # List projects
        list_resp = await client.get("/api/v1/projects")
        assert list_resp.status_code == 200
        assert any(p["id"] == proj_id for p in list_resp.json())

        # Create question
        q_resp = await client.post(
            "/api/v1/questions",
            json={"project_id": proj_id, "question_text": "Does pressure lower resistance?"},
        )
        assert q_resp.status_code == 200
        assert q_resp.json()["project_id"] == proj_id

        # Transition project
        trans_resp = await client.post(
            f"/api/v1/projects/{proj_id}/transition",
            json={"target_state": "QUESTION_DEFINED"},
        )
        assert trans_resp.status_code == 200
        assert trans_resp.json()["state"] == "QUESTION_DEFINED"
