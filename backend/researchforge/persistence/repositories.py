"""Typed repository implementations for database persistence."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from researchforge.domain.crypto import compute_content_sha256
from researchforge.domain.models.artifact import ArtifactType, ResearchArtifact
from researchforge.domain.models.computation_plan import ComputationPlan
from researchforge.domain.models.conclusion import Conclusion, HumanDecision
from researchforge.domain.models.evidence import (
    Claim,
    Evidence,
    EvidenceClaimBinding,
    EvidenceFragment,
    PotentialContradiction,
)
from researchforge.domain.models.experiment import Experiment, ExperimentPlan, ExperimentResult, ExperimentRun
from researchforge.domain.models.experiment_design import ExperimentDesign
from researchforge.domain.models.experimental_design_candidate import (
    CandidateDesignEvaluation,
    DesignCandidateStatus,
    DesignObjective,
    DiscriminationMetric,
    ExperimentalDesignCandidate,
    ParetoCandidateSet,
    ResourceRequirements,
)
from researchforge.domain.models.falsification import FalsificationEvaluation, FalsificationStatus
from researchforge.domain.models.gap import ResearchGap
from researchforge.domain.models.hypothesis import FalsificationCriterion, Hypothesis
from researchforge.domain.models.literature import Paper, Source
from researchforge.domain.models.parameter_space import ParameterSpace
from researchforge.domain.models.project import ResearchProject, ResearchQuestion
from researchforge.domain.models.thread import ResearchThread
from researchforge.domain.state_machine import HypothesisLifecycleState, ResearchLifecycleState
from researchforge.persistence.exceptions import IdempotencyConflict, OptimisticConcurrencyError
from researchforge.persistence.models import (
    ArtifactRecord,
    CandidateDesignEvaluationRecord,
    ClaimRecord,
    ConclusionRecord,
    ContradictionRecord,
    EvidenceClaimBindingRecord,
    EvidenceRecord,
    ExperimentalDesignCandidateRecord,
    ExperimentDesignRecord,
    ExperimentRecord,
    FalsificationRecord,
    GapRecord,
    HumanDecisionRecord,
    HypothesisRecord,
    IdempotencyRecord,
    ParetoCandidateSetRecord,
    ProjectRecord,
    ProvenanceEventRecord,
    QuestionRecord,
    RunRecord,
    SourceRecord,
    ThreadRecord,
    json_dumps_helper,
    json_loads_helper,
)
from researchforge.provenance.models import ProvenanceActor, ProvenanceEvent, ProvenanceEventType


class ProjectRepository:
    """Repository for ResearchProject aggregates."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, project: ResearchProject) -> ResearchProject:
        rec = self.session.get(ProjectRecord, project.id)
        if not rec:
            rec = ProjectRecord(
                id=project.id,
                title=project.title,
                description=project.description,
                state=project.state.value if hasattr(project.state, "value") else str(project.state),
                question_ids_json=json_dumps_helper(project.question_ids),
                source_ids_json=json_dumps_helper(project.source_ids),
                hypothesis_ids_json=json_dumps_helper(project.hypothesis_ids),
                experiment_ids_json=json_dumps_helper(project.experiment_ids),
                artifact_ids_json=json_dumps_helper(project.artifact_ids),
                provenance_refs_json=json_dumps_helper(project.provenance_refs),
            )
            self.session.add(rec)
        else:
            rec.title = project.title
            rec.description = project.description
            rec.state = project.state.value if hasattr(project.state, "value") else str(project.state)
            rec.question_ids_json = json_dumps_helper(project.question_ids)
            rec.source_ids_json = json_dumps_helper(project.source_ids)
            rec.hypothesis_ids_json = json_dumps_helper(project.hypothesis_ids)
            rec.experiment_ids_json = json_dumps_helper(project.experiment_ids)
            rec.artifact_ids_json = json_dumps_helper(project.artifact_ids)
            rec.provenance_refs_json = json_dumps_helper(project.provenance_refs)
            rec.updated_at = datetime.now(UTC).isoformat()
        self.session.flush()
        return project

    def get(self, project_id: str) -> ResearchProject | None:
        rec = self.session.get(ProjectRecord, project_id)
        if not rec:
            return None
        return ResearchProject(
            id=rec.id,
            title=rec.title,
            description=rec.description,
            state=ResearchLifecycleState(rec.state),
            question_ids=json_loads_helper(rec.question_ids_json),
            source_ids=json_loads_helper(rec.source_ids_json),
            hypothesis_ids=json_loads_helper(rec.hypothesis_ids_json),
            experiment_ids=json_loads_helper(rec.experiment_ids_json),
            artifact_ids=json_loads_helper(rec.artifact_ids_json),
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )

    def list_all(self) -> list[ResearchProject]:
        recs = self.session.query(ProjectRecord).all()
        return [
            ResearchProject(
                id=rec.id,
                title=rec.title,
                description=rec.description,
                state=ResearchLifecycleState(rec.state),
                question_ids=json_loads_helper(rec.question_ids_json),
                source_ids=json_loads_helper(rec.source_ids_json),
                hypothesis_ids=json_loads_helper(rec.hypothesis_ids_json),
                experiment_ids=json_loads_helper(rec.experiment_ids_json),
                artifact_ids=json_loads_helper(rec.artifact_ids_json),
                provenance_refs=json_loads_helper(rec.provenance_refs_json),
            )
            for rec in recs
        ]


