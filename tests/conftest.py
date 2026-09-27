"""Shared pytest fixtures for ResearchForge."""

import pytest
from researchforge.configuration.settings import Settings
from researchforge.domain.models.evidence import Evidence, EvidenceType
from researchforge.domain.models.hypothesis import FalsificationCriterion, Hypothesis
from researchforge.domain.models.project import ResearchProject
from researchforge.domain.state_machine import ResearchLifecycleState
from researchforge.provenance.ledger import ProvenanceLedger
from researchforge.providers import ProviderRegistry, register_default_providers


@pytest.fixture
def test_settings() -> Settings:
    """Provide clean test settings."""
    return Settings(
        env="test",
        debug=True,
        cognitia_mock_mode=True,
        sandbox_strict=True,
    )


@pytest.fixture
def provider_registry() -> ProviderRegistry:
    """Provide populated test provider registry."""
    reg = ProviderRegistry()
    return register_default_providers(reg)


@pytest.fixture
def in_memory_ledger() -> ProvenanceLedger:
    """Provide clean in-memory provenance ledger."""
    return ProvenanceLedger()


@pytest.fixture
def sample_project() -> ResearchProject:
    """Provide a standard sample project."""
    return ResearchProject(
        id="proj_test_001",
        title="Test Investigation of Material Lattices",
        description="Testing sample project state",
        state=ResearchLifecycleState.DRAFT,
    )


@pytest.fixture
def sample_falsification_criterion() -> FalsificationCriterion:
    """Provide a standard falsification criterion."""
    return FalsificationCriterion(
        id="crit_test_001",
        description="P-value must not exceed 0.05",
        condition_expression="p_value > 0.05",
        metric_name="p_value",
        refutation_threshold=0.05,
        is_fatal_to_hypothesis=True,
    )


@pytest.fixture
def sample_hypothesis(sample_falsification_criterion: FalsificationCriterion) -> Hypothesis:
    """Provide a valid falsifiable hypothesis."""
    return Hypothesis(
        id="hyp_test_001",
        project_id="proj_test_001",
        statement="Increased lattice strain reduces electrical resistance non-linearly.",
        mechanism="Strain-induced bandgap deformation.",
        falsification_criteria=[sample_falsification_criterion],
    )


@pytest.fixture
def sample_evidence() -> Evidence:
    """Provide a valid evidence item."""
    return Evidence(
        id="evid_test_001",
        evidence_type=EvidenceType.EXPERIMENTAL_RESULT,
        summary="Empirical measurement of resistance drop under 2% lattice strain.",
        confidence=0.95,
        validation_status="VALIDATED",
    )
