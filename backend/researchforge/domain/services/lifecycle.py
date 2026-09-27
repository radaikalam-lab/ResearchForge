"""Lifecycle management and transition orchestration services."""

from researchforge.domain.models.project import ResearchProject
from researchforge.domain.state_machine import ResearchLifecycleState, validate_transition


class LifecycleService:
    """Orchestrates verified state transitions on ResearchProjects."""

    @staticmethod
    def transition(
        project: ResearchProject,
        target_state: ResearchLifecycleState,
        has_human_approval: bool = False,
        has_evidence: bool = False,
    ) -> ResearchProject:
        """Advance or step back a research project state with strict invariant validation."""
        validate_transition(
            current=project.state,
            target=target_state,
            has_human_approval=has_human_approval,
            has_evidence=has_evidence,
        )
        project.state = target_state
        return project