class ThreadRepository:
    """Repository for ResearchThread aggregates."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, thread: ResearchThread, check_optimistic_lock: bool = False) -> ResearchThread:
        rec = self.session.get(ThreadRecord, thread.id)
        if not rec:
            rec = ThreadRecord(
                id=thread.id,
                project_id=thread.project_id,
                title=thread.title,
                state=thread.state.value if hasattr(thread.state, "value") else str(thread.state),
                version=thread.version,
                hypothesis_id=thread.hypothesis_id,
                active_experiment_id=thread.active_experiment_id,
                active_run_id=thread.active_run_id,
                artifact_ids_json=json_dumps_helper(thread.artifact_ids),
                provenance_refs_json=json_dumps_helper(thread.provenance_refs),
            )
            self.session.add(rec)
        else:
            if check_optimistic_lock and thread.version != rec.version:
                raise OptimisticConcurrencyError(thread.id, thread.version, rec.version)
            rec.title = thread.title
            rec.state = thread.state.value if hasattr(thread.state, "value") else str(thread.state)
            rec.version = rec.version + 1
            thread.version = rec.version
            rec.hypothesis_id = thread.hypothesis_id
            rec.active_experiment_id = thread.active_experiment_id
            rec.active_run_id = thread.active_run_id
            rec.artifact_ids_json = json_dumps_helper(thread.artifact_ids)
            rec.provenance_refs_json = json_dumps_helper(thread.provenance_refs)
            rec.updated_at = datetime.now(UTC).isoformat()
        self.session.flush()
        return thread

    def get(self, thread_id: str) -> ResearchThread | None:
        rec = self.session.get(ThreadRecord, thread_id)
        if not rec:
            return None
        return ResearchThread(
            id=rec.id,
            project_id=rec.project_id,
            title=rec.title,
            state=HypothesisLifecycleState(rec.state),
            version=rec.version,
            hypothesis_id=rec.hypothesis_id,
            active_experiment_id=rec.active_experiment_id,
            active_run_id=rec.active_run_id,
            artifact_ids=json_loads_helper(rec.artifact_ids_json),
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )

    def list_for_project(self, project_id: str) -> list[ResearchThread]:
        recs = self.session.query(ThreadRecord).filter_by(project_id=project_id).all()
        return [
            ResearchThread(
                id=r.id,
                project_id=r.project_id,
                title=r.title,
                state=HypothesisLifecycleState(r.state),
                version=r.version,
                hypothesis_id=r.hypothesis_id,
                active_experiment_id=r.active_experiment_id,
                active_run_id=r.active_run_id,
                artifact_ids=json_loads_helper(r.artifact_ids_json),
                provenance_refs=json_loads_helper(r.provenance_refs_json),
            )
            for r in recs
        ]


class QuestionRepository:
    """Repository for ResearchQuestion entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, q: ResearchQuestion) -> ResearchQuestion:
        rec = self.session.get(QuestionRecord, q.id)
        if not rec:
            rec = QuestionRecord(
                id=q.id,
                project_id=q.project_id,
                question_text=q.question_text,
                scope_boundaries_json=json_dumps_helper(q.scope_boundaries),
                primary_variable=q.primary_variable,
                target_phenomenon=q.target_phenomenon,
                provenance_refs_json=json_dumps_helper(q.provenance_refs),
            )
            self.session.add(rec)
        self.session.flush()
        return q

    def get(self, qid: str) -> ResearchQuestion | None:
        rec = self.session.get(QuestionRecord, qid)
        if not rec:
            return None
        return ResearchQuestion(
            id=rec.id,
            project_id=rec.project_id,
            question_text=rec.question_text,
            scope_boundaries=json_loads_helper(rec.scope_boundaries_json),
            primary_variable=rec.primary_variable,
            target_phenomenon=rec.target_phenomenon,
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )


class EvidenceRepository:
    """Repository for Evidence entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, ev: Evidence) -> Evidence:
        rec = self.session.get(EvidenceRecord, ev.id)
        if not rec:
            fragments_data = [f.model_dump(mode="json") if hasattr(f, "model_dump") else f for f in ev.fragments]
            rec = EvidenceRecord(
                id=ev.id,
                project_id=ev.project_id,
                source_id=ev.source_id,
                summary=ev.summary,
                fragments_json=json_dumps_helper(fragments_data),
                claims_json=json_dumps_helper(ev.claims),
                provenance_refs_json=json_dumps_helper(ev.provenance_refs),
            )
            self.session.add(rec)
        self.session.flush()
        return ev

    def get(self, evidence_id: str) -> Evidence | None:
        rec = self.session.get(EvidenceRecord, evidence_id)
        if not rec:
            return None
        frags_raw = json_loads_helper(rec.fragments_json)
        fragments = [EvidenceFragment(**f) if isinstance(f, dict) else f for f in frags_raw]
        return Evidence(
            id=rec.id,
            project_id=rec.project_id,
            source_id=rec.source_id,
            summary=rec.summary,
            fragments=fragments,
            claims=json_loads_helper(rec.claims_json),
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )


class GapRepository:
    """Repository for ResearchGap entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, gap: ResearchGap) -> ResearchGap:
        rec = self.session.get(GapRecord, gap.id)
        if not rec:
            rec = GapRecord(
                id=gap.id,
                project_id=gap.project_id,
                description=gap.description,
                unexplored_region=gap.unexplored_region,
                affected_variables_json=json_dumps_helper(gap.affected_variables),
                supporting_evidence_ids_json=json_dumps_helper(gap.supporting_evidence_ids),
                confidence=gap.confidence,
                provenance_refs_json=json_dumps_helper(gap.provenance_refs),
            )
            self.session.add(rec)
        self.session.flush()
        return gap

    def get(self, gap_id: str) -> ResearchGap | None:
        rec = self.session.get(GapRecord, gap_id)
        if not rec:
            return None
        return ResearchGap(
            id=rec.id,
            project_id=rec.project_id,
            description=rec.description,
            unexplored_region=rec.unexplored_region,
            affected_variables=json_loads_helper(rec.affected_variables_json),
            supporting_evidence_ids=json_loads_helper(rec.supporting_evidence_ids_json),
            confidence=rec.confidence,
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )

    def list_by_project(self, project_id: str) -> list[ResearchGap]:
        recs = self.session.query(GapRecord).filter(GapRecord.project_id == project_id).all()
        return [
            ResearchGap(
                id=rec.id,
                project_id=rec.project_id,
                description=rec.description,
                unexplored_region=rec.unexplored_region,
                affected_variables=json_loads_helper(rec.affected_variables_json),
                supporting_evidence_ids=json_loads_helper(rec.supporting_evidence_ids_json),
                confidence=rec.confidence,
                provenance_refs=json_loads_helper(rec.provenance_refs_json),
            )
            for rec in recs
        ]


