"""Publication provider protocol contract."""

from typing import Protocol, runtime_checkable

from researchforge.domain.models.artifact import Manuscript, ResearchArtifact


@runtime_checkable
class PublicationProvider(Protocol):
    """Contract for rendering manuscripts, checking traceability, and packaging bundles."""

    provider_name: str

    async def render_manuscript(self, manuscript: Manuscript, format_type: str = "MARKDOWN") -> ResearchArtifact:
        """Render manuscript into Markdown, Quarto, LaTeX, or PDF artifact."""
        ...

    async def build_reproducibility_bundle(self, project_id: str, artifact_ids: list[str]) -> ResearchArtifact:
        """Package code, environment, seeds, datasets, and provenance into reproducible ZIP archive."""
        ...

    async def verify_traceability(self, manuscript: Manuscript) -> tuple[bool, list[str]]:
        """Verify that every section claim links to valid evidence, tables, or figures."""
        ...
