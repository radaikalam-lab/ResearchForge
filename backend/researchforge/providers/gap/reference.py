"""Deterministic Reference Gap Analysis Provider."""

from researchforge.domain.contracts.gap import GapAnalysisProvider
from researchforge.domain.models.evidence import Claim, Evidence, PotentialContradiction
from researchforge.domain.models.gap import GapCandidate, GapType, ResearchGap
from researchforge.domain.models.hypothesis import Assumption, FalsificationCriterion, Hypothesis, Prediction


class ReferenceGapAnalysisProvider(GapAnalysisProvider):
    """Deterministic reference gap analysis provider deriving scientific gaps and hypothesis candidates."""

    provider_name: str = "reference-gap-analyzer-v1"

    async def analyze_gaps(
        self,
        evidence_items: list[Evidence],
        claims: list[Claim] | None = None,
        contradictions: list[PotentialContradiction] | None = None,
    ) -> list[GapCandidate]:
        """Analyze evidence, claims, and contradictions to propose research gap candidates."""
        candidates: list[GapCandidate] = []

        # 1. Contradiction Gap
        if contradictions:
            candidates.append(
                GapCandidate(
                    id="gap_cand_contra_01",
                    description=(
                        "Contradiction in Response Y across range [0.0, 2.0]: conflicting linear vs. null findings "
                        "due to assay variance and sample size disparity."
                    ),
                    gap_type=GapType.CONTRADICTION_GAP,
                    supporting_source_ids=[c.source_a_id for c in contradictions if c.source_a_id],
                    contradictory_source_ids=[c.source_b_id for c in contradictions if c.source_b_id],
                    affected_variables=["Parameter X", "Response Y", "Assay Noise"],
                    unexplored_region="Standardized high-powered replication in range [0.0, 2.0]",
                    confidence=0.94,
                    unresolved_questions=["Does variance masking conceal true linear slope in unbuffered assays?"],
                )
            )

        # 2. Boundary Condition Gap
        candidates.append(
            GapCandidate(
                id="gap_cand_boundary_01",
                description=(
                    "Uncharacterized boundary transition of Parameter X in regime [2.0, 3.0] between linear slope and "
                    "saturation plateau."
                ),
                gap_type=GapType.BOUNDARY_CONDITION_GAP,
                supporting_source_ids=[e.source_id for e in evidence_items if e.source_id],
                affected_variables=["Parameter X", "Response Y", "Saturation Threshold"],
                unexplored_region="Critical transition boundary X in [2.0, 3.0]",
                confidence=0.96,
                unresolved_questions=[
                    "At what precise threshold does linear response transition to saturation plateau?"
                ],
            )
        )

        return candidates

    async def evaluate_gap_validity(
        self,
        candidate: GapCandidate,
        evidence_items: list[Evidence],
    ) -> ResearchGap | None:
        """Promote a verified candidate to an authoritative ResearchGap aggregate."""
        if not evidence_items:
            return None

        return ResearchGap(
            id=f"gap_{candidate.id.replace('gap_cand_', '')}",
            project_id=evidence_items[0].project_id if evidence_items else "proj_default",
            title=f"Research Gap: {candidate.unexplored_region}",
            description=candidate.description,
            gap_type=candidate.gap_type,
            supporting_evidence_ids=[e.id for e in evidence_items],
            affected_variables=candidate.affected_variables,
            unexplored_region=candidate.unexplored_region,
            confidence=candidate.confidence,
            impact_score=0.90,
        )

    def propose_hypothesis_candidate(
        self,
        gap: ResearchGap,
        project_id: str,
    ) -> Hypothesis:
        """Formulate a testable scientific hypothesis candidate with mandatory falsification criteria."""
        falsification_1 = FalsificationCriterion(
            id="fc_01",
            description=(
                "Slope across transition regime [2.0, 3.0] remains strictly constant (>2.0) with no saturation plateau."
            ),
            condition_expression="saturation_index < 0.05 and p_value < 0.05",
            metric_name="saturation_index",
            refutation_threshold=0.05,
            is_fatal_to_hypothesis=True,
        )
        falsification_2 = FalsificationCriterion(
            id="fc_02",
            description="Response Y drops abruptly to zero at X = 2.0 without gradual plateau.",
            condition_expression="drop_rate > 0.80",
            metric_name="drop_rate",
            refutation_threshold=0.80,
            is_fatal_to_hypothesis=True,
        )

        pred = Prediction(
            id="pred_01",
            statement="Response Y exhibits non-linear saturation curve with inflection point between X=2.3 and X=2.7.",
            expected_observable="inflection_point_x",
            expected_direction="NON_LINEAR",
            significance_threshold=0.05,
        )

        assump = Assumption(
            id="assump_01",
            statement="System temperature and buffer condition Z remain constant during parameter ramp.",
            is_testable=True,
            criticality=0.90,
        )

        hyp = Hypothesis(
            id=f"hyp_{gap.id[:8]}_candidate",
            project_id=project_id,
            statement=(
                "Parameter X undergoes a non-linear saturation transition in regime [2.0, 3.0] "
                "at critical threshold X_c = 2.45."
            ),
            mechanism="Receptor binding saturation and kinetic rate limiting under condition Z.",
            prediction_ids=[pred.id],
            assumption_ids=[assump.id],
            falsification_criteria=[falsification_1, falsification_2],
            evidence_basis_ids=gap.supporting_evidence_ids,
            confidence=0.85,
        )
        return hyp