class HypothesisRepository:
    """Repository for Hypothesis entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, hyp: Hypothesis) -> Hypothesis:
        rec = self.session.get(HypothesisRecord, hyp.id)
        crit_data = [c.model_dump(mode="json") if hasattr(c, "model_dump") else c for c in hyp.falsification_criteria]
        if not rec:
            rec = HypothesisRecord(
                id=hyp.id,
                project_id=hyp.project_id,
                statement=hyp.statement,
                mechanism=hyp.mechanism,
                assumptions_json=json_dumps_helper(hyp.assumption_ids),
                predictions_json=json_dumps_helper(hyp.prediction_ids),
                falsification_criteria_json=json_dumps_helper(crit_data),
                evidence_ids_json=json_dumps_helper(hyp.evidence_basis_ids),
                provenance_refs_json=json_dumps_helper(hyp.provenance_refs),
            )
            self.session.add(rec)
        else:
            rec.statement = hyp.statement
            rec.mechanism = hyp.mechanism
            rec.assumptions_json = json_dumps_helper(hyp.assumption_ids)
            rec.predictions_json = json_dumps_helper(hyp.prediction_ids)
            rec.falsification_criteria_json = json_dumps_helper(crit_data)
            rec.evidence_ids_json = json_dumps_helper(hyp.evidence_basis_ids)
            rec.provenance_refs_json = json_dumps_helper(hyp.provenance_refs)
        self.session.flush()
        return hyp

    def get(self, hyp_id: str) -> Hypothesis | None:
        rec = self.session.get(HypothesisRecord, hyp_id)
        if not rec:
            return None
        crit_raw = json_loads_helper(rec.falsification_criteria_json)
        crit = [FalsificationCriterion(**c) if isinstance(c, dict) else c for c in crit_raw]
        return Hypothesis(
            id=rec.id,
            project_id=rec.project_id,
            statement=rec.statement,
            mechanism=rec.mechanism,
            assumption_ids=json_loads_helper(rec.assumptions_json),
            prediction_ids=json_loads_helper(rec.predictions_json),
            falsification_criteria=crit,
            evidence_basis_ids=json_loads_helper(rec.evidence_ids_json),
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )


class ExperimentRepository:
    """Repository for Experiment design entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, exp: Experiment) -> Experiment:
        rec = self.session.get(ExperimentRecord, exp.id)
        if not rec:
            rec = ExperimentRecord(
                id=exp.id,
                project_id=exp.project_id,
                hypothesis_id=exp.hypothesis_id,
                name=exp.name,
                design_spec_json=json_dumps_helper(exp.plan.model_dump(mode="json") if exp.plan else {}),
                parameters_json=json_dumps_helper(exp.parameters),
                execution_policy_ref="",
                provenance_refs_json=json_dumps_helper(exp.provenance_refs),
            )
            self.session.add(rec)
        self.session.flush()
        return exp

    def get(self, exp_id: str) -> Experiment | None:
        rec = self.session.get(ExperimentRecord, exp_id)
        if not rec:
            return None
        design_data = json_loads_helper(rec.design_spec_json)
        plan = None
        if isinstance(design_data, dict) and "hypothesis_id" in design_data:
            plan = ExperimentPlan(**design_data)
        return Experiment(
            id=rec.id,
            project_id=rec.project_id,
            hypothesis_id=rec.hypothesis_id,
            name=rec.name,
            plan=plan,
            parameters=json_loads_helper(rec.parameters_json),
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )


class RunRepository:
    """Repository for ExperimentRun entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, run: ExperimentRun) -> ExperimentRun:
        rec = self.session.get(RunRecord, run.id)
        if not rec:
            rec = RunRecord(
                id=run.id,
                experiment_id=run.experiment_id,
                project_id=run.project_id or "default",
                status=run.status,
                random_seed=run.random_seed,
                parameter_hash=run.parameter_hash,
                input_hash=run.input_hash,
                output_hash=run.output_hash,
                raw_results_json=json_dumps_helper(run.result.model_dump(mode="json") if run.result else run.results),
                execution_policy_ref=run.execution_policy_ref or "",
                capability_grant_ref=run.capability_grant_ref,
                environment_metadata_json=json_dumps_helper(run.environment_metadata),
                error_message=run.error_message,
                provenance_refs_json=json_dumps_helper(run.provenance_refs),
            )
            self.session.add(rec)
        else:
            rec.status = run.status
            rec.output_hash = run.output_hash
            rec.raw_results_json = json_dumps_helper(run.result.model_dump(mode="json") if run.result else run.results)
            rec.error_message = run.error_message
            rec.provenance_refs_json = json_dumps_helper(run.provenance_refs)
        self.session.flush()
        return run

    def get(self, run_id: str) -> ExperimentRun | None:
        rec = self.session.get(RunRecord, run_id)
        if not rec:
            return None
        res_data = json_loads_helper(rec.raw_results_json)
        res_obj = None
        if isinstance(res_data, dict) and "data" in res_data:
            res_obj = ExperimentResult(**res_data)
        return ExperimentRun(
            id=rec.id,
            experiment_id=rec.experiment_id,
            project_id=rec.project_id,
            status=rec.status,
            random_seed=rec.random_seed,
            parameter_hash=rec.parameter_hash,
            input_hash=rec.input_hash,
            output_hash=rec.output_hash,
            result=res_obj,
            results=res_data if isinstance(res_data, dict) else {},
            execution_policy_ref=rec.execution_policy_ref or None,
            capability_grant_ref=rec.capability_grant_ref,
            environment_metadata=json_loads_helper(rec.environment_metadata_json),
            error_message=rec.error_message,
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )


class FalsificationRepository:
    """Repository for FalsificationEvaluation entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, f: FalsificationEvaluation) -> FalsificationEvaluation:
        rec = self.session.get(FalsificationRecord, f.id)
        if not rec:
            rec = FalsificationRecord(
                id=f.id,
                project_id=f.project_id,
                hypothesis_id=f.hypothesis_id,
                status=f.status.value if hasattr(f.status, "value") else str(f.status),
                reasoning=f.reasoning,
                evidence_ids_json=json_dumps_helper(f.evidence_ids),
                analysis_ids_json=json_dumps_helper(f.analysis_ids),
                provenance_refs_json=json_dumps_helper(f.provenance_refs),
            )
            self.session.add(rec)
        self.session.flush()
        return f

    def get(self, fid: str) -> FalsificationEvaluation | None:
        rec = self.session.get(FalsificationRecord, fid)
        if not rec:
            return None
        return FalsificationEvaluation(
            id=rec.id,
            project_id=rec.project_id,
            hypothesis_id=rec.hypothesis_id,
            status=FalsificationStatus(rec.status),
            reasoning=rec.reasoning,
            evidence_ids=json_loads_helper(rec.evidence_ids_json),
            analysis_ids=json_loads_helper(rec.analysis_ids_json),
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )


class HumanDecisionRepository:
    """Repository for HumanDecision records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(
        self,
        decision_id_or_obj: HumanDecision | str | None = None,
        project_id: str = "",
        decision: str = "",
        rationale: str = "",
        hypothesis_id: str = "",
        evidence_ids: list[str] | None = None,
        analysis_ids: list[str] | None = None,
        signer_identity: str = "",
        signature: str = "",
        falsification_id: str | None = None,
        provenance_refs: list[str] | None = None,
        decision_id: str | None = None,
    ) -> HumanDecisionRecord:
        if isinstance(decision_id_or_obj, HumanDecision):
            obj = decision_id_or_obj
            dec_id = obj.id
            proj_id = obj.project_id
            dec_str = obj.decision.value if hasattr(obj.decision, "value") else str(obj.decision)
            rat = obj.rationale
            hyp_id = obj.target_entity_id if getattr(obj, "target_entity_type", "") == "Hypothesis" else hypothesis_id
            ev_ids = obj.evidence_ids
            an_ids = obj.analysis_ids
            signer = obj.reviewer_id
            sig = obj.signature or ""
            fals_id = obj.falsification_id
            prov_refs = obj.provenance_refs
        else:
            dec_id = decision_id or (decision_id_or_obj if isinstance(decision_id_or_obj, str) else "")
            proj_id = project_id
            dec_str = decision
            rat = rationale
            hyp_id = hypothesis_id
            ev_ids = evidence_ids or []
            an_ids = analysis_ids or []
            signer = signer_identity
            sig = signature
            fals_id = falsification_id
            prov_refs = provenance_refs or []

        rec = self.session.get(HumanDecisionRecord, dec_id)
        if not rec:
            rec = HumanDecisionRecord(
                id=dec_id,
                project_id=proj_id,
                decision=dec_str,
                rationale=rat,
                hypothesis_id=hyp_id,
                evidence_ids_json=json_dumps_helper(ev_ids),
                analysis_ids_json=json_dumps_helper(an_ids),
                falsification_id=fals_id,
                signer_identity=signer,
                signature=sig,
                provenance_refs_json=json_dumps_helper(prov_refs),
            )
            self.session.add(rec)
        self.session.flush()
        return rec

    def get(self, decision_id: str) -> HumanDecisionRecord | None:
        return self.session.get(HumanDecisionRecord, decision_id)


class ConclusionRepository:
    """Repository for scientific Conclusion entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, c: Conclusion) -> Conclusion:
        rec = self.session.get(ConclusionRecord, c.id)
        if not rec:
            rec = ConclusionRecord(
                id=c.id,
                project_id=c.project_id,
                statement=c.statement,
                status=c.status,
                decision_id=c.human_decision_id or "unknown",
                evidence_ids_json=json_dumps_helper(c.evidence_ids),
                analysis_ids_json=json_dumps_helper(c.statistical_analysis_ids),
                falsification_id=c.falsification_evaluation_id,
                artifact_ids_json=json_dumps_helper(c.artifact_ids),
                provenance_refs_json=json_dumps_helper(c.provenance_refs),
            )
            self.session.add(rec)
        else:
            rec.statement = c.statement
            rec.status = c.status
            rec.artifact_ids_json = json_dumps_helper(c.artifact_ids)
            rec.provenance_refs_json = json_dumps_helper(c.provenance_refs)
        self.session.flush()
        return c

    def get(self, cid: str) -> Conclusion | None:
        rec = self.session.get(ConclusionRecord, cid)
        if not rec:
            return None
        return Conclusion(
            id=rec.id,
            project_id=rec.project_id,
            statement=rec.statement,
            status=rec.status,
            human_decision_id=rec.decision_id,
            evidence_ids=json_loads_helper(rec.evidence_ids_json),
            statistical_analysis_ids=json_loads_helper(rec.analysis_ids_json),
            falsification_evaluation_id=rec.falsification_id,
            artifact_ids=json_loads_helper(rec.artifact_ids_json),
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )


class ArtifactRepository:
    """Repository for ResearchArtifact records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, art: ResearchArtifact) -> ResearchArtifact:
        rec = self.session.get(ArtifactRecord, art.id)
        if not rec:
            rec = ArtifactRecord(
                id=art.id,
                project_id=art.project_id,
                name=art.name,
                artifact_type=art.artifact_type.value
                if hasattr(art.artifact_type, "value")
                else str(art.artifact_type),
                file_path=art.file_path,
                content_sha256=art.content_sha256,
                status=art.status,
                upstream_artifact_ids_json=json_dumps_helper(art.upstream_artifact_ids),
                upstream_dataset_hashes_json=json_dumps_helper(art.upstream_dataset_hashes),
                metadata_json=json_dumps_helper(art.metadata),
                provenance_refs_json=json_dumps_helper(art.provenance_refs),
            )
            self.session.add(rec)
        else:
            rec.status = art.status
            rec.content_sha256 = art.content_sha256
            rec.upstream_artifact_ids_json = json_dumps_helper(art.upstream_artifact_ids)
            rec.upstream_dataset_hashes_json = json_dumps_helper(art.upstream_dataset_hashes)
            rec.provenance_refs_json = json_dumps_helper(art.provenance_refs)
        self.session.flush()
        return art

    def get(self, art_id: str) -> ResearchArtifact | None:
        rec = self.session.get(ArtifactRecord, art_id)
        if not rec:
            return None
        return ResearchArtifact(
            id=rec.id,
            project_id=rec.project_id,
            name=rec.name,
            artifact_type=ArtifactType(rec.artifact_type),
            file_path=rec.file_path,
            content_sha256=rec.content_sha256,
            status=rec.status,
            upstream_artifact_ids=json_loads_helper(rec.upstream_artifact_ids_json),
            upstream_dataset_hashes=json_loads_helper(rec.upstream_dataset_hashes_json),
            metadata=json_loads_helper(rec.metadata_json),
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )


class ProvenanceRepository:
    """Repository for database-backed Provenance events."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def record_event(self, event: ProvenanceEvent) -> ProvenanceEvent:
        ts_str = event.timestamp.isoformat() if hasattr(event.timestamp, "isoformat") else str(event.timestamp)
        rec = ProvenanceEventRecord(
            event_id=event.event_id,
            event_type=event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
            schema_version=event.schema_version,
            timestamp=ts_str,
            actor=event.actor.value if hasattr(event.actor, "value") else str(event.actor),
            actor_tier=event.actor_tier.value if hasattr(event.actor_tier, "value") else str(event.actor_tier),
            actor_id=event.actor_id,
            session_id=event.session_id,
            operation=event.operation,
            entity_id=event.entity_id,
            entity_type=event.entity_type,
            entity_refs_json=json_dumps_helper(event.entity_refs),
            input_refs_json=json_dumps_helper(event.input_refs),
            output_refs_json=json_dumps_helper(event.output_refs),
            parameters_json=json_dumps_helper(event.parameters),
            environment_json=json_dumps_helper(event.environment),
            redaction_metadata_json=json_dumps_helper(event.redaction_metadata),
            provider_identity=event.provider_identity,
            event_hash=event.event_hash,
            parent_event_hash=event.parent_event_hash,
        )
        self.session.add(rec)
        self.session.flush()
        return event

    def get(self, event_id: str) -> ProvenanceEvent | None:
        r = self.session.get(ProvenanceEventRecord, event_id)
        if not r:
            return None
        return ProvenanceEvent(
            event_id=r.event_id,
            event_type=ProvenanceEventType(r.event_type),
            schema_version=r.schema_version,
            timestamp=datetime.fromisoformat(r.timestamp) if isinstance(r.timestamp, str) else r.timestamp,
            actor=ProvenanceActor(r.actor),
            actor_id=r.actor_id,
            session_id=r.session_id,
            operation=r.operation,
            entity_id=r.entity_id,
            entity_type=r.entity_type,
            entity_refs=json_loads_helper(r.entity_refs_json),
            input_refs=json_loads_helper(r.input_refs_json),
            output_refs=json_loads_helper(r.output_refs_json),
            parameters=json_loads_helper(r.parameters_json),
            environment=json_loads_helper(r.environment_json),
            redaction_metadata=json_loads_helper(r.redaction_metadata_json),
            provider_identity=r.provider_identity,
            event_hash=r.event_hash,
            parent_event_hash=r.parent_event_hash,
        )

    def get_for_entity(self, entity_id: str) -> list[ProvenanceEvent]:
        recs = self.session.query(ProvenanceEventRecord).filter(ProvenanceEventRecord.entity_id == entity_id).all()
        return [
            ProvenanceEvent(
                event_id=r.event_id,
                event_type=ProvenanceEventType(r.event_type),
                schema_version=r.schema_version,
                timestamp=datetime.fromisoformat(r.timestamp) if isinstance(r.timestamp, str) else r.timestamp,
                actor=ProvenanceActor(r.actor),
                actor_id=r.actor_id,
                session_id=r.session_id,
                operation=r.operation,
                entity_id=r.entity_id,
                entity_type=r.entity_type,
                entity_refs=json_loads_helper(r.entity_refs_json),
                input_refs=json_loads_helper(r.input_refs_json),
                output_refs=json_loads_helper(r.output_refs_json),
                parameters=json_loads_helper(r.parameters_json),
                environment=json_loads_helper(r.environment_json),
                redaction_metadata=json_loads_helper(r.redaction_metadata_json),
                provider_identity=r.provider_identity,
                event_hash=r.event_hash,
                parent_event_hash=r.parent_event_hash,
            )
            for r in recs
        ]

    def list_all(self) -> list[ProvenanceEvent]:
        recs = self.session.query(ProvenanceEventRecord).all()
        return [
            ProvenanceEvent(
                event_id=r.event_id,
                event_type=ProvenanceEventType(r.event_type),
                schema_version=r.schema_version,
                timestamp=datetime.fromisoformat(r.timestamp) if isinstance(r.timestamp, str) else r.timestamp,
                actor=ProvenanceActor(r.actor),
                actor_id=r.actor_id,
                session_id=r.session_id,
                operation=r.operation,
                entity_id=r.entity_id,
                entity_type=r.entity_type,
                entity_refs=json_loads_helper(r.entity_refs_json),
                input_refs=json_loads_helper(r.input_refs_json),
                output_refs=json_loads_helper(r.output_refs_json),
                parameters=json_loads_helper(r.parameters_json),
                environment=json_loads_helper(r.environment_json),
                redaction_metadata=json_loads_helper(r.redaction_metadata_json),
                provider_identity=r.provider_identity,
                event_hash=r.event_hash,
                parent_event_hash=r.parent_event_hash,
            )
            for r in recs
        ]


