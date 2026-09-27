"""Providers package with default registry population."""

from researchforge.providers.citation.mock import MockCitationProvider
from researchforge.providers.cognitia.adapter import CognitiaAdapter
from researchforge.providers.evidence.mock import MockEvidenceProvider
from researchforge.providers.experiment.mock import MockExperimentProvider
from researchforge.providers.gap.mock import MockGapAnalysisProvider
from researchforge.providers.literature.mock import MockLiteratureProvider
from researchforge.providers.llm.mock import MockReasoningProvider
from researchforge.providers.publication.mock import MockPublicationProvider
from researchforge.providers.registry import ProviderRegistry, global_registry
from researchforge.providers.retrieval.mock import MockRetrievalProvider
from researchforge.providers.simulation.mock import MockSimulationProvider
from researchforge.providers.statistics.mock import MockStatisticsProvider


def register_default_providers(registry: ProviderRegistry | None = None) -> ProviderRegistry:
    """Populate registry with default local-first reference providers."""
    reg = registry or global_registry
    reg.register("literature", MockLiteratureProvider())
    reg.register("citation", MockCitationProvider())
    reg.register("evidence", MockEvidenceProvider())
    reg.register("retrieval", MockRetrievalProvider())
    reg.register("reasoning", MockReasoningProvider())
    reg.register("cognitia", CognitiaAdapter())
    reg.register("experiment", MockExperimentProvider())
    reg.register("simulation", MockSimulationProvider())
    reg.register("statistics", MockStatisticsProvider())
    reg.register("publication", MockPublicationProvider())
    reg.register("gap", MockGapAnalysisProvider())
    return reg


# Auto-populate global registry on import
register_default_providers(global_registry)

__all__ = [
    "CognitiaAdapter",
    "MockCitationProvider",
    "MockEvidenceProvider",
    "MockExperimentProvider",
    "MockGapAnalysisProvider",
    "MockLiteratureProvider",
    "MockPublicationProvider",
    "MockReasoningProvider",
    "MockRetrievalProvider",
    "MockSimulationProvider",
    "MockStatisticsProvider",
    "ProviderRegistry",
    "global_registry",
    "register_default_providers",
]
