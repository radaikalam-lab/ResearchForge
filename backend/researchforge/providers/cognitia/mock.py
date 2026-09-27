"""Mock Cognitia Provider satisfying CognitiaProvider contract for local/offline testing."""

import uuid
from typing import Any

from researchforge.domain.contracts.cognitia import (
    CognitiaAdvisoryRequest,
    CognitiaAdvisoryResult,
    CognitiaProvider,
)
from researchforge.domain.models.epistemic import EpistemicAssessment, EpistemicTier
from researchforge.domain.models.evidence import Claim, ScientificModel
from researchforge.domain.models.experiment import ExperimentResult
from researchforge.domain.models.falsification import (
    FalsificationEvaluation,
    FalsificationStatus,
)
from researchforge.domain.models.hypothesis import Assumption, Hypothesis
from researchforge.domain.value_objects.directional import CandidatePath, DirectionalSpecification
from researchforge.domain.value_objects.uncertainty import UncertaintyProfile


class MockCognitiaProvider(CognitiaProvider):
    """Deterministic local reference implementation of Cognitia Epistemic Plane."""

    provider_name: str = "mock-cognitia-v1"

    async def evaluate_claim(self, claim: Claim) -> EpistemicAssessment:
        """Critique claim epistemics."""
        return EpistemicAssessment(
            id=f"epist_{uuid.uuid4().hex[:8]}",
            target_id=claim.id,
            target_type="Claim",
            tier=EpistemicTier.TIER_1_CRITIQUE,
            epistemic_soundness=0.88,
            coherence_score=0.92,
            identified_assumptions=["Assumes linearity in parameter response regime."],
            hidden_assumptions=["Assumes unmeasured environmental variables remain stationary."],
            vulnerabilities=["Boundary conditions not established beyond standard regime."],
            falsifiability_assessment="Claim is empirically testable via regression against baseline.",
            uncertainty=UncertaintyProfile(epistemic_uncertainty=0.15),
        )

    async def evaluate_hypothesis(self, hypothesis: Hypothesis) -> EpistemicAssessment:
        """Critique hypothesis structure, assumptions, and falsifiability."""
        return EpistemicAssessment(
            id=f"epist_{uuid.uuid4().hex[:8]}",
            target_id=hypothesis.id,
            target_type="Hypothesis",
            tier=EpistemicTier.TIER_1_CRITIQUE,
            epistemic_soundness=0.85,
            coherence_score=0.90,
            identified_assumptions=[f"Assumes mechanism: {hypothesis.mechanism}"],
            hidden_assumptions=["Assumes measurement apparatus noise follows Gaussian distribution."],
            vulnerabilities=["High sensitivity to confounding variables in multi-parameter space."],
            falsifiability_assessment=(
                f"Contains {len(hypothesis.falsification_criteria)} explicit falsification criteria."
            ),
            uncertainty=UncertaintyProfile(model_uncertainty=0.10, epistemic_uncertainty=0.12),
        )

    async def identify_assumptions(self, hypothesis: Hypothesis) -> list[Assumption]:
        """Decompose hypothesis into explicit testable assumptions."""
        return [
            Assumption(
                id=f"assump_{uuid.uuid4().hex[:8]}",
                statement="Linear scalability across standard operating parameter bounds.",
                is_testable=True,
                criticality=0.85,
                justification="Derived from underlying mechanistic equations.",
            ),
            Assumption(
                id=f"assump_{uuid.uuid4().hex[:8]}",
                statement="Absence of non-linear hysteresis under cyclic perturbation.",
                is_testable=True,
                criticality=0.70,
                justification="Consistent with first-order perturbation theory.",
            ),
        ]

    async def compare_models(self, models: list[ScientificModel]) -> dict[str, Any]:
        """Perform model comparison across predictive scope and complexity."""
        return {
            "comparison_id": f"comp_{uuid.uuid4().hex[:8]}",
            "model_count": len(models),
            "preferred_model": models[0].name if models else None,
            "aic_bic_ranking": [m.name for m in models],
            "epistemic_tradeoff": "Model 1 offers higher parsimony with minimal residual penalty.",
        }

    async def evaluate_representation(self, representation_spec: dict[str, Any]) -> dict[str, Any]:
        """Critique mathematical representation adequacy."""
        return {
            "is_adequate": True,
            "dimensional_consistency": "VALIDATED",
            "conservation_laws_respected": True,
        }

    async def generate_candidate_paths(self, spec: DirectionalSpecification) -> list[CandidatePath]:
        """Generate non-authoritative candidate research pathways."""
        return [
            CandidatePath(
                path_id=f"path_{uuid.uuid4().hex[:8]}",
                description="High-throughput numerical simulation sweep followed by Bayesian model fitting.",
                steps=[
                    "Run parameter lattice simulation (N=500)",
                    "Fit generalized linear model with cross-validation",
                    "Evaluate against falsification thresholds",
                ],
                estimated_cost_hours=1.5,
                risk_profile="LOW",
                rationale="Minimizes compute expenditure while covering primary state space.",
                is_authoritative_plan=False,
            ),
            CandidatePath(
                path_id=f"path_{uuid.uuid4().hex[:8]}",
                description="Adaptive Markov Chain Monte Carlo parameter exploration.",
                steps=[
                    "Initialize MCMC chains with Latin hypercube sampling",
                    "Assess Gelman-Rubin convergence",
                    "Compute posterior parameter distributions",
                ],
                estimated_cost_hours=4.0,
                risk_profile="MEDIUM",
                rationale="Provides rigorous parameter uncertainty estimation.",
                is_authoritative_plan=False,
            ),
        ]

    async def evaluate_falsification(
        self, hypothesis: Hypothesis, results: list[ExperimentResult]
    ) -> FalsificationEvaluation:
        """Popperian falsification evaluation against experiment results."""
        has_failure = False
        failed_ids = []
        for crit in hypothesis.falsification_criteria:
            for res in results:
                metric_val = res.metrics.get(crit.metric_name)
                if metric_val is not None and metric_val >= crit.refutation_threshold:
                    has_failure = True
                    failed_ids.append(crit.id)

        status = FalsificationStatus.CONTRADICTED if has_failure else FalsificationStatus.SUPPORTED
        reason = (
            f"Experimental observations refuted {len(failed_ids)} falsification criteria."
            if has_failure
            else "Experimental observations satisfy all predictions without triggering refutation thresholds."
        )

        return FalsificationEvaluation(
            id=f"eval_{uuid.uuid4().hex[:8]}",
            hypothesis_id=hypothesis.id,
            status=status,
            reason=reason,
            evidence_refs=[r.id for r in results],
            evaluated_criteria_ids=[c.id for c in hypothesis.falsification_criteria],
            failed_criteria_ids=failed_ids,
            uncertainty=UncertaintyProfile(sampling_uncertainty=0.05, computational_uncertainty=0.02),
        )

    async def track_theory_transition(
        self, prior_theory: str, proposed_theory: str, anomalies: list[str]
    ) -> dict[str, Any]:
        """Analyze Kuhn/Lakatos scientific theory transition."""
        return {
            "progressive_problemshift": True,
            "excess_empirical_content": True,
            "corroborated_excess_content": len(anomalies) > 0,
            "notes": f"Proposed theory explains {len(anomalies)} anomalies of {prior_theory}.",
        }

    async def consult_advisory(self, request: CognitiaAdvisoryRequest) -> CognitiaAdvisoryResult:
        """Provide non-authoritative advisory analysis over a bounded semantic graph context."""
        return CognitiaAdvisoryResult(
            id=f"adv_res_{uuid.uuid4().hex[:8]}",
            result_id=f"adv_res_{uuid.uuid4().hex[:8]}",
            request_id=request.request_id,
            context_graph_hash=request.context_graph_hash,
            recommendations=[
                "Explore boundary conditions where parameter linearity may break down.",
                "Incorporate orthogonal measurement modalities to control for systematic error.",
            ],
            criticisms=[
                "Assumption of unmeasured environmental stationarity lacks empirical validation in current subgraph."
            ],
            candidate_hypotheses=[
                "H_alt: Response metric displays sub-linear logarithmic saturation at high parameter densities."
            ],
            candidate_relationships=[
                {
                    "relation_type": "CONTRADICTS",
                    "source": "empirical_finding_alpha",
                    "target": "theoretical_model_beta",
                }
            ],
            uncertainty=0.18,
            provenance={
                "provider": self.provider_name,
                "context_hash": request.context_graph_hash,
                "contract_version": request.semantic_contract_version,
            },
            model_metadata={
                "engine": "cognitia-epistemic-plane-mock",
                "tier": "ADVISORY_TIER_1",
            },
            advisory_status="ADVISORY",
        )
