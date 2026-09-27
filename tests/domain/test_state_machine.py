"""Tests for the 17-state Research Lifecycle State Machine."""

import pytest
from researchforge.domain.models.project import ResearchProject
from researchforge.domain.services.lifecycle import LifecycleService
from researchforge.domain.state_machine import (
    InvalidStateTransitionError,
    ResearchLifecycleState,
)


def test_valid_sequential_state_progression(sample_project: ResearchProject) -> None:
    """Verify correct sequential progression across early lifecycle states."""
    assert sample_project.state == ResearchLifecycleState.DRAFT

    LifecycleService.transition(sample_project, ResearchLifecycleState.QUESTION_DEFINED)
    assert sample_project.state == ResearchLifecycleState.QUESTION_DEFINED

    LifecycleService.transition(sample_project, ResearchLifecycleState.EVIDENCE_COLLECTION)
    assert sample_project.state == ResearchLifecycleState.EVIDENCE_COLLECTION

    LifecycleService.transition(sample_project, ResearchLifecycleState.EVIDENCE_STRUCTURED)
    assert sample_project.state == ResearchLifecycleState.EVIDENCE_STRUCTURED


def test_invalid_bypass_transition_fails(sample_project: ResearchProject) -> None:
    """Invariant: Silent bypass of intermediate validation steps is prohibited."""
    assert sample_project.state == ResearchLifecycleState.DRAFT

    # Attempting to jump directly from DRAFT to EXPERIMENT_READY must raise error
    with pytest.raises(InvalidStateTransitionError):
        LifecycleService.transition(sample_project, ResearchLifecycleState.EXPERIMENT_READY)


def test_transition_to_conclusion_accepted_requires_approval_and_evidence(
    sample_project: ResearchProject,
) -> None:
    """Invariant: Advancing to CONCLUSION_ACCEPTED requires explicit human review and evidence."""
    sample_project.state = ResearchLifecycleState.HUMAN_REVIEW

    # Case 1: No approval, no evidence
    with pytest.raises(InvalidStateTransitionError):
        LifecycleService.transition(
            sample_project,
            ResearchLifecycleState.CONCLUSION_ACCEPTED,
            has_human_approval=False,
            has_evidence=False,
        )

    # Case 2: Approval without evidence
    with pytest.raises(InvalidStateTransitionError):
        LifecycleService.transition(
            sample_project,
            ResearchLifecycleState.CONCLUSION_ACCEPTED,
            has_human_approval=True,
            has_evidence=False,
        )

    # Case 3: Both valid
    LifecycleService.transition(
        sample_project,
        ResearchLifecycleState.CONCLUSION_ACCEPTED,
        has_human_approval=True,
        has_evidence=True,
    )
    assert sample_project.state == ResearchLifecycleState.CONCLUSION_ACCEPTED