class IdempotencyRepository:
    """Repository for deduplicating repeated operations with idempotency keys."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_record(self, key: str) -> dict[str, Any] | None:
        rec = self.session.get(IdempotencyRecord, key)
        if not rec:
            return None
        return {
            "key": rec.key,
            "operation": rec.operation,
            "entity_id": rec.entity_id,
            "request_hash": rec.request_hash,
            "actor_id": rec.actor_id,
            "response": json.loads(rec.response_payload_json),
        }

    def save_record(
        self,
        key: str,
        operation: str,
        entity_id: str,
        response_payload: dict[str, Any],
        request_payload: dict[str, Any] | None = None,
        actor_id: str = "",
    ) -> IdempotencyRecord:
        req_hash = compute_content_sha256(request_payload) if request_payload else ""
        rec = IdempotencyRecord(
            key=key,
            operation=operation,
            entity_id=entity_id,
            request_hash=req_hash,
            actor_id=actor_id,
            response_payload_json=json_dumps_helper(response_payload),
        )
        self.session.add(rec)
        self.session.flush()
        return rec

    def check_and_validate(
        self,
        key: str,
        operation: str,
        request_payload: dict[str, Any] | None = None,
        actor_id: str = "",
    ) -> dict[str, Any] | None:
        """Validate an idempotency key: return cached result on identical match or raise IdempotencyConflict."""
        rec = self.session.get(IdempotencyRecord, key)
        if not rec:
            return None

        req_hash = compute_content_sha256(request_payload) if request_payload else ""

        if rec.operation != operation:
            raise IdempotencyConflict(
                key=key,
                message=f"Key '{key}' was previously registered for operation '{rec.operation}', not '{operation}'.",
            )
        if req_hash and rec.request_hash and rec.request_hash != req_hash:
            raise IdempotencyConflict(
                key=key,
                message=f"Key '{key}' was previously registered with different request parameters.",
            )
        if actor_id and rec.actor_id and rec.actor_id != actor_id:
            raise IdempotencyConflict(
                key=key,
                message=f"Key '{key}' was previously registered for actor '{rec.actor_id}', not '{actor_id}'.",
            )

        return {
            "key": rec.key,
            "operation": rec.operation,
            "entity_id": rec.entity_id,
            "response": json.loads(rec.response_payload_json),
        }


class SourceRepository:
    """Repository for literature Source entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, s: Source) -> Source:
        rec = self.session.get(SourceRecord, s.id)
        if not rec:
            rec = SourceRecord(
                id=s.id,
                project_id=s.project_id,
                title=s.title,
                source_type=s.source_type,
                uri=s.uri,
                provider_name=s.provider_name,
                provider_record_id=s.provider_record_id,
                retrieval_query=s.retrieval_query,
                retrieved_content=s.retrieved_content,
                content_hash=s.raw_content_hash,
                metadata_hash=s.metadata_hash,
                retrieval_timestamp=s.retrieval_timestamp,
                paper_json=json_dumps_helper(s.paper.model_dump(mode="json") if s.paper else {}),
                provenance_refs_json=json_dumps_helper(s.provenance_refs),
            )
            self.session.add(rec)
        else:
            rec.retrieved_content = s.retrieved_content
            rec.content_hash = s.raw_content_hash
            rec.provenance_refs_json = json_dumps_helper(s.provenance_refs)
        self.session.flush()
        return s

    def get(self, sid: str) -> Source | None:
        rec = self.session.get(SourceRecord, sid)
        if not rec:
            return None
        paper_data = json_loads_helper(rec.paper_json)
        paper = Paper(**paper_data) if paper_data else None
        return Source(
            id=rec.id,
            project_id=rec.project_id,
            title=rec.title,
            source_type=rec.source_type,
            uri=rec.uri,
            provider_name=rec.provider_name,
            provider_record_id=rec.provider_record_id,
            retrieval_query=rec.retrieval_query,
            retrieved_content=rec.retrieved_content,
            raw_content_hash=rec.content_hash,
            metadata_hash=rec.metadata_hash,
            retrieval_timestamp=rec.retrieval_timestamp,
            paper=paper,
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )

    def list_by_project(self, project_id: str) -> list[Source]:
        recs = self.session.query(SourceRecord).filter(SourceRecord.project_id == project_id).all()
        return [self.get(r.id) for r in recs if self.get(r.id) is not None]  # type: ignore


