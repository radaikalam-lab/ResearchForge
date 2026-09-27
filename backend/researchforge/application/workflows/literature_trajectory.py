"""Phase 1 Literature & Evidence Intelligence end-to-end workflow service."""

import uuid
from pathlib import Path
from typing import Any

from researchforge.artifacts.evidence_bundle import EvidenceBundleGenerator
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
from researchforge.domain.models.project import ResearchProject, ResearchQuestion
from researchforge.domain.models.thread import ResearchThread
from researchforge.domain.state_machine import ResearchLifecycleState
from researchforge.persistence.database import DatabaseManager, get_db_manager
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.provenance.models import ProvenanceActor, ProvenanceEvent, ProvenanceEventType
from researchforge.provenance.tracker import ProvenanceTracker
from researchforge.providers.cognitia.adapter import CognitiaAdapter
from researchforge.providers.evidence.reference import ReferenceEvidenceExtractionProvider
from researchforge.providers.gap.reference import ReferenceGapAnalysisProvider
from researchforge.providers.literature.reference import ReferenceLiteratureProvider
from researchforge.providers.registry import ProviderRegistry, global_registry


class LiteratureTrajectoryExecutionResult:
    """The structured output bundle of a completed literature and evidence trajectory."""

    def __init__(
        self,
        project: ResearchProject,
        thread: ResearchThread,
        question: ResearchQuestion,
        sources: list[Source],
        evidence_items: list[Evidence],
        fragments: list[EvidenceFragment],
        claims: list[Claim],
        bindings: list[EvidenceClaimBinding],
        contradictions: list[PotentialContradiction],
        gaps: list[ResearchGap],
        hypotheses: list[Hypothesis],
        cognitia_critiques: list[Any],
        evidence_bundle_path: Path,
        evidence_bundle_hash: str,
        events: list[ProvenanceEvent],
    ) -> None:
        self.project = project
        self.thread = thread
        self.question = question
        self.sources = sources
        self.evidence_items = evidence_items
        self.fragments = fragments
        self.claims = claims
        self.bindings = bindings
        self.contradictions = contradictions
        self.gaps = gaps
        self.hypotheses = hypotheses
        self.cognitia_critiques = cognitia_critiques
        self.evidence_bundle_path = evidence_bundle_path
        self.evidence_bundle_hash = evidence_bundle_hash
        self.events = events


