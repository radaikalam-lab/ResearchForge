"""Evidence provider protocol contract."""

from typing import Protocol, runtime_checkable

from researchforge.domain.models.evidence import Claim, Evidence, EvidenceFragment
from researchforge.domain.models.literature import Source


@runtime_checkable
class EvidenceProvider(Protocol):
    """Contract for extracting, structuring, and validating evidence fragments."""

    provider_name: str

    async def extract_fragments(self, source: Source) -> list[EvidenceFragment]:
        """Extract atomic evidence fragments (text, tables, figures, equations) from a source."""
        ...

    async def validate_extraction(self, fragment: EvidenceFragment, source: Source) -> bool:
        """Verify that a fragment is truthfully grounded in the parent source content."""
        ...

    async def synthesize_evidence(self, fragments: list[EvidenceFragment], claim: Claim) -> Evidence:
        """Synthesize multiple fragments into a structured Evidence entity for a claim."""
        ...
