"""Mock literature provider for offline testing."""

import uuid

from researchforge.domain.contracts.literature import LiteratureProvider
from researchforge.domain.models.literature import Citation, Paper, Source
from researchforge.domain.schemas.dtos import (
    LiteratureCitationRequest,
    LiteratureFetchRequest,
    LiteratureRelatedRequest,
    LiteratureSearchRequest,
    LiteratureSearchResponse,
)


class MockLiteratureProvider(LiteratureProvider):
    """Reference offline implementation of LiteratureProvider."""

    provider_name: str = "mock-literature-v1"

    def __init__(self) -> None:
        self._sources: list[Source] = []

    async def search(
        self,
        query_or_request: str | LiteratureSearchRequest,
        limit: int = 10,
    ) -> list[Source] | LiteratureSearchResponse:
        """Return deterministic mock sources matching query."""
        if isinstance(query_or_request, LiteratureSearchRequest):
            query = query_or_request.query
            limit = query_or_request.limit
            is_dto = True
        else:
            query = str(query_or_request)
            is_dto = False

        source_id = f"src_{uuid.uuid4().hex[:8]}"
        paper = Paper(
            id=f"paper_{uuid.uuid4().hex[:8]}",
            title=f"Investigation into {query}",
            authors=["Alice Researcher", "Bob Scientist"],
            abstract=f"An empirical exploration of phenomena related to {query}.",
            year=2025,
            doi="10.1000/mock.doi.123",
            journal_name="Journal of Computational Discovery",
            citation_count=42,
        )
        source = Source(
            id=source_id,
            source_type="SCHOLARLY_PAPER",
            uri=f"https://doi.org/{paper.doi}",
            provider_name=self.provider_name,
            provider_record_id=f"rec_{paper.id}",
            retrieval_query=query,
            retrieved_content=paper.abstract,
            paper=paper,
        )
        self._sources.append(source)
        res_sources = [source][:limit]

        if is_dto:
            return LiteratureSearchResponse(
                sources=res_sources,
                total_found=len(res_sources),
                provider_name=self.provider_name,
                query_hash=source.content_hash(),
            )
        return res_sources

    async def fetch(
        self,
        record_id_or_request: str | LiteratureFetchRequest,
    ) -> Source | None:
        """Fetch source by record ID."""
        record_id = (
            record_id_or_request.record_id
            if isinstance(record_id_or_request, LiteratureFetchRequest)
            else str(record_id_or_request)
        )
        for s in self._sources:
            if s.provider_record_id == record_id or s.id == record_id:
                return s
        return None

    async def citations(
        self,
        paper_id_or_request: str | LiteratureCitationRequest,
    ) -> list[Citation]:
        """Return citations for paper."""
        paper_id = (
            paper_id_or_request.paper_id
            if isinstance(paper_id_or_request, LiteratureCitationRequest)
            else str(paper_id_or_request)
        )
        return [
            Citation(
                id=f"cite_{uuid.uuid4().hex[:8]}",
                source_paper_id=f"paper_{uuid.uuid4().hex[:8]}",
                target_paper_id=paper_id,
                citation_intent="BACKGROUND",
                is_influential=True,
            )
        ]

    async def related(
        self,
        paper_id_or_request: str | LiteratureRelatedRequest,
        limit: int = 5,
    ) -> list[Paper]:
        """Return related papers."""
        paper_id = (
            paper_id_or_request.paper_id
            if isinstance(paper_id_or_request, LiteratureRelatedRequest)
            else str(paper_id_or_request)
        )
        return [
            Paper(
                id=f"paper_{uuid.uuid4().hex[:8]}",
                title=f"Related Work to {paper_id}",
                authors=["Carol Investigator"],
                year=2024,
            )
        ]
