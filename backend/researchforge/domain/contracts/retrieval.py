"""Retrieval provider protocol contract supporting dual semantic & exact modes."""

from typing import Protocol, runtime_checkable

from researchforge.domain.models.evidence import EvidenceFragment


@runtime_checkable
class RetrievalProvider(Protocol):
    """Contract supporting dual retrieval modes: Semantic similarity and Exact evidence match."""

    provider_name: str

    async def index(self, fragments: list[EvidenceFragment]) -> int:
        """Index fragments for dual-mode retrieval."""
        ...

    async def search_semantic(self, query: str, top_k: int = 5) -> list[EvidenceFragment]:
        """Perform vector embedding semantic search (returns candidate passages, NOT proof)."""
        ...

    async def search_evidence(self, exact_pattern: str, top_k: int = 5) -> list[EvidenceFragment]:
        """Perform exact structured matching against extracted figures, tables, and equations."""
        ...
