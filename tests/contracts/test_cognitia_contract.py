"""Contract test for CognitiaProvider implementations."""

import pytest
from researchforge.domain.contracts.cognitia import CognitiaProvider
from researchforge.domain.models.epistemic import EpistemicTier
from researchforge.domain.models.evidence import Claim, ScientificModel
from researchforge.domain.models.experiment import ExperimentResult
from researchforge.domain.models.falsification import FalsificationStatus
from researchforge.domain.models.hypothesis import FalsificationCriterion, Hypothesis
from researchforge.domain.value_objects.directional import (
    DirectionalSpecification,
    ResearchState,
    TargetResearchState,
)
from researchforge.providers.cognitia.adapter import CognitiaAdapter


@pytest.mark.asyncio
async def test_cognitia_provider_contract_conformance() -> None:
    """Verify provider implements CognitiaProvider protocol."""
    provider: CognitiaProvider = CognitiaAdapter()
    assert isinstance(provider, CognitiaProvider)

    claim = Claim(id="c1", statement="Phase stability increases under high pressure.")
    assessment = await provider.evaluate_claim(claim)
    assert assessment.target_id == claim.id
    assert assessment.tier == EpistemicTier.TIER_1_CRITIQUE
    assert assessment.epistemic_soundness > 0.0

    crit = FalsificationCriterion(
        id="crit_1",
        description="Refutation threshold",
        condition_expression="error_rate > 0.1",
        metric_name="error_rate",
        refutation_threshold=0.1,
    )
    hyp = Hypothesis(
        id="h1",
        project_id="p1",
        statement="Lattice distortion leads to bandgap shift.",
        mechanism="Atomic displacement.",
        falsification_criteria=[crit],
    )

    hyp_assessment = await provider.evaluate_hypothesis(hyp)
    assert hyp_assessment.target_id == hyp.id
    assert len(hyp_assessment.identified_assumptions) > 0

    assumptions = await provider.identify_assumptions(hyp)
    assert len(assumptions) > 0

    models = [
        ScientificModel(id="m1", name="LinearModel"),
        ScientificModel(id="m2", name="QuadraticModel"),
    ]
    model_comp = await provider.compare_models(models)
    assert "preferred_model" in model_comp

    spec = DirectionalSpecification(
        current_state=ResearchState(domain="Materials"),
        target_state=TargetResearchState(goals=["Validate bandgap shift"]),
    )
    paths = await provider.generate_candidate_paths(spec)
    assert len(paths) > 0
    assert paths[0].is_authoritative_plan is False

    # Falsification evaluation (supported)
    res_supported = [
        ExperimentResult(
            id="r1",
            run_id="run_1",
            metrics={"error_rate": 0.02},
            output_hash="hash_1",
        )
    ]
    fals_supported = await provider.evaluate_falsification(hyp, res_supported)
    assert fals_supported.status == FalsificationStatus.SUPPORTED

    # Falsification evaluation (contradicted)
    res_failed = [
        ExperimentResult(
            id="r2",
            run_id="run_2",
            metrics={"error_rate": 0.25},
            output_hash="hash_2",
        )
    ]
    fals_failed = await provider.evaluate_falsification(hyp, res_failed)
    assert fals_failed.status == FalsificationStatus.CONTRADICTED
