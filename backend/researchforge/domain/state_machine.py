"""Formal hierarchical state machines, transition engine, and authority guards."""

from collections.abc import Callable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from researchforge.domain.value_objects.epistemic import EpistemicTier


# ------------------------------------------------------------------------------
# 1. Project-Level Aggregate Lifecycle
# ------------------------------------------------------------------------------
class ResearchLifecycleState(StrEnum):
    """The 17 sequential and branching states of the computational research program."""

    DRAFT = "DRAFT"
    QUESTION_DEFINED = "QUESTION_DEFINED"
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
    EVIDENCE_STRUCTURED = "EVIDENCE_STRUCTURED"
    GAP_ANALYSIS = "GAP_ANALYSIS"
    HYPOTHESIS_FORMED = "HYPOTHESIS_FORMED"
    HYPOTHESIS_CRITIQUE = "HYPOTHESIS_CRITIQUE"
    EXPERIMENT_DESIGNED = "EXPERIMENT_DESIGNED"
    EXPERIMENT_READY = "EXPERIMENT_READY"
    COMPUTATION_RUNNING = "COMPUTATION_RUNNING"
    RESULTS_AVAILABLE = "RESULTS_AVAILABLE"
    FALSIFICATION = "FALSIFICATION"
    EVIDENCE_EVALUATION = "EVIDENCE_EVALUATION"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    CONCLUSION_ACCEPTED = "CONCLUSION_ACCEPTED"
    ARTIFACT_GENERATION = "ARTIFACT_GENERATION"
    PUBLISHABLE_ARTIFACT = "PUBLISHABLE_ARTIFACT"


# Backward compatibility alias
ProjectLifecycleState = ResearchLifecycleState


# ------------------------------------------------------------------------------
# 2. Research Thread / Hypothesis Lifecycle (Section 4.2)
# ------------------------------------------------------------------------------
class HypothesisLifecycleState(StrEnum):
    """Lifecycle of an individual scientific hypothesis or research thread."""

    DRAFT = "DRAFT"
    FORMED = "FORMED"
    CRITIQUE_PENDING = "CRITIQUE_PENDING"
    CRITIQUED = "CRITIQUED"
    EXPERIMENT_DESIGN_PENDING = "EXPERIMENT_DESIGN_PENDING"
    EXPERIMENT_READY = "EXPERIMENT_READY"
    UNDER_TEST = "UNDER_TEST"
    EVIDENCE_AVAILABLE = "EVIDENCE_AVAILABLE"
    FALSIFICATION_PENDING = "FALSIFICATION_PENDING"
    EVALUATION_PENDING = "EVALUATION_PENDING"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    SUPERSEDED = "SUPERSEDED"
    INVALIDATED = "INVALIDATED"


# ------------------------------------------------------------------------------
# 3. Experiment Lifecycle (Section 4.3)
# ------------------------------------------------------------------------------
class ExperimentLifecycleState(StrEnum):
    """Lifecycle of a computational or numerical experiment."""

    DRAFT = "DRAFT"
    DESIGNED = "DESIGNED"
    VALIDATED = "VALIDATED"
    READY = "READY"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    INVALIDATED = "INVALIDATED"


# ------------------------------------------------------------------------------
# 4. Run Lifecycle (Section 4.4)
# ------------------------------------------------------------------------------
class RunLifecycleState(StrEnum):
    """Lifecycle of an individual computational execution instance."""

    CREATED = "CREATED"
    APPROVED = "APPROVED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    INVALIDATED = "INVALIDATED"


# ------------------------------------------------------------------------------
# 5. Artifact Lifecycle (Section 4.5)
# ------------------------------------------------------------------------------
class ArtifactLifecycleState(StrEnum):
    """Lifecycle of reproducible manuscripts, figures, and dataset bundles."""

    DRAFT = "DRAFT"
    BUILDING = "BUILDING"
    VERIFIED = "VERIFIED"
    PUBLISHED = "PUBLISHED"
    INVALIDATED = "INVALIDATED"
    SUPERSEDED = "SUPERSEDED"


# ------------------------------------------------------------------------------
# 6. Typed Transition Errors (Section 6)
# ------------------------------------------------------------------------------
class StateMachineError(Exception):
    """Base error for all state machine and transition violations."""


class InvalidStateTransitionError(StateMachineError):
    """Raised when attempting an unauthorized or invalid state transition."""

    def __init__(
        self,
        current_state: Any,
        target_state: Any,
        reason: str = "",
    ) -> None:
        cur_str = getattr(current_state, "value", current_state)
        tgt_str = getattr(target_state, "value", target_state)
        msg = f"Cannot transition from {cur_str} to {tgt_str}."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(msg)
        self.current_state = current_state
        self.target_state = target_state
        self.reason = reason


