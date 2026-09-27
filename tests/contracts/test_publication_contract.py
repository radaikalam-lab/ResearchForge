"""Contract test for PublicationProvider implementations."""

import pytest
from researchforge.domain.contracts.publication import PublicationProvider
from researchforge.domain.models.artifact import (
    ArtifactType,
    Manuscript,
    ManuscriptSection,
)
from researchforge.providers.publication.mock import MockPublicationProvider


@pytest.mark.asyncio
async def test_publication_provider_contract_conformance() -> None:
    """Verify provider implements PublicationProvider protocol."""
    provider: PublicationProvider = MockPublicationProvider()
    assert isinstance(provider, PublicationProvider)

    section = ManuscriptSection(
        id="sec_1",
        title="Results",
        content="The hypothesis was supported by p < 0.01.",
        section_type="RESULTS",
        referenced_claim_ids=["claim_01"],
        referenced_evidence_ids=["evid_01"],
    )
    manuscript = Manuscript(
        id="ms_1",
        project_id="proj_1",
        title="Lattice Dynamics under High Pressure",
        abstract="A study on lattice deformations.",
        sections=[section],
    )

    art = await provider.render_manuscript(manuscript, format_type="MARKDOWN")
    assert art.artifact_type == ArtifactType.MANUSCRIPT_MARKDOWN
    assert art.content_sha256 != ""

    bundle = await provider.build_reproducibility_bundle("proj_1", [art.id])
    assert bundle.artifact_type == ArtifactType.REPRODUCIBILITY_BUNDLE_ZIP

    is_traceable, issues = await provider.verify_traceability(manuscript)
    assert is_traceable is True
    assert len(issues) == 0
