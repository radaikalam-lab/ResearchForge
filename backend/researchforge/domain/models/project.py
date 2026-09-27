"""Research project, question, objective, and context models."""

from typing import Any

from pydantic import Field

from researchforge.domain.base import AggregateRoot, Entity
from researchforge.domain.state_machine import ResearchLifecycleState
from researchforge.domain.value_objects.directional import DirectionalSpecification


class ResearchObjective(Entity):
    """Specific measurable research objective."""

    name: str
    description: str
    target_metric: str | None = None
    target_value: float | None = None


class ResearchConstraint(Entity):
    """Boundary constraint on research exploration."""

    name: str
    description: str
    is_hard: bool = True
    constraint_type: str = "COMPUTATIONAL"  # COMPUTATIONAL, ETHICAL, SCOPE, RESOURCE


class ResearchContext(Entity):
    """Contextual metadata, domain background, and environment state."""

    domain: str
    subdomain: str | None = None
    known_prior_work: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchQuestion(Entity):
    """Primary or secondary scientific research question."""

    project_id: str
    question_text: str
    scope_boundaries: list[str] = Field(default_factory=list)
    key_variables: list[str] = Field(default_factory=list)
    primary_variable: str = ""
    target_phenomenon: str = ""
    parent_question_id: str | None = None
    epistemic_importance: float = Field(default=1.0, ge=0.0, le=1.0)


class ResearchProject(AggregateRoot):
    """Root aggregate container for a computational research lifecycle investigation."""

    title: str
    description: str = ""
    state: ResearchLifecycleState = Field(default=ResearchLifecycleState.DRAFT)
    directional_spec: DirectionalSpecification | None = None
    thread_ids: list[str] = Field(default_factory=list)
    question_ids: list[str] = Field(default_factory=list)
    objective_ids: list[str] = Field(default_factory=list)
    constraint_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    hypothesis_ids: list[str] = Field(default_factory=list)
    experiment_ids: list[str] = Field(default_factory=list)
    conclusion_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)

    def derive_aggregate_state(self, child_thread_states: list[str]) -> ResearchLifecycleState:
        """Derive coarse project-level state from active research threads without conflating sub-states."""
        if not child_thread_states:
            return self.state
        if all(s == "ACCEPTED" for s in child_thread_states):
            return ResearchLifecycleState.CONCLUSION_ACCEPTED
        if any(s in ("UNDER_TEST", "RUNNING") for s in child_thread_states):
            return ResearchLifecycleState.COMPUTATION_RUNNING
        if any(s == "ACCEPTED" for s in child_thread_states) and all(
            s in ("ACCEPTED", "REJECTED", "INCONCLUSIVE", "SUPERSEDED", "INVALIDATED") for s in child_thread_states
        ):
            return ResearchLifecycleState.CONCLUSION_ACCEPTED
        return self.state
