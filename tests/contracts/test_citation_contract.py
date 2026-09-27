"""Contract test for CitationProvider implementations."""

import pytest
from researchforge.domain.contracts.citation import CitationProvider
from researchforge.domain.models.literature import Citation
from researchforge.providers.citation.mock import MockCitationProvider


@pytest.mark.asyncio
async def test_citation_provider_contract_conformance() -> None:
    """Verify provider implements CitationProvider protocol."""
    provider: CitationProvider = MockCitationProvider()
    assert isinstance(provider, CitationProvider)

    paper = await provider.resolve_doi("10.1038/nature12345")
    assert paper is not None
    assert paper.doi == "10.1038/nature12345"

    bibtex = await provider.format_bibtex(paper)
    assert bibtex.startswith("@article")
    assert paper.title in bibtex

    valid_cites = [
        Citation(id="c1", source_paper_id="p1", target_paper_id="p2"),
        Citation(id="c2", source_paper_id="p2", target_paper_id="p3"),
    ]
    assert await provider.validate_citation_graph(valid_cites) is True

    invalid_cites = [
        Citation(id="c1", source_paper_id="p1", target_paper_id="p1"),
    ]
    assert await provider.validate_citation_graph(invalid_cites) is False
