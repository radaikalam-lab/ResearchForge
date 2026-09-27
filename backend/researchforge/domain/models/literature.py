"""Scholarly literature, source, and citation models."""

import hashlib
from typing import Any

from pydantic import Field

from researchforge.domain.base import DomainModel, canonical_json_dumps, current_iso_timestamp


def compute_source_identity(provider_name: str, provider_record_id: str) -> str:
    """Deterministic source ID derived from provider name and provider record ID."""
    clean_key = f"{provider_name.strip().lower()}:{provider_record_id.strip()}"
    digest = hashlib.sha256(clean_key.encode("utf-8")).hexdigest()[:16]
    return f"src_{digest}"


class Citation(DomainModel):
    """Citation link between papers or claims."""

    source_paper_id: str
    target_paper_id: str
    raw_citation_text: str | None = None
    citation_intent: str = "BACKGROUND"  # BACKGROUND, METHOD, RESULT, CONTRADICTION, EXTENSION
    is_influential: bool = False


class Paper(DomainModel):
    """Normalized scholarly paper record."""

    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: str = ""
    year: int | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    openalex_id: str | None = None
    venue: str | None = None
    journal_name: str | None = None
    citation_count: int = 0
    reference_ids: list[str] = Field(default_factory=list)
    pdf_hash: str | None = None
    raw_content_hash: str = ""
    metadata_hash: str = ""
    raw_payload: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.raw_content_hash and self.abstract:
            self.raw_content_hash = hashlib.sha256(self.abstract.encode("utf-8")).hexdigest()
        if not self.metadata_hash:
            meta = {
                "title": self.title,
                "authors": sorted(self.authors),
                "year": self.year,
                "doi": self.doi,
            }
            self.metadata_hash = hashlib.sha256(canonical_json_dumps(meta).encode("utf-8")).hexdigest()


class Source(DomainModel):
    """External or ingested scientific information source."""

    project_id: str = ""
    title: str = ""
    source_type: str = "SCHOLARLY_PAPER"  # SCHOLARLY_PAPER, DATASET, REPO, REPORT, MANUAL_ENTRY
    uri: str
    provider_name: str
    provider_record_id: str
    retrieval_query: str = ""
    retrieved_content: str = ""
    raw_content_hash: str = ""
    metadata_hash: str = ""
    retrieval_timestamp: str = Field(default_factory=current_iso_timestamp)
    provider_version: str = "1.0.0"
    normalization_version: str = "1.0.0"
    paper: Paper | None = None

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = compute_source_identity(self.provider_name, self.provider_record_id)
        if not self.title and self.paper:
            self.title = self.paper.title
        if not self.raw_content_hash:
            raw = self.retrieved_content or (self.paper.abstract if self.paper else "")
            self.raw_content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        if not self.metadata_hash:
            meta = {
                "uri": self.uri,
                "provider_name": self.provider_name,
                "provider_record_id": self.provider_record_id,
                "source_type": self.source_type,
            }
            self.metadata_hash = hashlib.sha256(canonical_json_dumps(meta).encode("utf-8")).hexdigest()
