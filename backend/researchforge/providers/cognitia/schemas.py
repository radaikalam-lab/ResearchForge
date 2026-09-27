"""Schemas for payload exchange with Cognitia Epistemic Plane."""

from typing import Any

from pydantic import BaseModel, Field


class CognitiaEvaluationRequest(BaseModel):
    """Request payload sent to Cognitia reasoning service."""

    target_id: str
    target_type: str
    content: str
    context: dict[str, Any] = Field(default_factory=dict)
    directional_spec: dict[str, Any] | None = None


class CognitiaEvaluationResponse(BaseModel):
    """Response payload received from Cognitia reasoning service."""

    target_id: str
    epistemic_soundness: float = 0.85
    coherence_score: float = 0.90
    identified_assumptions: list[str] = Field(default_factory=list)
    hidden_assumptions: list[str] = Field(default_factory=list)
    vulnerabilities: list[str] = Field(default_factory=list)
    falsifiability_assessment: str = ""
    candidate_paths: list[dict[str, Any]] = Field(default_factory=list)
