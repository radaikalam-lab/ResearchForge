"""Directional Programming constructs aligned with Cognitia."""

from typing import Any

from pydantic import BaseModel, Field


class ResearchState(BaseModel):
    """Specification of a research state."""

    domain: str = Field(description="Scientific domain or subfield")
    known_evidence_summary: str = Field(default="", description="Summary of established evidence")
    parameters: dict[str, Any] = Field(default_factory=dict, description="State parameters")


class TargetResearchState(BaseModel):
    """Target scientific state to establish."""

    goals: list[str] = Field(default_factory=list, description="Target scientific claims or phenomena to establish")
    required_confidence: float = Field(default=0.95, ge=0.0, le=1.0)


class DirectionalConstraint(BaseModel):
    """Execution, ethical, or computational constraint."""

    name: str
    description: str
    is_hard_constraint: bool = True


class DirectionalSpecification(BaseModel):
    """Directional research specification contract."""

    current_state: ResearchState
    target_state: TargetResearchState
    objectives: list[str] = Field(default_factory=list)
    constraints: list[DirectionalConstraint] = Field(default_factory=list)
    available_capabilities: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    uncertainty_tolerance: float = Field(default=0.05, ge=0.0, le=1.0)


class CandidatePath(BaseModel):
    """Proposed path toward the target research state."""

    path_id: str
    description: str
    steps: list[str]
    estimated_cost_hours: float = 0.0
    risk_profile: str = "LOW"
    rationale: str = ""
    is_authoritative_plan: bool = False  # NEVER authoritative by default
