"""Mock retrieval provider supporting dual semantic and exact modes."""

from researchforge.domain.contracts.retrieval import RetrievalProvider
from researchforge.domain.models.evidence import EvidenceFragment


class MockRetrievalProvider(RetrievalProvider):
    """Mock dual-mode retrieval provider."""

    provider_name: str = "mock-retrieval-v1"

    def __init__(self) -> None:
        self._fragments: list[EvidenceFragment] = []

    async def index(self, fragments: list[EvidenceFragment]) -> int:
        """Index fragments."""
        self._fragments.extend(fragments)
        return len(fragments)

    async def search_semantic(self, query: str, top_k: int = 5) -> list[EvidenceFragment]:
        """Perform semantic search (heuristic word match for mock)."""
        words = set(query.lower().split())
        matched = [f for f in self._fragments if any(w in f.content.lower() for w in words)]
        return matched[:top_k] if matched else self._fragments[:top_k]

    async def search_evidence(self, exact_pattern: str, top_k: int = 5) -> list[EvidenceFragment]:
        """Perform exact structured matching."""
        return [f for f in self._fragments if exact_pattern in f.content][:top_k]
