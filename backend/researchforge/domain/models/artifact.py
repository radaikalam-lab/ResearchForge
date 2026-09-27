"""Reproducible research artifacts, manuscripts, figures, and tables."""

from enum import StrEnum
from typing import Any

from pydantic import Field

from researchforge.domain.base import DomainModel


class ArtifactType(StrEnum):
    """Types of generated research artifacts."""

    MANUSCRIPT_MARKDOWN = "MANUSCRIPT_MARKDOWN"
    MANUSCRIPT_QUARTO = "MANUSCRIPT_QUARTO"
    MANUSCRIPT_LATEX = "MANUSCRIPT_LATEX"
    MANUSCRIPT_PDF = "MANUSCRIPT_PDF"
    MANUSCRIPT_JSON = "MANUSCRIPT_JSON"
    FIGURE_PNG = "FIGURE_PNG"
    FIGURE_SVG = "FIGURE_SVG"
    TABLE_CSV = "TABLE_CSV"
    REPRODUCIBILITY_BUNDLE_ZIP = "REPRODUCIBILITY_BUNDLE_ZIP"
    DATASET_PARQUET = "DATASET_PARQUET"
    PROVENANCE_LEDGER = "PROVENANCE_LEDGER"


class Figure(DomainModel):
    """Reproducible figure generated from experiment or simulation run."""

    title: str
    caption: str
    file_path: str
    file_hash: str
    source_run_id: str
    generation_script_hash: str


class Table(DomainModel):
    """Reproducible data table."""

    title: str
    caption: str
    columns: list[str] = Field(default_factory=list)
    row_count: int = 0
    file_path: str
    file_hash: str
    source_analysis_id: str


class ManuscriptSection(DomainModel):
    """Section of a scientific manuscript with claim and evidence links."""

    title: str
    content: str
    section_type: str = "INTRODUCTION"  # INTRODUCTION, METHODS, RESULTS, DISCUSSION, CONCLUSION
    referenced_claim_ids: list[str] = Field(default_factory=list)
    referenced_evidence_ids: list[str] = Field(default_factory=list)
    referenced_figure_ids: list[str] = Field(default_factory=list)
    referenced_table_ids: list[str] = Field(default_factory=list)
    is_interpretation: bool = False  # If True, explicitly marked as speculative/interpretive


class Manuscript(DomainModel):
    """Complete scientific manuscript container."""

    project_id: str
    title: str
    abstract: str
    authors: list[str] = Field(default_factory=list)
    sections: list[ManuscriptSection] = Field(default_factory=list)
    bibtex_references: list[str] = Field(default_factory=list)
    traceability_verified: bool = False


class ResearchArtifact(DomainModel):
    """Versioned and content-addressed research deliverable."""

    project_id: str
    name: str
    artifact_type: ArtifactType
    file_path: str
    content_sha256: str
    status: str = "VALID"
    upstream_artifact_ids: list[str] = Field(default_factory=list)
    upstream_dataset_hashes: list[str] = Field(default_factory=list)
    upstream_code_hash: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