class LiteratureEvidenceWorkflowService:
    """Coordinates the deterministic Phase 1 research trajectory from literature ingestion to hypothesis."""

    def __init__(
        self,
        db_manager: DatabaseManager | None = None,
        registry: ProviderRegistry | None = None,
        artifacts_dir: Path | None = None,
    ) -> None:
        self.db_manager = db_manager or get_db_manager()
        self.registry = registry or global_registry
        self.artifacts_dir = artifacts_dir or Path("./artifacts")

        # Ensure default Phase 1 reference providers are available if not registered
        if not self.registry.has("literature_reference"):
            self.registry.register("literature_reference", ReferenceLiteratureProvider())
        if not self.registry.has("evidence_reference"):
            self.registry.register("evidence_reference", ReferenceEvidenceExtractionProvider())
        if not self.registry.has("gap_reference"):
            self.registry.register("gap_reference", ReferenceGapAnalysisProvider())

    async def execute_literature_trajectory(
        self,
        question_text: str = "What is the empirical effect of Parameter X on Response Y across low and high regimes?",
        primary_variable: str = "Parameter X",
        target_phenomenon: str = "Response Y",
        idempotency_key: str | None = None,
    ) -> LiteratureTrajectoryExecutionResult:
        """Execute full Phase 1 vertical slice:
        Question -> Literature -> Evidence -> Claims -> Contradictions -> Gaps -> Hypotheses -> Evidence Bundle.
        """
        with UnitOfWork(self.db_manager) as uow:
            tracker = ProvenanceTracker(uow.ledger)
            pid = f"proj_lit_{uuid.uuid4().hex[:8]}"
            tid = f"th_{uuid.uuid4().hex[:8]}"

            # 1. Project & Thread
            project = ResearchProject(
                id=pid,
                title=f"Literature Study: {target_phenomenon} vs {primary_variable}",
                state=ResearchLifecycleState.DRAFT,
            )
            thread = ResearchThread(
                id=tid,
                project_id=pid,
                title="Primary Literature Analysis Branch",
                state=ResearchLifecycleState.DRAFT,
            )
            uow.projects.save(project)
            uow.threads.save(thread)

            e_proj = tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id="system_orchestrator",
                operation=ProvenanceEventType.PROJECT_CREATED,
                entity_id=pid,
                entity_type="ResearchProject",
                parameters={"title": project.title},
            )
            uow.record_provenance(e_proj)

            # 2. Research Question
            qid = f"q_{uuid.uuid4().hex[:8]}"
            question = ResearchQuestion(
                id=qid,
                project_id=pid,
                question_text=question_text,
                primary_variable=primary_variable,
                target_phenomenon=target_phenomenon,
                scope_boundaries=["low regime [0.0, 2.0]", "high regime [2.0, 5.0]"],
            )
            uow.questions.save(question)
            project.state = ResearchLifecycleState.QUESTION_DEFINED
            uow.projects.save(project)

            e_q = tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id="system_orchestrator",
                operation=ProvenanceEventType.QUESTION_DEFINED,
                entity_id=qid,
                entity_type="ResearchQuestion",
                entity_refs=[pid],
                parameters={"question_text": question_text},
            )
            uow.record_provenance(e_q)

            # 3. Literature Ingestion
            lit_provider = (
                self.registry.get("literature_reference")
                if self.registry.has("literature_reference")
                else self.registry.get("literature")
            )
            sources = await lit_provider.search(primary_variable, limit=10)
            if not isinstance(sources, list):
                sources = sources.sources

            for src in sources:
                src.project_id = pid
                uow.sources.save(src)

                # Provenance: SOURCE_INGESTED & DOCUMENT_NORMALIZED
                e_src = tracker.track(
                    actor=ProvenanceActor.RESEARCHFORGE,
                    actor_id=lit_provider.provider_name,
                    operation=ProvenanceEventType.SOURCE_INGESTED,
                    entity_id=src.id,
                    entity_type="Source",
                    entity_refs=[pid, qid],
                    parameters={"uri": src.uri, "provider_record_id": src.provider_record_id},
                )
                uow.record_provenance(e_src)

                e_norm = tracker.track(
                    actor=ProvenanceActor.RESEARCHFORGE,
                    actor_id=lit_provider.provider_name,
                    operation=ProvenanceEventType.DOCUMENT_NORMALIZED,
                    entity_id=src.id,
                    entity_type="Source",
                    entity_refs=[src.id],
                    parameters={"content_hash": src.raw_content_hash, "metadata_hash": src.metadata_hash},
                )
                uow.record_provenance(e_norm)

            # 4. Evidence & Claim Extraction
            ev_provider = (
                self.registry.get("evidence_reference")
                if self.registry.has("evidence_reference")
                else ReferenceEvidenceExtractionProvider()
            )

            all_fragments: list[EvidenceFragment] = []
            all_claims: list[Claim] = []
            all_evidence: list[Evidence] = []
            all_bindings: list[EvidenceClaimBinding] = []

            for src in sources:
                frags = await ev_provider.extract_fragments(src)
                all_fragments.extend(frags)

                claims = await ev_provider.extract_candidate_claims(src, frags)
                for c in claims:
                    c.project_id = pid
                    uow.claims.save(c)
                    all_claims.append(c)

                    # Provenance: CLAIM_CREATED
                    e_claim = tracker.track(
                        actor=ProvenanceActor.RESEARCHFORGE,
                        actor_id=ev_provider.provider_name,
                        operation=ProvenanceEventType.CLAIM_CREATED,
                        entity_id=c.id,
                        entity_type="Claim",
                        entity_refs=[src.id],
                        parameters={"statement": c.statement, "claim_type": str(c.claim_type)},
                    )
                    uow.record_provenance(e_claim)

                # Synthesize Evidence for primary claim
                if claims:
                    ev = await ev_provider.synthesize_evidence(frags, claims[0])
                    ev.project_id = pid
                    uow.evidence.save(ev)
                    all_evidence.append(ev)

                    # Explicit Claim-Evidence Bindings
                    bindings = ev_provider.create_bindings(pid, claims, frags, ev.id)
                    for b in bindings:
                        uow.bindings.save(b)
                        all_bindings.append(b)

                        e_bind = tracker.track(
                            actor=ProvenanceActor.RESEARCHFORGE,
                            actor_id=ev_provider.provider_name,
                            operation=ProvenanceEventType.CLAIM_BOUND,
                            entity_id=b.id,
                            entity_type="EvidenceClaimBinding",
                            entity_refs=[ev.id, b.claim_id, b.source_id],
                            parameters={"binding_type": b.binding_type},
                        )
                        uow.record_provenance(e_bind)

                    e_ev = tracker.track(
                        actor=ProvenanceActor.RESEARCHFORGE,
                        actor_id=ev_provider.provider_name,
                        operation=ProvenanceEventType.EVIDENCE_EXTRACTED,
                        entity_id=ev.id,
                        entity_type="Evidence",
                        entity_refs=[src.id, claims[0].id],
                        parameters={"summary": ev.summary, "fragment_count": len(frags)},
                    )
                    uow.record_provenance(e_ev)

            project.state = ResearchLifecycleState.EVIDENCE_STRUCTURED
            uow.projects.save(project)

            # 5. Contradiction Detection
            contradictions = ev_provider.detect_contradictions(pid, all_claims)
            for con in contradictions:
                uow.contradictions.save(con)
                e_con = tracker.track(
                    actor=ProvenanceActor.RESEARCHFORGE,
                    actor_id=ev_provider.provider_name,
                    operation=ProvenanceEventType.CONTRADICTION_IDENTIFIED,
                    entity_id=con.id,
                    entity_type="PotentialContradiction",
                    entity_refs=[con.claim_a_id, con.claim_b_id],
                    parameters={"contradiction_type": con.contradiction_type, "description": con.description},
                )
                uow.record_provenance(e_con)

            # 6. Research Gap Analysis
            gap_provider = (
                self.registry.get("gap_reference")
                if self.registry.has("gap_reference")
                else ReferenceGapAnalysisProvider()
            )
            gap_candidates = await gap_provider.analyze_gaps(all_evidence, all_claims, contradictions)

            verified_gaps: list[ResearchGap] = []
            for cand in gap_candidates:
                gap = await gap_provider.evaluate_gap_validity(cand, all_evidence)
                if gap:
                    gap.project_id = pid
                    uow.gaps.save(gap)
                    verified_gaps.append(gap)

                    e_gap = tracker.track(
                        actor=ProvenanceActor.RESEARCHFORGE,
                        actor_id=gap_provider.provider_name,
                        operation=ProvenanceEventType.GAP_IDENTIFIED,
                        entity_id=gap.id,
                        entity_type="ResearchGap",
                        entity_refs=[e.id for e in all_evidence],
                        parameters={"gap_type": str(gap.gap_type), "description": gap.description},
                    )
                    uow.record_provenance(e_gap)

            project.state = ResearchLifecycleState.GAP_ANALYSIS
            uow.projects.save(project)

            # 7. Hypothesis Candidate Formulation
            hypotheses: list[Hypothesis] = []
            if verified_gaps:
                primary_gap = verified_gaps[0]
                hyp = gap_provider.propose_hypothesis_candidate(primary_gap, pid)
                uow.hypotheses.save(hyp)
                hypotheses.append(hyp)

                thread.hypothesis_id = hyp.id
                uow.threads.save(thread)

                e_hyp = tracker.track(
                    actor=ProvenanceActor.RESEARCHFORGE,
                    actor_id=gap_provider.provider_name,
                    operation=ProvenanceEventType.HYPOTHESIS_GENERATED,
                    entity_id=hyp.id,
                    entity_type="Hypothesis",
                    entity_refs=[primary_gap.id],
                    parameters={"statement": hyp.statement, "mechanism": hyp.mechanism},
                )
                uow.record_provenance(e_hyp)

            project.state = ResearchLifecycleState.HYPOTHESIS_FORMED
            uow.projects.save(project)

            # 8. Advisory Cognitia Critique
            cognitia_adapter = CognitiaAdapter()
            cognitia_critiques = []
            if hypotheses:
                critique = await cognitia_adapter.evaluate_hypothesis(hypotheses[0])
                cognitia_critiques.append(critique)

            # 9. Artifact Generation: research_evidence_bundle.json
            bundle_gen = EvidenceBundleGenerator(
                project_id=pid,
                question=question,
                sources=sources,
                evidence_items=all_evidence,
                fragments=all_fragments,
                claims=all_claims,
                bindings=all_bindings,
                contradictions=contradictions,
                gaps=verified_gaps,
                hypotheses=hypotheses,
                provenance_head=uow.ledger.get_head_hash() if uow.ledger else "",
            )
            bundle_dir = self.artifacts_dir / pid
            bundle_path, bundle_hash = bundle_gen.save_bundle(bundle_dir)

            e_art = tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id="system_orchestrator",
                operation=ProvenanceEventType.ARTIFACT_GENERATED,
                entity_id=f"art_ev_{pid[:8]}",
                entity_type="ResearchArtifact",
                entity_refs=[pid],
                parameters={"bundle_path": str(bundle_path), "content_hash": bundle_hash},
            )
            uow.record_provenance(e_art)

            # Record Idempotency if key supplied
            if idempotency_key and uow.idempotency:
                uow.idempotency.save_record(
                    key=idempotency_key,
                    operation="execute_literature_trajectory",
                    entity_id=pid,
                    response_payload={"project_id": pid, "bundle_hash": bundle_hash},
                )

            all_events = uow.provenance_repo.list_all() if uow.provenance_repo else []

            return LiteratureTrajectoryExecutionResult(
                project=project,
                thread=thread,
                question=question,
                sources=sources,
                evidence_items=all_evidence,
                fragments=all_fragments,
                claims=all_claims,
                bindings=all_bindings,
                contradictions=contradictions,
                gaps=verified_gaps,
                hypotheses=hypotheses,
                cognitia_critiques=cognitia_critiques,
                evidence_bundle_path=bundle_path,
                evidence_bundle_hash=bundle_hash,
                events=all_events,
            )
