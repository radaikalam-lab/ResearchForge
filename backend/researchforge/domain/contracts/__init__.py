"""Domain contracts (typing Protocols) for all ResearchForge providers."""

from researchforge.domain.contracts.citation import CitationProvider
from researchforge.domain.contracts.cognitia import CognitiaProvider
from researchforge.domain.contracts.evidence import EvidenceProvider
from researchforge.domain.contracts.experiment import ExperimentProvider
from researchforge.domain.contracts.gap import GapAnalysisProvider
from researchforge.domain.contracts.graph_persistence import GraphPersistencePort
from researchforge.domain.contracts.literature import LiteratureProvider
from researchforge.domain.contracts.publication import PublicationProvider
from researchforge.domain.contracts.reasoning import ReasoningProvider
from researchforge.domain.contracts.retrieval import RetrievalProvider
from researchforge.domain.contracts.simulation import SimulationProvider
from researchforge.domain.contracts.statistics import StatisticsProvider

__all__ = [
    "CitationProvider",
    "CognitiaProvider",
    "EvidenceProvider",
    "ExperimentProvider",
    "GapAnalysisProvider",
    "GraphPersistencePort",
    "LiteratureProvider",
    "PublicationProvider",
    "ReasoningProvider",
    "RetrievalProvider",
    "SimulationProvider",
    "StatisticsProvider",
]
