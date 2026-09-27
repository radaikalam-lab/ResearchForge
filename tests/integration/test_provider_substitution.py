"""Tests demonstrating provider substitution across trajectories without domain contract changes (Workstream R)."""

from pathlib import Path
from typing import Any

import pytest
from researchforge.application.workflows.trajectory import ResearchTrajectoryService
from researchforge.domain.contracts.evidence import EvidenceProvider
from researchforge.domain.contracts.literature import LiteratureProvider
from researchforge.domain.models.evidence import Claim, Evidence, EvidenceFragment, EvidenceType
from researchforge.domain.models.literature import Source
from researchforge.domain.state_machine import ResearchLifecycleState
from researchforge.persistence.database import DatabaseManager
from researchforge.providers.registry import ProviderRegistry, global_registry


class AlternativeLiteratureProvider(LiteratureProvider):
    """Alternative literature provider implementation returning standardized synthetic records."""

    provider_name: str = "alternative-literature-mock-v2"

    async def search(self, query: str, limit: int = 10) -> list[Source]:
        return [
            Source(
                id="src_alt_01",
                uri="https://alt.scholar.org/paper-01",
                provider_name=self.provider_name,
                provider_record_id="rec_alt_01",
                retrieved_content="Alternative literature source evaluating parameter X in range [0, 2].",
            )
        ]

    async def fetch_metadata(self, source_id: str) -> dict[str, Any]:
        return {"source_id": source_id, "provider": self.provider_name}


class AlternativeEvidenceProvider(EvidenceProvider):
    """Alternative evidence extraction provider returning standardized synthesized evidence."""

    provider_name: str = "alternative-evidence-mock-v2"

    async def extract_fragments(self, source: Source) -> list[EvidenceFragment]:
        return [
            EvidenceFragment(
                id="frag_alt_01",
                source_id=source.id,
                evidence_type=EvidenceType.TEXT,
                location_reference="Section 3.1",
                content="Monotonic positive response observed for parameter X.",
                confidence=0.92,
            )
        ]

    async def synthesize_evidence(self, fragments: list[EvidenceFragment], claim: Claim) -> Evidence:
        return Evidence(
            id="ev_alt_01",
            source_id=fragments[0].source_id if fragments else "src_alt_01",
            summary="Synthesized alternative baseline evidence.",
            fragments=fragments,
            claim_ids=[claim.id],
            claims=[claim.statement],
        )


@pytest.mark.asyncio
async def test_provider_substitution_trajectory(tmp_path: Path) -> None:
    """Prove that substituting Literature and Evidence providers preserves identical domain contracts."""
    db_file = tmp_path / "alt_trajectory.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Configure custom registry with substituted providers
    custom_registry = ProviderRegistry()
    for k, v in global_registry._providers.items():
        custom_registry.register(k, v)
    custom_registry.register("literature", AlternativeLiteratureProvider())
    custom_registry.register("evidence", AlternativeEvidenceProvider())

    service = ResearchTrajectoryService(
        db_manager=db_mgr,
        artifacts_dir=artifacts_dir,
        registry=custom_registry,
    )

    res = await service.execute_reference_trajectory(
        title="Substituted Provider Trajectory Study",
        seed=101,
        secret_key="dev_alt_key",
    )

    # Verify trajectory completed with full domain contract fidelity
    assert res.project.state == ResearchLifecycleState.PUBLISHABLE_ARTIFACT
    assert res.conclusion.is_validated is True
    assert res.falsification.status.value == "SUPPORTED"
    assert res.run.status == "COMPLETED"
    assert Path(res.artifact.file_path).exists()
