"""
Experimental Design Candidate and Design Evaluation Domain Models (Phase 2.4).

Provides typed representations for:
    - DesignObjective: Controlled vocabulary of experimental goals
    - DesignCandidateStatus: Lifecycle state of candidate designs
    - ResourceRequirements: Domain-neutral resource bounds
    - ObservableTarget: Explicit target observables for model discrimination
    - DiscriminationMetric: Formally defined discrimination metric
    - ExperimentalDesignCandidate: Non-authoritative candidate experiment design
    - CandidateDesignEvaluation: Multi-objective evaluation of a candidate design
    - ParetoCandidateSet: Non-dominated trade-off set across multiple objectives
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field, model_validator

from researchforge.domain.base import DomainModel, ValueObject


class DesignObjective(StrEnum):
    """Explicit scientific objective for experimental design."""

    MODEL_DISCRIMINATION = "MODEL_DISCRIMINATION"
    PARAMETER_ESTIMATION = "PARAMETER_ESTIMATION"
    HYPOTHESIS_TESTING = "HYPOTHESIS_TESTING"
    SENSITIVITY_CHARACTERIZATION = "SENSITIVITY_CHARACTERIZATION"
    BOUNDARY_CONDITION_TEST = "BOUNDARY_CONDITION_TEST"
    ROBUSTNESS_TEST = "ROBUSTNESS_TEST"


class DesignCandidateStatus(StrEnum):
    """Lifecycle status of an experimental design candidate."""

    CANDIDATE = "CANDIDATE"
    EVALUATED = "EVALUATED"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"


class ObservableTarget(DomainModel):
    """Specification of an observable targeted for discrimination or testing."""

    id: str = Field(default="", description="Unique identifier")
    observable_id: str = Field(default="", description="Unique observable identifier")
    name: str = Field(description="Human-readable observable name")
    definition: str = Field(default="", description="Mathematical or physical definition")
    units: str = Field(default="", description="Physical / dimensionless units")
    source: str = Field(default="wave_lattice", description="System or operator providing the observable")
    computation_method: str = Field(default="", description="Method of extraction from raw simulation data")
    limitations: str = Field(default="", description="Known limitations of this observable metric")

    @model_validator(mode="after")
    def sync_id(self) -> ObservableTarget:
        if not self.id and self.observable_id:
            self.id = self.observable_id
        elif not self.observable_id and self.id:
            self.observable_id = self.id
        return self


class ResourceRequirements(ValueObject):
    """Domain-neutral execution and resource constraints for a candidate design."""

    max_runtime_sec: float | None = Field(default=None, description="Upper bound on computational runtime in seconds")
    max_memory_mb: float | None = Field(default=None, description="Upper bound on peak memory usage in megabytes")
    max_parameter_count: int | None = Field(default=None, description="Maximum number of simultaneous free parameters")
    max_experiments: int | None = Field(default=None, description="Maximum number of runs in a design batch")
    max_spatial_nodes: int | None = Field(default=None, description="Maximum grid resolution / spatial nodes")
    max_time_steps: int | None = Field(default=None, description="Maximum time integration steps")
    required_hardware: str | None = Field(default=None, description="Specialized hardware required (e.g. GPU, CPU)")
    required_instrument: str | None = Field(default=None, description="Physical laboratory instrument required")
    estimated_cost: float = Field(default=0.0, description="Abstract resource cost units")


class DiscriminationMetric(ValueObject):
    """
    Formally documented discrimination metric between competing models.

    Must explicitly define numerator, denominator, assumptions, and limitations.
    Never equates model difference to absolute probability or truth.
    """

    metric_name: str = Field(description="Name of the discrimination metric")
    numerator: str = Field(description="Definition of signal / model difference term")
    denominator: str = Field(description="Definition of noise / numerical uncertainty term")
    value: float = Field(description="Calculated scalar value of discrimination ratio D")
    assumptions: list[str] = Field(default_factory=list, description="Assumptions underlying the metric formulation")
    units: str = Field(default="dimensionless", description="Units of the metric")
    interpretation: str = Field(default="", description="Scientific interpretation guide")
    limitations: str = Field(default="", description="Known limits, edge cases, and validity boundaries")


class ExperimentalDesignCandidate(DomainModel):
    """
    Candidate experiment design capable of discriminating competing models or testing hypotheses.

    It is a candidate proposal; it does NOT possess execution or scientific authority
    until explicitly reviewed and promoted by human/domain authority.
    """

    id: str = Field(default="", description="Unique identifier")
    candidate_design_id: str = Field(default="", description="Unique candidate design identifier")
    project_id: str = Field(description="Parent research project identifier")
    research_question_id: str | None = Field(default=None, description="Governing research question ID")
    hypothesis_id: str | None = Field(default=None, description="Governing hypothesis ID")
    model_ids: list[str] = Field(default_factory=list, description="Competing models being evaluated / discriminated")
    parameter_assignments: dict[str, Any] = Field(
        default_factory=dict,
        description="Explicit assigned values for explored parameters",
    )
    controlled_variables: dict[str, Any] = Field(
        default_factory=dict,
        description="Explicitly held constant variables and experimental conditions",
    )
    independent_variables: list[str] = Field(
        default_factory=list,
        description="Names of variables systematically perturbed in this design",
    )
    dependent_variables: list[str] = Field(
        default_factory=list,
        description="Names of expected output/response variables",
    )
    target_observables: list[str] = Field(
        default_factory=list,
        description="IDs / names of observables targeted for discrimination",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Identified constraints satisfied by this candidate",
    )
    expected_information: dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of expected scientific information yield",
    )
    design_objective: DesignObjective = Field(
        default=DesignObjective.MODEL_DISCRIMINATION,
        description="Primary formal objective of this design",
    )
    execution_requirements: dict[str, Any] = Field(
        default_factory=dict,
        description="Technical execution configuration parameters",
    )
    resource_requirements: ResourceRequirements = Field(
        default_factory=ResourceRequirements,
        description="Resource and execution budget constraints",
    )
    risk_constraints: list[str] = Field(
        default_factory=list,
        description="Risk boundaries or instability hazards",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Explicit methodological and physical assumptions",
    )
    design_status: DesignCandidateStatus = Field(
        default=DesignCandidateStatus.CANDIDATE,
        description="Lifecycle state (CANDIDATE, EVALUATED, PROMOTED, REJECTED)",
    )
    design_strategy: str = Field(
        default="GRID",
        description="Exploration strategy used (e.g. GRID, LATIN_HYPERCUBE, ONE_AT_A_TIME)",
    )
    random_seed: int | None = Field(
        default=None,
        description="Explicit random seed for stochastic generation reproducibility",
    )
    sensitivity_study_ref: str | None = Field(
        default=None,
        description="Ref to SensitivityStudy consumed to guide candidate generation",
    )
    provenance_ref: str | None = Field(default=None, description="Provenance event identifier")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_id(self) -> ExperimentalDesignCandidate:
        if not self.id and self.candidate_design_id:
            self.id = self.candidate_design_id
        elif not self.candidate_design_id and self.id:
            self.candidate_design_id = self.id
        return self


class CandidateDesignEvaluation(DomainModel):
    """
    Comprehensive multi-objective evaluation of a candidate experimental design.

    Quantifies properties such as model discrimination, numerical robustness, resource cost,
    and sensitivity alignment. Does NOT declare an authoritative 'best experiment' winner.
    """

    id: str = Field(default="", description="Unique identifier")
    evaluation_id: str = Field(default="", description="Unique evaluation identifier")
    candidate_design_id: str = Field(description="Subject candidate design identifier")
    model_predictions: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Predicted observable values per model: {model_id: {observable: value}}",
    )
    predicted_differences: dict[str, float] = Field(
        default_factory=dict,
        description="Predicted observable divergence between competing models",
    )
    numerical_uncertainties: dict[str, float] = Field(
        default_factory=dict,
        description="Estimated numerical / discretization uncertainty per observable",
    )
    sensitivities: dict[str, float] = Field(
        default_factory=dict,
        description="Observed parameter sensitivities consumed from sensitivity studies",
    )
    discrimination_metric: DiscriminationMetric | None = Field(
        default=None,
        description="Formal model discrimination metric documentation",
    )
    discrimination_score: float = Field(
        default=0.0,
        description="Ratio of model difference to effective numerical uncertainty",
    )
    numerical_robustness: float = Field(
        default=1.0,
        description="Index of numerical stability (1.0 = highly robust, 0.0 = near CFL / unstable)",
    )
    parameter_coverage: float = Field(
        default=1.0,
        description="Coverage metric of parameter space explored",
    )
    resource_cost: float = Field(
        default=0.0,
        description="Quantified computational or experimental resource consumption score",
    )
    constraint_satisfaction: bool = Field(
        default=True,
        description="Whether all physical and numerical constraints are satisfied",
    )
    sensitivity_alignment: float = Field(
        default=1.0,
        description="Degree to which perturbations align with high-sensitivity parameters",
    )
    expected_observable_difference: float = Field(
        default=0.0,
        description="Magnitude of primary observable divergence",
    )
    evaluation_status: str = Field(default="COMPLETED", description="Status of evaluation calculation")
    notes: str = Field(default="", description="Evaluator notes — does NOT declare a winner")
    provenance_ref: str | None = Field(default=None, description="Provenance event identifier")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_id(self) -> CandidateDesignEvaluation:
        if not self.id and self.evaluation_id:
            self.id = self.evaluation_id
        elif not self.evaluation_id and self.id:
            self.evaluation_id = self.id
        return self


class ParetoCandidateSet(DomainModel):
    """
    Representation of the Pareto non-dominated frontier across candidate designs.

    Preserves multi-objective trade-offs (e.g. discrimination vs cost vs numerical uncertainty)
    without collapsing everything into an arbitrary single score or declaring a winner.
    """

    id: str = Field(default="", description="Unique identifier")
    set_id: str = Field(default="", description="Unique Pareto candidate set identifier")
    project_id: str = Field(description="Parent research project identifier")
    candidate_evaluations: list[CandidateDesignEvaluation] = Field(
        default_factory=list,
        description="Evaluations included in this multi-objective trade-off analysis",
    )
    non_dominated_candidate_ids: list[str] = Field(
        default_factory=list,
        description="IDs of candidate designs on the Pareto non-dominated frontier",
    )
    objectives: list[str] = Field(
        default_factory=list,
        description="List of objectives evaluated (e.g. ['maximize:discrimination_score', 'minimize:resource_cost'])",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_id(self) -> ParetoCandidateSet:
        if not self.id and self.set_id:
            self.id = self.set_id
        elif not self.set_id and self.id:
            self.set_id = self.id
        return self
