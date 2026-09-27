"""Mock publication provider."""

import hashlib
import uuid

from researchforge.domain.contracts.publication import PublicationProvider
from researchforge.domain.models.artifact import (
    ArtifactType,
    Manuscript,
    ResearchArtifact,
)


class MockPublicationProvider(PublicationProvider):
    """Mock implementation of PublicationProvider."""

    provider_name: str = "mock-publication-v1"

    async def render_manuscript(self, manuscript: Manuscript, format_type: str = "MARKDOWN") -> ResearchArtifact:
        """Render manuscript into markdown artifact."""
        body = f"# {manuscript.title}\n\n## Abstract\n{manuscript.abstract}\n\n"
        for section in manuscript.sections:
            body += f"## {section.title}\n{section.content}\n\n"

        content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        art_id = f"art_{uuid.uuid4().hex[:8]}"

        return ResearchArtifact(
            id=art_id,
            project_id=manuscript.project_id,
            name=f"{manuscript.title.lower().replace(' ', '_')}.md",
            artifact_type=ArtifactType.MANUSCRIPT_MARKDOWN,
            file_path=f"./artifacts/{manuscript.project_id}/manuscript.md",
            content_sha256=content_hash,
            metadata={"format": format_type, "sections_count": len(manuscript.sections)},
        )

    async def build_reproducibility_bundle(self, project_id: str, artifact_ids: list[str]) -> ResearchArtifact:
        """Create reproducibility bundle archive representation."""
        bundle_hash = hashlib.sha256(f"bundle_{project_id}_{len(artifact_ids)}".encode()).hexdigest()
        return ResearchArtifact(
            id=f"bundle_{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            name=f"reproducibility_bundle_{project_id}.zip",
            artifact_type=ArtifactType.REPRODUCIBILITY_BUNDLE_ZIP,
            file_path=f"./artifacts/{project_id}/bundle.zip",
            content_sha256=bundle_hash,
            metadata={"bundled_artifact_count": len(artifact_ids)},
        )

    async def verify_traceability(self, manuscript: Manuscript) -> tuple[bool, list[str]]:
        """Verify claim grounding and citation completeness."""
        unresolved = []
        for section in manuscript.sections:
            if (
                not section.is_interpretation
                and not section.referenced_claim_ids
                and not section.referenced_evidence_ids
            ):
                if section.section_type in {"RESULTS", "CONCLUSION"}:
                    unresolved.append(f"Section '{section.title}' lacks evidence links.")
        return len(unresolved) == 0, unresolved
