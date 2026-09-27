"""Citation provider protocol contract."""

from typing import Protocol, runtime_checkable

from researchforge.domain.models.literature import Citation, Paper


@runtime_checkable
class CitationProvider(Protocol):
    """Contract for DOI resolution, BibTeX formatting, and citation graph validation."""

    provider_name: str

    async def resolve_doi(self, doi: str) -> Paper | None:
        """Resolve a DOI into a normalized Paper record."""
        ...

    async def format_bibtex(self, paper: Paper) -> str:
        """Render a deterministic BibTeX entry for the given paper."""
        ...

    async def validate_citation_graph(self, citations: list[Citation]) -> bool:
        """Verify topological consistency and detect citation cycles or anomalies."""
        ...
