"""Research thread aggregate root for managing concurrent hypothesis lines."""

from pydantic import Field

from researchforge.domain.base import AggregateRoot
from researchforge.domain.state_machine import HypothesisLifecycleState


class ResearchThread(AggregateRoot):
    """Aggregate root representing one coherent line of scientific investigation within a project."""

    project_id: str
    title: str
    description: str = ""
    state: HypothesisLifecycleState = Field(default=HypothesisLifecycleState.DRAFT)
    hypothesis_id: str | None = None
    active_experiment_id: str | None = None
    active_run_id: str | None = None
    hypothesis_ids: list[str] = Field(default_factory=list)
    experiment_ids: list[str] = Field(default_factory=list)
    run_ids: list[str] = Field(default_factory=list)
    result_ids: list[str] = Field(default_factory=list)
    falsification_ids: list[str] = Field(default_factory=list)
    conclusion_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)

    def is_active(self) -> bool:
        """Check if research thread is actively in progress."""
        return self.state not in {
            HypothesisLifecycleState.ACCEPTED,
            HypothesisLifecycleState.REJECTED,
            HypothesisLifecycleState.SUPERSEDED,
            HypothesisLifecycleState.INVALIDATED,
        }
