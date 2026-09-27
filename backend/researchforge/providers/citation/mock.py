"""Mock citation provider."""

import uuid

from researchforge.domain.contracts.citation import CitationProvider
from researchforge.domain.models.literature import Citation, Paper


class MockCitationProvider(CitationProvider):
    """Mock implementation of CitationProvider."""

    provider_name: str = "mock-citation-v1"

    async def resolve_doi(self, doi: str) -> Paper | None:
        """Resolve a DOI into a Paper."""
        return Paper(
            id=f"paper_{uuid.uuid4().hex[:8]}",
            title=f"Resolved Paper for {doi}",
            authors=["Lead Author"],
            year=2024,
            doi=doi,
        )

    async def format_bibtex(self, paper: Paper) -> str:
        """Render BibTeX entry."""
        author_str = " and ".join(paper.authors) if paper.authors else "Anonymous"
        year_str = str(paper.year) if paper.year else "2025"
        return (
            f"@article{{{paper.id},\n"
            f"  title = {{{paper.title}}},\n"
            f"  author = {{{author_str}}},\n"
            f"  year = {{{year_str}}}\n"
            f"}}"
        )

    async def validate_citation_graph(self, citations: list[Citation]) -> bool:
        """Verify no self-citations or cycles."""
        for c in citations:
            if c.source_paper_id == c.target_paper_id:
                return False
        return True