class ClaimRepository:
    """Repository for scientific Claim entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, c: Claim) -> Claim:
        rec = self.session.get(ClaimRecord, c.id)
        if not rec:
            rec = ClaimRecord(
                id=c.id,
                project_id=c.project_id,
                statement=c.statement,
                claim_type=str(c.claim_type),
                subject=c.subject,
                predicate=c.predicate,
                object=c.object,
                parameter_name=c.parameter_name,
                parameter_range_json=json_dumps_helper(
                    list(c.parameter_value_range) if c.parameter_value_range else []
                ),
                source_ids_json=json_dumps_helper(c.source_ids),
                evidence_ids_json=json_dumps_helper(c.evidence_ids),
                extraction_confidence=c.extraction_confidence,
                source_reported_confidence=c.source_reported_confidence,
                domain_assessment=c.domain_assessment,
                is_grounded_in_evidence=c.is_grounded_in_evidence,
                provenance_refs_json=json_dumps_helper(c.provenance_refs),
            )
            self.session.add(rec)
        else:
            rec.statement = c.statement
            rec.domain_assessment = c.domain_assessment
            rec.evidence_ids_json = json_dumps_helper(c.evidence_ids)
            rec.provenance_refs_json = json_dumps_helper(c.provenance_refs)
        self.session.flush()
        return c

    def get(self, cid: str) -> Claim | None:
        rec = self.session.get(ClaimRecord, cid)
        if not rec:
            return None
        prange = json_loads_helper(rec.parameter_range_json)
        return Claim(
            id=rec.id,
            project_id=rec.project_id,
            statement=rec.statement,
            claim_type=rec.claim_type,
            subject=rec.subject,
            predicate=rec.predicate,
            object=rec.object,
            parameter_name=rec.parameter_name,
            parameter_value_range=tuple(prange) if prange and len(prange) == 2 else None,
            source_ids=json_loads_helper(rec.source_ids_json),
            evidence_ids=json_loads_helper(rec.evidence_ids_json),
            extraction_confidence=rec.extraction_confidence,
            source_reported_confidence=rec.source_reported_confidence,
            domain_assessment=rec.domain_assessment,
            is_grounded_in_evidence=rec.is_grounded_in_evidence,
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )

    def list_by_project(self, project_id: str) -> list[Claim]:
        recs = self.session.query(ClaimRecord).filter(ClaimRecord.project_id == project_id).all()
        return [self.get(r.id) for r in recs if self.get(r.id) is not None]  # type: ignore


class EvidenceClaimBindingRepository:
    """Repository for EvidenceClaimBinding records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, b: EvidenceClaimBinding) -> EvidenceClaimBinding:
        rec = self.session.get(EvidenceClaimBindingRecord, b.id)
        if not rec:
            rec = EvidenceClaimBindingRecord(
                id=b.id,
                project_id=b.project_id,
                evidence_id=b.evidence_id,
                fragment_id=b.fragment_id,
                claim_id=b.claim_id,
                source_id=b.source_id,
                binding_type=b.binding_type,
                extraction_confidence=b.extraction_confidence,
                source_reported_confidence=b.source_reported_confidence,
                domain_assessment=b.domain_assessment,
                provenance_refs_json=json_dumps_helper(b.provenance_refs),
            )
            self.session.add(rec)
        self.session.flush()
        return b

    def list_by_project(self, project_id: str) -> list[EvidenceClaimBinding]:
        recs = (
            self.session.query(EvidenceClaimBindingRecord)
            .filter(EvidenceClaimBindingRecord.project_id == project_id)
            .all()
        )
        return [
            EvidenceClaimBinding(
                id=r.id,
                project_id=r.project_id,
                evidence_id=r.evidence_id,
                fragment_id=r.fragment_id,
                claim_id=r.claim_id,
                source_id=r.source_id,
                binding_type=r.binding_type,
                extraction_confidence=r.extraction_confidence,
                source_reported_confidence=r.source_reported_confidence,
                domain_assessment=r.domain_assessment,
                provenance_refs=json_loads_helper(r.provenance_refs_json),
            )
            for r in recs
        ]


class ContradictionRepository:
    """Repository for PotentialContradiction records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, c: PotentialContradiction) -> PotentialContradiction:
        rec = self.session.get(ContradictionRecord, c.id)
        if not rec:
            rec = ContradictionRecord(
                id=c.id,
                project_id=c.project_id,
                claim_a_id=c.claim_a_id,
                claim_b_id=c.claim_b_id,
                source_a_id=c.source_a_id,
                source_b_id=c.source_b_id,
                contradiction_type=c.contradiction_type,
                description=c.description,
                scope_difference=c.scope_difference,
                parameter_difference=c.parameter_difference,
                methodological_difference=c.methodological_difference,
                provenance_refs_json=json_dumps_helper(c.provenance_refs),
            )
            self.session.add(rec)
        self.session.flush()
        return c

    def list_by_project(self, project_id: str) -> list[PotentialContradiction]:
        recs = self.session.query(ContradictionRecord).filter(ContradictionRecord.project_id == project_id).all()
        return [
            PotentialContradiction(
                id=r.id,
                project_id=r.project_id,
                claim_a_id=r.claim_a_id,
                claim_b_id=r.claim_b_id,
                source_a_id=r.source_a_id,
                source_b_id=r.source_b_id,
                contradiction_type=r.contradiction_type,
                description=r.description,
                scope_difference=r.scope_difference,
                parameter_difference=r.parameter_difference,
                methodological_difference=r.methodological_difference,
                provenance_refs=json_loads_helper(r.provenance_refs_json),
            )
            for r in recs
        ]


class ExperimentDesignRepository:
    """Repository for declarative ExperimentDesign records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, design: ExperimentDesign) -> ExperimentDesign:
        rec = self.session.get(ExperimentDesignRecord, design.id)
        ps_dict = design.parameter_space.model_dump(mode="json")
        cp_dict = design.computation_plan.model_dump(mode="json")

        if not rec:
            rec = ExperimentDesignRecord(
                id=design.id,
                project_id=design.project_id,
                hypothesis_id=design.hypothesis_id,
                name=design.name,
                description=design.description,
                version=design.version,
                parameter_space_json=json_dumps_helper(ps_dict),
                computation_plan_json=json_dumps_helper(cp_dict),
                falsification_criteria_refs_json=json_dumps_helper(design.falsification_criteria_refs),
                provenance_refs_json=json_dumps_helper(design.provenance_refs),
            )
            self.session.add(rec)
        else:
            rec.name = design.name
            rec.description = design.description
            rec.version = design.version
            rec.parameter_space_json = json_dumps_helper(ps_dict)
            rec.computation_plan_json = json_dumps_helper(cp_dict)
            rec.falsification_criteria_refs_json = json_dumps_helper(design.falsification_criteria_refs)
            rec.provenance_refs_json = json_dumps_helper(design.provenance_refs)

        self.session.flush()
        return design

    def get(self, design_id: str) -> ExperimentDesign | None:
        rec = self.session.get(ExperimentDesignRecord, design_id)
        if not rec:
            return None
        ps_data = json_loads_helper(rec.parameter_space_json) or {}
        cp_data = json_loads_helper(rec.computation_plan_json) or {}
        return ExperimentDesign(
            id=rec.id,
            project_id=rec.project_id,
            hypothesis_id=rec.hypothesis_id,
            name=rec.name,
            description=rec.description,
            version=rec.version,
            parameter_space=ParameterSpace.model_validate(ps_data) if ps_data else ParameterSpace(name="Default"),
            computation_plan=ComputationPlan.model_validate(cp_data) if cp_data else ComputationPlan(name="Default"),
            falsification_criteria_refs=json_loads_helper(rec.falsification_criteria_refs_json),
            provenance_refs=json_loads_helper(rec.provenance_refs_json),
        )

    def list_by_project(self, project_id: str) -> list[ExperimentDesign]:
        recs = self.session.query(ExperimentDesignRecord).filter(ExperimentDesignRecord.project_id == project_id).all()
        results = []
        for rec in recs:
            ps_data = json_loads_helper(rec.parameter_space_json) or {}
            cp_data = json_loads_helper(rec.computation_plan_json) or {}
            results.append(
                ExperimentDesign(
                    id=rec.id,
                    project_id=rec.project_id,
                    hypothesis_id=rec.hypothesis_id,
                    name=rec.name,
                    description=rec.description,
                    version=rec.version,
                    parameter_space=ParameterSpace.model_validate(ps_data)
                    if ps_data
                    else ParameterSpace(name="Default"),
                    computation_plan=ComputationPlan.model_validate(cp_data)
                    if cp_data
                    else ComputationPlan(name="Default"),
                    falsification_criteria_refs=json_loads_helper(rec.falsification_criteria_refs_json),
                    provenance_refs=json_loads_helper(rec.provenance_refs_json),
                )
            )
        return results


