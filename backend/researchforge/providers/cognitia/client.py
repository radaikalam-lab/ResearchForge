"""HTTP Client for communicating with remote or local Cognitia daemon."""

import httpx

from researchforge.providers.cognitia.schemas import (
    CognitiaEvaluationRequest,
    CognitiaEvaluationResponse,
)


class CognitiaClient:
    """Low-level HTTP client for Cognitia REST endpoints."""

    def __init__(self, base_url: str = "http://127.0.0.1:8080", api_key: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async def evaluate(self, request: CognitiaEvaluationRequest) -> CognitiaEvaluationResponse:
        """Call remote Cognitia evaluation endpoint."""
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.post(
                "/api/v1/epistemic/evaluate",
                json=request.model_dump(mode="json"),
                headers=self.headers,
            )
            resp.raise_for_status()
            return CognitiaEvaluationResponse(**resp.json())
