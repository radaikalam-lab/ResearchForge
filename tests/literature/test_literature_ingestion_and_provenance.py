"""Tests for literature ingestion, source identity determinism, and provenance tracking (Phase 1)."""

from pathlib import Path

import pytest
from researchforge.domain.models.literature import compute_source_identity
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.provenance.models import ProvenanceEvent, ProvenanceEventType
from researchforge.providers.literature.openalex import OpenAlexLiteratureProvider
from researchforge.providers.literature.reference import ReferenceLiteratureProvider


@pytest.mark.asyncio
async def test_reference_literature_source_determinism() -> None:
    """Validate that ReferenceLiteratureProvider returns deterministic sources with stable SHA-256 hashes."""
    provider = ReferenceLiteratureProvider()
    sources = await provider.search("parameter_x", limit=10)

    assert len(sources) == 4
    # All sources must be clearly labeled synthetic
    for s in sources:
        assert "[SYNTHETIC REFERENCE LITERATURE]" in s.title
        assert s.raw_content_hash != ""
        assert s.metadata_hash != ""
        assert s.id == compute_source_identity(provider.provider_name, s.provider_record_id)


@pytest.mark.asyncio
async def test_idempotent_source_ingestion(tmp_path: Path) -> None:
    """Validate that repeated ingestion of identical source does not create duplicates or corrupt hashes."""
    db_file = tmp_path / "lit_ingest.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    provider = ReferenceLiteratureProvider()
    sources = await provider.search("parameter_x", limit=1)
    target_source = sources[0]

    with UnitOfWork(db_mgr) as uow:
        uow.sources.save(target_source)
        e1 = ProvenanceEvent(
            event_id="prov_src_01",
            event_type=ProvenanceEventType.SOURCE_INGESTED,
            entity_id=target_source.id,
            entity_type="Source",
        )
        uow.record_provenance(e1)

    # Re-save identical source
    with UnitOfWork(db_mgr) as uow:
        retrieved = uow.sources.get(target_source.id)
        assert retrieved is not None
        assert retrieved.raw_content_hash == target_source.raw_content_hash
        assert retrieved.metadata_hash == target_source.metadata_hash

        # Second save must update existing record cleanly
        uow.sources.save(target_source)
        assert len(uow.sources.list_by_project(target_source.project_id)) == 1


@pytest.mark.asyncio
async def test_openalex_provider_offline_fallback() -> None:
    """Validate OpenAlex provider returns normalized schema records in offline/fallback mode."""
    provider = OpenAlexLiteratureProvider(timeout_sec=0.1)
    sources = await provider.search("synthetic parameter x", limit=2)

    assert len(sources) >= 1
    s = sources[0]
    assert s.source_type == "SCHOLARLY_PAPER"
    assert s.provider_name == "openalex-literature-v1"
    assert s.raw_content_hash != ""
