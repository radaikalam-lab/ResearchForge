"""Mock evidence provider."""

import uuid

from researchforge.domain.contracts.evidence import EvidenceProvider
from researchforge.domain.models.evidence import (
    Claim,
    Evidence,
    EvidenceFragment,
    EvidenceType,
)
from researchforge.domain.models.literature import Source
from researchforge.domain.value_objects.uncertainty import UncertaintyProfile


class MockEvidenceProvider(EvidenceProvider):
    """Mock implementation of EvidenceProvider."""

    provider_name: str = "mock-evidence-v1"

    async def extract_fragments(self, source: Source) -> list[EvidenceFragment]:
        """Extract mock evidence fragments from source content."""
        frag_id = f"frag_{uuid.uuid4().hex[:8]}"
        return [
            EvidenceFragment(
                id=frag_id,
                source_id=source.id,
                evidence_type=EvidenceType.TEXT,
                location_reference="Section 3, Paragraph 2",
                content=f"Empirical evidence extracted from {source.uri}: Effect magnitude exceeds threshold by 35%.",
                confidence=0.95,
                extraction_method="PARSER",
            )
        ]

    async def validate_extraction(self, fragment: EvidenceFragment, source: Source) -> bool:
        """Verify fragment is grounded in source."""
        return fragment.source_id == source.id

    async def synthesize_evidence(self, fragments: list[EvidenceFragment], claim: Claim) -> Evidence:
        """Synthesize multiple fragments into an Evidence entity."""
        evid_id = f"evid_{uuid.uuid4().hex[:8]}"
        return Evidence(
            id=evid_id,
            claim_ids=[claim.id],
            fragment_ids=[f.id for f in fragments],
            evidence_type=fragments[0].evidence_type if fragments else EvidenceType.TEXT,
            summary=f"Synthesized evidence from {len(fragments)} fragments supporting claim {claim.id}.",
            confidence=0.92,
            uncertainty=UncertaintyProfile(measurement_uncertainty=0.05, sampling_uncertainty=0.04),
            validation_status="VALIDATED",
        )