# Alias
InvalidTransitionError = InvalidStateTransitionError


class AuthorityViolationError(StateMachineError):
    """Raised when the acting tier lacks authority for a state transition."""


class MissingArtifactError(StateMachineError):
    """Raised when required prerequisites or evidence artifacts are missing."""


class GuardViolationError(StateMachineError):
    """Raised when a formal transition guard condition evaluates to False."""


class InvalidatedDependencyError(StateMachineError):
    """Raised when a transition depends on an upstream entity that has been invalidated."""


# ------------------------------------------------------------------------------
# 7. Formal Transition Model & Transition Engine
# ------------------------------------------------------------------------------
class Transition(BaseModel):
    """Formal specification of a lifecycle state transition."""

    source_state: str
    target_state: str
    trigger: str
    required_actor_tier: EpistemicTier = EpistemicTier.TIER_2_COMPUTATION
    guard_description: str = ""
    required_artifacts: list[str] = Field(default_factory=list)
    provenance_event_type: str = "STATE_TRANSITIONED"


class TransitionEngine:
    """Executable engine for evaluating, guarding, and executing lifecycle transitions."""

    def __init__(self) -> None:
        self._transitions: dict[tuple[str, str], Transition] = {}
        self._guards: dict[tuple[str, str], Callable[..., bool]] = {}

    def register_transition(
        self,
        transition: Transition,
        guard_fn: Callable[..., bool] | None = None,
    ) -> None:
        """Register a valid state transition rule and optional executable guard."""
        key = (transition.source_state, transition.target_state)
        self._transitions[key] = transition
        if guard_fn:
            self._guards[key] = guard_fn

    def can_transition(
        self,
        current_state: str,
        target_state: str,
        actor_tier: EpistemicTier = EpistemicTier.TIER_2_COMPUTATION,
        context: dict[str, Any] | None = None,
    ) -> tuple[bool, str | None]:
        """Check if transition is allowable without mutating state."""
        key = (current_state, target_state)
        if key not in self._transitions:
            return False, f"Transition from {current_state} to {target_state} is not registered."

        spec = self._transitions[key]
        # Authority tier hierarchy check (higher numerical index = higher authority)
        tier_order = {
            EpistemicTier.TIER_0_PROPOSAL: 0,
            EpistemicTier.TIER_1_CRITIQUE: 1,
            EpistemicTier.TIER_2_COMPUTATION: 2,
            EpistemicTier.TIER_3_HUMAN_AUTHORITY: 3,
        }
        if tier_order[actor_tier] < tier_order[spec.required_actor_tier]:
            return False, (f"Requires {spec.required_actor_tier.value} authority. Acting tier: {actor_tier.value}.")

        # Execute guard if registered
        if key in self._guards and context is not None:
            guard_passed = self._guards[key](**context)
            if not guard_passed:
                return False, f"Guard condition failed: {spec.guard_description}"

        return True, None

    def execute_transition(
        self,
        current_state: str,
        target_state: str,
        actor_tier: EpistemicTier = EpistemicTier.TIER_2_COMPUTATION,
        available_artifacts: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Execute and validate a transition, raising typed errors on violation."""
        key = (current_state, target_state)
        if key not in self._transitions:
            raise InvalidTransitionError(current_state, target_state, "Not a valid transition path.")

        spec = self._transitions[key]

        # Tier authority check
        tier_order = {
            EpistemicTier.TIER_0_PROPOSAL: 0,
            EpistemicTier.TIER_1_CRITIQUE: 1,
            EpistemicTier.TIER_2_COMPUTATION: 2,
            EpistemicTier.TIER_3_HUMAN_AUTHORITY: 3,
        }
        if tier_order[actor_tier] < tier_order[spec.required_actor_tier]:
            raise AuthorityViolationError(
                f"Transition to {target_state} requires {spec.required_actor_tier.value}. Provided: {actor_tier.value}."
            )

        # Check required artifacts
        if spec.required_artifacts:
            available = set(available_artifacts or [])
            missing = set(spec.required_artifacts) - available
            if missing:
                raise MissingArtifactError(
                    f"Transition to {target_state} lacks required artifacts: {', '.join(missing)}."
                )

        # Check guard
        if key in self._guards and context is not None:
            guard_ok = self._guards[key](**context)
            if not guard_ok:
                raise GuardViolationError(f"Guard condition failed: {spec.guard_description}")

        return target_state


# ------------------------------------------------------------------------------
# 8. Project-level Legacy Transition Topology & Validator
# ------------------------------------------------------------------------------
VALID_TRANSITIONS: dict[ResearchLifecycleState, set[ResearchLifecycleState]] = {
    ResearchLifecycleState.DRAFT: {
        ResearchLifecycleState.QUESTION_DEFINED,
    },
    ResearchLifecycleState.QUESTION_DEFINED: {
        ResearchLifecycleState.EVIDENCE_COLLECTION,
        ResearchLifecycleState.DRAFT,
    },
    ResearchLifecycleState.EVIDENCE_COLLECTION: {
        ResearchLifecycleState.EVIDENCE_STRUCTURED,
        ResearchLifecycleState.QUESTION_DEFINED,
    },
    ResearchLifecycleState.EVIDENCE_STRUCTURED: {
        ResearchLifecycleState.GAP_ANALYSIS,
        ResearchLifecycleState.EVIDENCE_COLLECTION,
    },
    ResearchLifecycleState.GAP_ANALYSIS: {
        ResearchLifecycleState.HYPOTHESIS_FORMED,
        ResearchLifecycleState.EVIDENCE_COLLECTION,
    },
    ResearchLifecycleState.HYPOTHESIS_FORMED: {
        ResearchLifecycleState.HYPOTHESIS_CRITIQUE,
        ResearchLifecycleState.GAP_ANALYSIS,
    },
    ResearchLifecycleState.HYPOTHESIS_CRITIQUE: {
        ResearchLifecycleState.EXPERIMENT_DESIGNED,
        ResearchLifecycleState.HYPOTHESIS_FORMED,
    },
    ResearchLifecycleState.EXPERIMENT_DESIGNED: {
        ResearchLifecycleState.EXPERIMENT_READY,
        ResearchLifecycleState.HYPOTHESIS_CRITIQUE,
    },
    ResearchLifecycleState.EXPERIMENT_READY: {
        ResearchLifecycleState.COMPUTATION_RUNNING,
        ResearchLifecycleState.EXPERIMENT_DESIGNED,
    },
    ResearchLifecycleState.COMPUTATION_RUNNING: {
        ResearchLifecycleState.RESULTS_AVAILABLE,
        ResearchLifecycleState.EXPERIMENT_READY,
    },
    ResearchLifecycleState.RESULTS_AVAILABLE: {
        ResearchLifecycleState.FALSIFICATION,
        ResearchLifecycleState.COMPUTATION_RUNNING,
    },
    ResearchLifecycleState.FALSIFICATION: {
        ResearchLifecycleState.EVIDENCE_EVALUATION,
        ResearchLifecycleState.EXPERIMENT_DESIGNED,
    },
    ResearchLifecycleState.EVIDENCE_EVALUATION: {
        ResearchLifecycleState.HUMAN_REVIEW,
        ResearchLifecycleState.HYPOTHESIS_FORMED,
    },
    ResearchLifecycleState.HUMAN_REVIEW: {
        ResearchLifecycleState.CONCLUSION_ACCEPTED,
        ResearchLifecycleState.HYPOTHESIS_CRITIQUE,
        ResearchLifecycleState.EXPERIMENT_DESIGNED,
    },
    ResearchLifecycleState.CONCLUSION_ACCEPTED: {
        ResearchLifecycleState.ARTIFACT_GENERATION,
        ResearchLifecycleState.HUMAN_REVIEW,
    },
    ResearchLifecycleState.ARTIFACT_GENERATION: {
        ResearchLifecycleState.PUBLISHABLE_ARTIFACT,
        ResearchLifecycleState.CONCLUSION_ACCEPTED,
    },
    ResearchLifecycleState.PUBLISHABLE_ARTIFACT: {
        ResearchLifecycleState.ARTIFACT_GENERATION,
    },
}


def validate_transition(
    current: ResearchLifecycleState,
    target: ResearchLifecycleState,
    has_human_approval: bool = False,
    has_evidence: bool = False,
) -> None:
    """Validate project-level lifecycle transition according to state invariants."""
    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStateTransitionError(current, target, "Transition not allowed by state machine topology.")

    if target == ResearchLifecycleState.CONCLUSION_ACCEPTED:
        if not has_human_approval:
            raise InvalidStateTransitionError(
                current, target, "Advancing to CONCLUSION_ACCEPTED requires explicit human approval."
            )
        if not has_evidence:
            raise InvalidStateTransitionError(
                current, target, "Advancing to CONCLUSION_ACCEPTED requires verified empirical/computational evidence."
            )
