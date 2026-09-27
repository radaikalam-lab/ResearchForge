"""Evidence, claims, fragments, variables, methods, and scientific model entities."""

from enum import StrEnum
from typing import Any

from pydantic import Field

from researchforge.domain.base import DomainModel
from researchforge.domain.models.model_validation import ModelValidationStatus
from researchforge.domain.value_objects.uncertainty import UncertaintyProfile


class EvidenceType(StrEnum):
    """Categorization of concrete scientific evidence."""

    TEXT = "TEXT"
    TABLE = "TABLE"
    FIGURE = "FIGURE"
    EQUATION = "EQUATION"
    DATASET = "DATASET"
    EXPERIMENTAL_RESULT = "EXPERIMENTAL_RESULT"
    SIMULATION_RESULT = "SIMULATION_RESULT"
    STATISTICAL_RESULT = "STATISTICAL_RESULT"
    OBSERVATION = "OBSERVATION"
    REVIEWER_ASSERTION = "REVIEWER_ASSERTION"


class EvidenceFragment(DomainModel):
    """Atomic excerpt or data slice representing a verifiable observation."""

    source_id: str
    evidence_type: EvidenceType
    location_reference: str = Field(description="Page, line, table number, or URI fragment")
    content: str = Field(description="Exact excerpt, tabular string, or equation string")
    extracted_data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_method: str = "MANUAL"  # MANUAL, OCR, PARSER, LLM_PROPOSED


class Evidence(DomainModel):
    """Validated aggregation of evidence fragments supporting or refuting claims."""

    project_id: str = ""
    source_id: str = ""
    claim_ids: list[str] = Field(default_factory=list)
    fragment_ids: list[str] = Field(default_factory=list)
    evidence_type: EvidenceType = EvidenceType.TEXT
    summary: str = ""
    fragments: list[EvidenceFragment] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    uncertainty: UncertaintyProfile = Field(default_factory=UncertaintyProfile)
    validation_status: str = "VALIDATED"  # VALIDATED, UNVERIFIED, CONTRADICTED


class ClaimType(StrEnum):
    """Controlled vocabulary for scientific claims."""

    OBSERVATION = "OBSERVATION"
    MEASUREMENT = "MEASUREMENT"
    METHOD = "METHOD"
    CAUSAL_CLAIM = "CAUSAL_CLAIM"
    CORRELATION = "CORRELATION"
    PARAMETER_RELATIONSHIP = "PARAMETER_RELATIONSHIP"
    LIMITATION = "LIMITATION"
    NEGATIVE_RESULT = "NEGATIVE_RESULT"
    BOUNDARY_CONDITION = "BOUNDARY_CONDITION"
    CONTRADICTION = "CONTRADICTION"
    EMPIRICAL = "EMPIRICAL"
    THEORETICAL = "THEORETICAL"


class Claim(DomainModel):
    """Scientific assertion extracted from literature or produced by an experiment."""

    project_id: str = ""
    statement: str
    claim_type: str = "EMPIRICAL"  # ClaimType values supported as strings or enums
    subject: str = ""
    predicate: str = ""
    object: str = ""
    parameter_name: str | None = None
    parameter_value_range: tuple[float, float] | None = None
    source_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_reported_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    domain_assessment: str = "PENDING"  # PENDING, ACCEPTED, REJECTED, CONTRADICTED
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    is_grounded_in_evidence: bool = False


class EvidenceClaimBinding(DomainModel):
    """Explicit verifiable link binding an Evidence item or fragment to a Claim."""

    project_id: str
    evidence_id: str
    fragment_id: str | None = None
    claim_id: str
    source_id: str
    binding_type: str = "SUPPORTS"  # SUPPORTS, REFUTES, QUALIFIES, RESTRICTS
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_reported_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    domain_assessment: str = "ACCEPTED"  # ACCEPTED, DISPUTED, REJECTED


class PotentialContradiction(DomainModel):
    """Formal contradiction or discrepancy between two claims across literature/evidence sources."""

    project_id: str
    claim_a_id: str
    claim_b_id: str
    source_a_id: str = ""
    source_b_id: str = ""
    # Types: DIRECT_OPPOSITION, PARAMETER_DISCREPANCY, METHODOLOGICAL_DIFFERENCE, BOUNDARY_CONDITION_DISCREPANCY
    contradiction_type: str = "PARAMETER_DISCREPANCY"
    description: str
    scope_difference: str = ""
    parameter_difference: str = ""
    methodological_difference: str = ""


class Variable(DomainModel):
    """Scientific variable under observation or manipulation."""

    name: str
    symbol: str | None = None
    variable_type: str = "INDEPENDENT"  # INDEPENDENT, DEPENDENT, CONTROL, CONFOUNDING
    unit: str | None = None
    data_type: str = "FLOAT"  # FLOAT, INT, CATEGORICAL, MATRIX, TIME_SERIES
    valid_range: tuple[float, float] | None = None
    description: str = ""


class Method(DomainModel):
    """Scientific procedure, algorithm, or experimental protocol."""

    name: str
    description: str
    category: str = "COMPUTATIONAL"  # COMPUTATIONAL, ANALYTICAL, STATISTICAL, EXPERIMENTAL
    parameters: dict[str, Any] = Field(default_factory=dict)
    code_reference: str | None = None


class ScientificModel(DomainModel):
    """Mathematical, mechanistic, or statistical model.

    A model captures the mathematical specification and its assumptions,
    distinct from any particular numerical implementation or run.
    """

    name: str
    version: str = "1.0.0"
    description: str = Field(default="", description="Detailed description of the model")
    mathematical_form: str = Field(
        default="",
        description="Governing equations in mathematical notation or formal language",
    )
    equations: list[str] = Field(default_factory=list)
    state_variables: list[str] = Field(
        default_factory=list,
        description="State variables of the model (e.g. u(x,t), v(x,t))",
    )
    parameters: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    boundary_conditions: dict[str, Any] = Field(
        default_factory=dict,
        description="Boundary condition specifications",
    )
    initial_conditions: dict[str, Any] = Field(
        default_factory=dict,
        description="Initial condition specifications",
    )
    source_terms: dict[str, Any] = Field(
        default_factory=dict,
        description="Source term specifications",
    )
    domain_of_validity: str = ""
    validity_scope: str = Field(
        default="",
        description="Domain of applicability for which the model is intended",
    )
    validation_status: ModelValidationStatus = Field(
        default=ModelValidationStatus.UNVERIFIED,
        description="Current validation status of the model",
    )
