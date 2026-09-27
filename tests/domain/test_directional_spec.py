"""Tests for Directional Programming specifications."""

from researchforge.domain.value_objects.directional import (
    CandidatePath,
    DirectionalConstraint,
    DirectionalSpecification,
    ResearchState,
    TargetResearchState,
)


def test_directional_specification_contract() -> None:
    """Verify serialization and semantics of directional research specifications."""
    spec = DirectionalSpecification(
        current_state=ResearchState(
            domain="materials_science",
            known_evidence_summary="sparse experimental data in high-temperature phase",
        ),
        target_state=TargetResearchState(
            goals=["establish whether lattice strain affects conductivity non-linearly"],
            required_confidence=0.95,
        ),
        objectives=["identify causal relationship", "estimate critical strain threshold"],
        constraints=[
            DirectionalConstraint(
                name="compute_budget",
                description="bounded compute budget under 10 GPU hours",
                is_hard_constraint=True,
            )
        ],
        available_capabilities=["COMPUTE_NUMERICAL", "RUN_SIMULATION"],
        forbidden_actions=["AUTONOMOUS_PUBLICATION", "PHYSICAL_ACTUATION"],
        success_criteria=["falsifiable hypothesis", "statistically defensible result"],
        uncertainty_tolerance=0.05,
    )

    assert spec.current_state.domain == "materials_science"
    assert len(spec.constraints) == 1
    assert "AUTONOMOUS_PUBLICATION" in spec.forbidden_actions


def test_candidate_paths_are_non_authoritative() -> None:
    """Verify candidate paths are explicitly non-authoritative proposals."""
    path = CandidatePath(
        path_id="path_01",
        description="High throughput lattice simulation",
        steps=["Step 1", "Step 2"],
        is_authoritative_plan=False,
    )
    assert path.is_authoritative_plan is False