class ExperimentalDesignCandidateRepository:
    """Repository for ExperimentalDesignCandidate aggregates."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, candidate: ExperimentalDesignCandidate) -> ExperimentalDesignCandidate:
        rec = self.session.get(ExperimentalDesignCandidateRecord, candidate.candidate_design_id)
        res_dict = candidate.resource_requirements.model_dump()
        if not rec:
            rec = ExperimentalDesignCandidateRecord(
                id=candidate.candidate_design_id,
                project_id=candidate.project_id,
                research_question_id=candidate.research_question_id,
                hypothesis_id=candidate.hypothesis_id,
                model_ids_json=json_dumps_helper(candidate.model_ids),
                parameter_assignments_json=json_dumps_helper(candidate.parameter_assignments),
                controlled_variables_json=json_dumps_helper(candidate.controlled_variables),
                independent_variables_json=json_dumps_helper(candidate.independent_variables),
                dependent_variables_json=json_dumps_helper(candidate.dependent_variables),
                target_observables_json=json_dumps_helper(candidate.target_observables),
                constraints_json=json_dumps_helper(candidate.constraints),
                expected_information_json=json_dumps_helper(candidate.expected_information),
                design_objective=str(candidate.design_objective),
                execution_requirements_json=json_dumps_helper(candidate.execution_requirements),
                resource_requirements_json=json_dumps_helper(res_dict),
                risk_constraints_json=json_dumps_helper(candidate.risk_constraints),
                assumptions_json=json_dumps_helper(candidate.assumptions),
                design_status=str(candidate.design_status),
                design_strategy=candidate.design_strategy,
                random_seed=candidate.random_seed,
                sensitivity_study_ref=candidate.sensitivity_study_ref,
                provenance_refs_json=json_dumps_helper([candidate.provenance_ref] if candidate.provenance_ref else []),
            )
            self.session.add(rec)
        else:
            rec.design_status = str(candidate.design_status)
            rec.parameter_assignments_json = json_dumps_helper(candidate.parameter_assignments)
            rec.controlled_variables_json = json_dumps_helper(candidate.controlled_variables)
            rec.resource_requirements_json = json_dumps_helper(res_dict)
            rec.provenance_refs_json = json_dumps_helper([candidate.provenance_ref] if candidate.provenance_ref else [])

        self.session.flush()
        return candidate

    def get(self, candidate_id: str) -> ExperimentalDesignCandidate | None:
        rec = self.session.get(ExperimentalDesignCandidateRecord, candidate_id)
        if not rec:
            return None
        res_data = json_loads_helper(rec.resource_requirements_json) or {}
        prov_list = json_loads_helper(rec.provenance_refs_json)
        return ExperimentalDesignCandidate(
            candidate_design_id=rec.id,
            project_id=rec.project_id,
            research_question_id=rec.research_question_id,
            hypothesis_id=rec.hypothesis_id,
            model_ids=json_loads_helper(rec.model_ids_json),
            parameter_assignments=json_loads_helper(rec.parameter_assignments_json),
            controlled_variables=json_loads_helper(rec.controlled_variables_json),
            independent_variables=json_loads_helper(rec.independent_variables_json),
            dependent_variables=json_loads_helper(rec.dependent_variables_json),
            target_observables=json_loads_helper(rec.target_observables_json),
            constraints=json_loads_helper(rec.constraints_json),
            expected_information=json_loads_helper(rec.expected_information_json),
            design_objective=DesignObjective(rec.design_objective),
            execution_requirements=json_loads_helper(rec.execution_requirements_json),
            resource_requirements=ResourceRequirements.model_validate(res_data) if res_data else ResourceRequirements(),
            risk_constraints=json_loads_helper(rec.risk_constraints_json),
            assumptions=json_loads_helper(rec.assumptions_json),
            design_status=DesignCandidateStatus(rec.design_status),
            design_strategy=rec.design_strategy,
            random_seed=rec.random_seed,
            sensitivity_study_ref=rec.sensitivity_study_ref,
            provenance_ref=prov_list[0] if prov_list else None,
        )

    def list_by_project(self, project_id: str) -> list[ExperimentalDesignCandidate]:
        recs = (
            self.session.query(ExperimentalDesignCandidateRecord)
            .filter(ExperimentalDesignCandidateRecord.project_id == project_id)
            .all()
        )
        results = []
        for rec in recs:
            res_data = json_loads_helper(rec.resource_requirements_json) or {}
            prov_list = json_loads_helper(rec.provenance_refs_json)
            results.append(
                ExperimentalDesignCandidate(
                    candidate_design_id=rec.id,
                    project_id=rec.project_id,
                    research_question_id=rec.research_question_id,
                    hypothesis_id=rec.hypothesis_id,
                    model_ids=json_loads_helper(rec.model_ids_json),
                    parameter_assignments=json_loads_helper(rec.parameter_assignments_json),
                    controlled_variables=json_loads_helper(rec.controlled_variables_json),
                    independent_variables=json_loads_helper(rec.independent_variables_json),
                    dependent_variables=json_loads_helper(rec.dependent_variables_json),
                    target_observables=json_loads_helper(rec.target_observables_json),
                    constraints=json_loads_helper(rec.constraints_json),
                    expected_information=json_loads_helper(rec.expected_information_json),
                    design_objective=DesignObjective(rec.design_objective),
                    execution_requirements=json_loads_helper(rec.execution_requirements_json),
                    resource_requirements=(
                        ResourceRequirements.model_validate(res_data)
                        if res_data
                        else ResourceRequirements()
                    ),
                    risk_constraints=json_loads_helper(rec.risk_constraints_json),
                    assumptions=json_loads_helper(rec.assumptions_json),
                    design_status=DesignCandidateStatus(rec.design_status),
                    design_strategy=rec.design_strategy,
                    random_seed=rec.random_seed,
                    sensitivity_study_ref=rec.sensitivity_study_ref,
                    provenance_ref=prov_list[0] if prov_list else None,
                )
            )
        return results


class CandidateDesignEvaluationRepository:
    """Repository for CandidateDesignEvaluation records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, evaluation: CandidateDesignEvaluation) -> CandidateDesignEvaluation:
        rec = self.session.get(CandidateDesignEvaluationRecord, evaluation.evaluation_id)
        disc_dict = evaluation.discrimination_metric.model_dump() if evaluation.discrimination_metric else {}
        if not rec:
            prov_refs = [evaluation.provenance_ref] if evaluation.provenance_ref else []
            rec = CandidateDesignEvaluationRecord(
                id=evaluation.evaluation_id,
                candidate_design_id=evaluation.candidate_design_id,
                model_predictions_json=json_dumps_helper(evaluation.model_predictions),
                predicted_differences_json=json_dumps_helper(evaluation.predicted_differences),
                numerical_uncertainties_json=json_dumps_helper(evaluation.numerical_uncertainties),
                sensitivities_json=json_dumps_helper(evaluation.sensitivities),
                discrimination_metric_json=json_dumps_helper(disc_dict),
                discrimination_score=evaluation.discrimination_score,
                numerical_robustness=evaluation.numerical_robustness,
                parameter_coverage=evaluation.parameter_coverage,
                resource_cost=evaluation.resource_cost,
                constraint_satisfaction=evaluation.constraint_satisfaction,
                sensitivity_alignment=evaluation.sensitivity_alignment,
                expected_observable_difference=evaluation.expected_observable_difference,
                evaluation_status=evaluation.evaluation_status,
                notes=evaluation.notes,
                provenance_refs_json=json_dumps_helper(prov_refs),
            )
            self.session.add(rec)
        else:
            rec.discrimination_score = evaluation.discrimination_score
            rec.numerical_robustness = evaluation.numerical_robustness
            rec.resource_cost = evaluation.resource_cost
            rec.evaluation_status = evaluation.evaluation_status
            rec.notes = evaluation.notes

        self.session.flush()
        return evaluation

    def get(self, evaluation_id: str) -> CandidateDesignEvaluation | None:
        rec = self.session.get(CandidateDesignEvaluationRecord, evaluation_id)
        if not rec:
            return None
        disc_data = json_loads_helper(rec.discrimination_metric_json) or {}
        prov_list = json_loads_helper(rec.provenance_refs_json)
        return CandidateDesignEvaluation(
            evaluation_id=rec.id,
            candidate_design_id=rec.candidate_design_id,
            model_predictions=json_loads_helper(rec.model_predictions_json),
            predicted_differences=json_loads_helper(rec.predicted_differences_json),
            numerical_uncertainties=json_loads_helper(rec.numerical_uncertainties_json),
            sensitivities=json_loads_helper(rec.sensitivities_json),
            discrimination_metric=DiscriminationMetric.model_validate(disc_data) if disc_data else None,
            discrimination_score=rec.discrimination_score,
            numerical_robustness=rec.numerical_robustness,
            parameter_coverage=rec.parameter_coverage,
            resource_cost=rec.resource_cost,
            constraint_satisfaction=rec.constraint_satisfaction,
            sensitivity_alignment=rec.sensitivity_alignment,
            expected_observable_difference=rec.expected_observable_difference,
            evaluation_status=rec.evaluation_status,
            notes=rec.notes,
            provenance_ref=prov_list[0] if prov_list else None,
        )

    def get_by_candidate(self, candidate_id: str) -> CandidateDesignEvaluation | None:
        rec = (
            self.session.query(CandidateDesignEvaluationRecord)
            .filter(CandidateDesignEvaluationRecord.candidate_design_id == candidate_id)
            .first()
        )
        if not rec:
            return None
        return self.get(rec.id)


