"""Domain validation service enforcing scientific invariants."""

from researchforge.domain.models.artifact import Manuscript
from researchforge.domain.models.conclusion import Conclusion, ResearchFinding
from researchforge.domain.models.hypothesis import Hypothesis
from researchforge.domain.models.statistics import StatisticalAnalysis


class InvariantViolationError(Exception):
    """Raised when a core scientific or architectural invariant is violated."""


class ScientificValidationService:
    """Validates structural and epistemic invariants across domain entities."""

    @staticmethod
    def validate_hypothesis_falsifiability(hypothesis: Hypothesis) -> None:
        """Invariant: A hypothesis MUST have at least one explicit falsification criterion."""
        if not hypothesis.falsification_criteria:
            raise InvariantViolationError(f"Hypothesis '{hypothesis.id}' lacks explicit falsification criteria.")

    @staticmethod
    def validate_finding_grounding(finding: ResearchFinding) -> None:
        """Invariant: A scientific finding MUST link to at least one evidence item."""
        if not finding.evidence_ids:
            raise InvariantViolationError(
                f"Finding '{finding.id}' cannot be accepted without supporting evidence references."
            )

    @staticmethod
    def validate_conclusion_authority(conclusion: Conclusion) -> None:
        """Invariant: A conclusion requires verified findings and explicit human gatekeeper approval."""
        if not conclusion.finding_ids:
            raise InvariantViolationError(f"Conclusion '{conclusion.id}' must reference at least one verified finding.")
        if not conclusion.human_decision_id:
            raise InvariantViolationError(f"Conclusion '{conclusion.id}' lacks human researcher authorization.")

    @staticmethod
    def validate_statistical_integrity(analysis: StatisticalAnalysis) -> None:
        """Invariant: Statistical test results must reference raw underlying data."""
        for test in analysis.tests:
            if not test.raw_data_refs:
                raise InvariantViolationError(
                    f"Statistical test '{test.test_name}' has no raw numerical data references."
                )

    @staticmethod
    def validate_manuscript_traceability(manuscript: Manuscript) -> None:
        """Invariant: Every manuscript section claim must be traceable or explicitly marked as interpretation."""
        for section in manuscript.sections:
            if (
                not section.is_interpretation
                and not section.referenced_claim_ids
                and not section.referenced_evidence_ids
            ):
                if section.section_type in {"RESULTS", "CONCLUSION"}:
                    raise InvariantViolationError(f"Manuscript section '{section.title}' contains ungrounded claims.")
