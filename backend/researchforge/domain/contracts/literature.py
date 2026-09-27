"""Literature provider protocol contract with typed DTO signatures (Section 28)."""

from typing import Protocol, runtime_checkable

from researchforge.domain.models.literature import Citation, Paper, Source
from researchforge.domain.schemas.dtos import (
    LiteratureCitationRequest,
    LiteratureFetchRequest,
    LiteratureRelatedRequest,
    LiteratureSearchRequest,
    LiteratureSearchResponse,
)


@runtime_checkable
class LiteratureProvider(Protocol):
    """Contract for scholarly search and bibliographic retrieval engines."""

    provider_name: str

    async def search(
        self,
        query_or_request: str | LiteratureSearchRequest,
        limit: int = 10,
    ) -> list[Source] | LiteratureSearchResponse:
        """Search scholarly literature and return Source domain records."""
        ...

    async def fetch(
        self,
        record_id_or_request: str | LiteratureFetchRequest,
    ) -> Source | None:
        """Fetch a specific source by its provider record ID."""
        ...

    async def citations(
        self,
        paper_id_or_request: str | LiteratureCitationRequest,
    ) -> list[Citation]:
        """Retrieve downstream citations referencing the target paper."""
        ...

    async def related(
        self,
        paper_id_or_request: str | LiteratureRelatedRequest,
        limit: int = 5,
    ) -> list[Paper]:
        """Retrieve related papers based on bibliographic coupling or co-citation."""
        ...
