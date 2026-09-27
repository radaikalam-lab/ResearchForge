"""Artifact generator for structured Phase 1 Research Evidence Bundles."""

import hashlib
import json
from pathlib import Path
from typing import Any

from researchforge.domain.base import canonical_json_dumps, current_iso_timestamp
from researchforge.domain.models.evidence import (
    Claim,
    Evidence,
    EvidenceClaimBinding,
    EvidenceFragment,
    PotentialContradiction,
)
from researchforge.domain.models.gap import ResearchGap
from researchforge.domain.models.hypothesis import Hypothesis
from researchforge.domain.models.literature import Source
from researchforge.domain.models.project import ResearchQuestion


class EvidenceBundleGenerator:
    """Produces canonical, machine-verifiable research_evidence_bundle.json artifacts."""

    def __init__(
        self,
        project_id: str,
        question: ResearchQuestion,
        sources: list[Source],
        evidence_items: list[Evidence],
        fragments: list[EvidenceFragment],
        claims: list[Claim],
        bindings: list[EvidenceClaimBinding],
        contradictions: list[PotentialContradiction],
        gaps: list[ResearchGap],
        hypotheses: list[Hypothesis],
        provenance_head: str = "",
    ) -> None:
        self.project_id = project_id
        self.question = question
        self.sources = sources
        self.evidence_items = evidence_items
        self.fragments = fragments
        self.claims = claims
        self.bindings = bindings
        self.contradictions = contradictions
        self.gaps = gaps
        self.hypotheses = hypotheses
        self.provenance_head = provenance_head

    def to_dict(self) -> dict[str, Any]:
        """Construct deterministic dictionary payload."""
        data = {
            "schema_version": "1.0.0",
            "artifact_type": "RESEARCH_EVIDENCE_BUNDLE",
            "project_id": self.project_id,
            "generated_at": current_iso_timestamp(),
            "research_question": self.question.model_dump(mode="json"),
            "sources": [s.model_dump(mode="json") for s in self.sources],
            "evidence_items": [e.model_dump(mode="json") for e in self.evidence_items],
            "evidence_fragments": [f.model_dump(mode="json") for f in self.fragments],
            "claims": [c.model_dump(mode="json") for c in self.claims],
            "claim_evidence_bindings": [b.model_dump(mode="json") for b in self.bindings],
            "contradictions": [con.model_dump(mode="json") for con in self.contradictions],
            "research_gaps": [g.model_dump(mode="json") for g in self.gaps],
            "hypotheses": [h.model_dump(mode="json") for h in self.hypotheses],
            "provenance_head": self.provenance_head,
        }
        # Compute artifact integrity hash over canonical representation
        data_to_hash = dict(data)
        data_to_hash.pop("generated_at", None)
        canonical_str = canonical_json_dumps(data_to_hash)
        content_hash = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
        data["content_hash"] = content_hash
        return data

    def save_bundle(self, output_dir: Path) -> tuple[Path, str]:
        """Save research_evidence_bundle.json to output directory and return path and content hash."""
        output_dir.mkdir(parents=True, exist_ok=True)
        bundle_data = self.to_dict()
        file_path = output_dir / "research_evidence_bundle.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(bundle_data, f, indent=2)
        return file_path, bundle_data["content_hash"]