class ParetoCandidateSetRepository:
    """Repository for ParetoCandidateSet records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, pareto_set: ParetoCandidateSet) -> ParetoCandidateSet:
        rec = self.session.get(ParetoCandidateSetRecord, pareto_set.set_id)
        evals_data = [e.model_dump(mode="json") for e in pareto_set.candidate_evaluations]
        if not rec:
            rec = ParetoCandidateSetRecord(
                id=pareto_set.set_id,
                project_id=pareto_set.project_id,
                non_dominated_candidate_ids_json=json_dumps_helper(pareto_set.non_dominated_candidate_ids),
                objectives_json=json_dumps_helper(pareto_set.objectives),
                evaluations_json=json_dumps_helper(evals_data),
                metadata_json=json_dumps_helper(pareto_set.metadata),
            )
            self.session.add(rec)
        else:
            rec.non_dominated_candidate_ids_json = json_dumps_helper(pareto_set.non_dominated_candidate_ids)
            rec.objectives_json = json_dumps_helper(pareto_set.objectives)
            rec.evaluations_json = json_dumps_helper(evals_data)
            rec.metadata_json = json_dumps_helper(pareto_set.metadata)

        self.session.flush()
        return pareto_set

    def get(self, set_id: str) -> ParetoCandidateSet | None:
        rec = self.session.get(ParetoCandidateSetRecord, set_id)
        if not rec:
            return None
        evals_raw = json_loads_helper(rec.evaluations_json) or []
        evals = [CandidateDesignEvaluation.model_validate(e) for e in evals_raw]
        return ParetoCandidateSet(
            set_id=rec.id,
            project_id=rec.project_id,
            candidate_evaluations=evals,
            non_dominated_candidate_ids=json_loads_helper(rec.non_dominated_candidate_ids_json),
            objectives=json_loads_helper(rec.objectives_json),
            metadata=json_loads_helper(rec.metadata_json),
        )

    def get_by_project(self, project_id: str) -> ParetoCandidateSet | None:
        rec = (
            self.session.query(ParetoCandidateSetRecord)
            .filter(ParetoCandidateSetRecord.project_id == project_id)
            .order_by(ParetoCandidateSetRecord.created_at.desc())
            .first()
        )
        if not rec:
            return None
        return self.get(rec.id)
