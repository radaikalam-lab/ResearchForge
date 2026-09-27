"""Contract test for LiteratureProvider implementations."""

import pytest
from researchforge.domain.contracts.literature import LiteratureProvider
from researchforge.providers.literature.mock import MockLiteratureProvider


@pytest.mark.asyncio
async def test_literature_provider_contract_conformance() -> None:
    """Verify provider implements LiteratureProvider protocol."""
    provider: LiteratureProvider = MockLiteratureProvider()
    assert isinstance(provider, LiteratureProvider)
    assert provider.provider_name == "mock-literature-v1"

    sources = await provider.search("quantum annealing", limit=5)
    assert len(sources) > 0
    source = sources[0]
    assert source.id.startswith("src_")
    assert source.paper is not None
    assert "quantum annealing" in source.paper.title

    fetched = await provider.fetch(source.id)
    assert fetched is not None
    assert fetched.id == source.id

    citations = await provider.citations(source.paper.id)
    assert len(citations) > 0
    assert citations[0].target_paper_id == source.paper.id

    related = await provider.related(source.paper.id)
    assert len(related) > 0
