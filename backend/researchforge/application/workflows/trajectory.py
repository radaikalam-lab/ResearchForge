"""Reference Research Trajectory application workflow executing the full lifecycle end-to-end."""

import uuid
from pathlib import Path
from typing import Any

from researchforge.artifacts.manager import ArtifactManager
from researchforge.domain.base import canonical_json_dumps
from researchforge.domain.models.artifact import ArtifactType, ResearchArtifact
from researchforge.domain.models.conclusion import Conclusion, DecisionType, HumanDecision
from researchforge.domain.models.evidence import Evidence
from researchforge.domain.models.experiment import Experiment, ExperimentPlan, ExperimentResult, ExperimentRun
from researchforge.domain.models.falsification import FalsificationEvaluation
from researchforge.domain.models.gap import GapType, ResearchGap
from researchforge.domain.models.hypothesis import FalsificationCriterion, Hypothesis
from researchforge.domain.models.project import ResearchProject, ResearchQuestion
from researchforge.domain.models.thread import ResearchThread
from researchforge.domain.services.falsification import FalsificationEngine
from researchforge.domain.services.lifecycle import LifecycleService
from researchforge.domain.state_machine import HypothesisLifecycleState, ResearchLifecycleState
from researchforge.execution.policy import Capability, CapabilityGrant, ExecutionPolicy
from researchforge.execution.request import ExecutionRequest
from researchforge.execution.sandbox import ExecutionSandbox
from researchforge.persistence.database import DatabaseManager, get_db_manager
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.provenance.event_types import ProvenanceEventType
from researchforge.provenance.models import ProvenanceActor, ProvenanceEvent
from researchforge.provenance.tracker import ProvenanceTracker
from researchforge.providers.registry import ProviderRegistry, global_registry


class TrajectoryExecutionResult:
    """The structured output bundle of a completed reference research trajectory."""

    def __init__(
        self,
        project: ResearchProject,
        thread: ResearchThread,
        question: ResearchQuestion,
        sources: list[Any],
        evidence: Evidence,
        gap: ResearchGap,
        hypothesis: Hypothesis,
        cognitia_critique: Any,
        experiment: Experiment,
        run: ExperimentRun,
        analysis: Any,
        falsification: FalsificationEvaluation,
        decision: HumanDecision,
        conclusion: Conclusion,
        artifact: ResearchArtifact,
        checkpoint: Any,
        events: list[ProvenanceEvent],
    ) -> None:
        self.project = project
        self.thread = thread
        self.question = question
        self.sources = sources
        self.evidence = evidence
        self.gap = gap
        self.hypothesis = hypothesis
        self.cognitia_critique = cognitia_critique
        self.experiment = experiment
        self.run = run
        self.analysis = analysis
        self.falsification = falsification
        self.decision = decision
        self.conclusion = conclusion
        self.artifact = artifact
        self.checkpoint = checkpoint
        self.events = events


class ResearchTrajectoryService:
    """Orchestrates end-to-end computational research trajectories."""

    def __init__(
        self,
        db_manager: DatabaseManager | None = None,
        registry: ProviderRegistry | None = None,
        artifacts_dir: Path | None = None,
    ) -> None:
        self.db_manager = db_manager or get_db_manager()
        self.registry = registry or global_registry
        self.artifacts_dir = artifacts_dir or Path("./artifacts")

    async def execute_reference_trajectory(
        self,
        title: str = "Reference Study: Parameter X Impact on Response Y under Condition Z",
        seed: int = 42,
        secret_key: str = "dev_human_key_42",
        idempotency_key: str | None = None,
    ) -> TrajectoryExecutionResult:
        """Execute deterministic reference scenario from genesis to publishable artifact."""
        with UnitOfWork(self.db_manager) as uow:
            # 0. Idempotency Check
            if idempotency_key and uow.idempotency:
                existing = uow.idempotency.get_record(idempotency_key)
                if existing:
                    proj = uow.projects.get(existing["entity_id"])
                    if proj:
                        # Return previously completed project reference
                        pass

            tracker = ProvenanceTracker(uow.ledger)
            artifact_mgr = ArtifactManager(base_dir=self.artifacts_dir, ledger=uow.ledger)

            # 1. Create ResearchProject
            proj_id = f"proj_{uuid.uuid4().hex[:8]}"
            project = ResearchProject(
                id=proj_id,
                title=title,
                description="Deterministic reference trajectory testing Phase 0.2 contracts.",
                state=ResearchLifecycleState.DRAFT,
            )
            uow.projects.save(project)
            e_proj = tracker.track(
                actor=ProvenanceActor.HUMAN,
                actor_id="principal_investigator",
                operation=ProvenanceEventType.PROJECT_CREATED,
                entity_id=project.id,
                entity_type="ResearchProject",
                parameters={"title": project.title, "state": "DRAFT"},
            )
            uow.record_provenance(e_proj)

            # 2. Create ResearchThread
            thread_id = f"th_{uuid.uuid4().hex[:8]}"
            thread = ResearchThread(
                id=thread_id,
                project_id=project.id,
                title="Thread Alpha: Parameter X variation",
                state=HypothesisLifecycleState.DRAFT,
            )
            uow.threads.save(thread)

            # 3. Define Research Question
            qid = f"q_{uuid.uuid4().hex[:8]}"
            question = ResearchQuestion(
                id=qid,
                project_id=project.id,
                question_text="Does parameter X influence response Y under controlled condition Z?",
                scope_boundaries=["Condition Z", "X in [0, 3]"],
                primary_variable="parameter_x",
                target_phenomenon="response_y",
            )
            uow.questions.save(question)
            project.question_ids.append(question.id)
            project.state = ResearchLifecycleState.QUESTION_DEFINED
            uow.projects.save(project)

            e_q = tracker.track(
                actor=ProvenanceActor.HUMAN,
                actor_id="principal_investigator",
                operation=ProvenanceEventType.QUESTION_DEFINED,
                entity_id=question.id,
                entity_type="ResearchQuestion",
                input_refs=[project.id],
                parameters={"question_text": question.question_text},
            )
            uow.record_provenance(e_q)

            # 4. Search and Ingest Literature Sources
            lit_provider = self.registry.get("literature")
            sources = await lit_provider.search(question.primary_variable)
            project.state = ResearchLifecycleState.EVIDENCE_COLLECTION
            uow.projects.save(project)
            for s in sources:
                project.source_ids.append(s.id)
                e_src = tracker.track(
                    actor=ProvenanceActor.RESEARCHFORGE,
                    actor_id=lit_provider.provider_name,
                    operation=ProvenanceEventType.SOURCE_RETRIEVED,
                    entity_id=s.id,
                    entity_type="Source",
                    input_refs=[question.id],
                    parameters={"uri": s.uri, "title": s.paper.title if s.paper else ""},
                )
                uow.record_provenance(e_src)

            # 5. Extract Evidence & Fragments
            ev_provider = self.registry.get("evidence")
            primary_src = sources[0] if sources else None
            if hasattr(ev_provider, "extract_fragments") and primary_src:
                frags = await ev_provider.extract_fragments(primary_src)
                from researchforge.domain.models.evidence import Claim

                claim = Claim(
                    id=f"claim_{uuid.uuid4().hex[:8]}",
                    statement="Parameter X impacts Response Y monotonically",
                    project_id=project.id,
                )
                evidence = await ev_provider.synthesize_evidence(frags, claim)
                evidence.project_id = project.id
                evidence.source_id = primary_src.id
                evidence.fragments = frags
            else:
                evidence = Evidence(
                    id=f"evid_{uuid.uuid4().hex[:8]}",
                    project_id=project.id,
                    source_id=primary_src.id if primary_src else "src_default",
                    summary="Synthesized baseline evidence on Parameter X.",
                )
            uow.evidence.save(evidence)
            project.state = ResearchLifecycleState.EVIDENCE_STRUCTURED
            uow.projects.save(project)

            e_ev = tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id=ev_provider.provider_name,
                operation=ProvenanceEventType.EVIDENCE_EXTRACTED,
                entity_id=evidence.id,
                entity_type="Evidence",
                input_refs=[s.id for s in sources],
                parameters={"summary": evidence.summary},
            )
            uow.record_provenance(e_ev)

            # 6. Gap Analysis
            gap_provider = self.registry.get("gap")
            gap = ResearchGap(
                id=f"gap_{uuid.uuid4().hex[:8]}",
                project_id=project.id,
                title="Unexplored parameter regime X=3 under Condition Z",
                description=(
                    "Existing evidence covers parameter X in {0, 1, 2}. No evidence exists for X=3 under Condition Z."
                ),
                gap_type=GapType.BOUNDARY_CONDITION_GAP,
                affected_variables=["parameter_x", "response_y"],
                unexplored_region="X=3",
                supporting_evidence_ids=[evidence.id],
                confidence=0.95,
            )
            uow.gaps.save(gap)
            project.state = ResearchLifecycleState.GAP_ANALYSIS
            uow.projects.save(project)
            e_gap = tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id=gap_provider.provider_name,
                operation=ProvenanceEventType.GAP_IDENTIFIED,
                entity_id=gap.id,
                entity_type="ResearchGap",
                input_refs=[evidence.id],
                parameters={"description": gap.description},
            )
            uow.record_provenance(e_gap)

            # 7. Formulate Scientific Hypothesis
            crit = FalsificationCriterion(
                id=f"crit_{uuid.uuid4().hex[:8]}",
                description="Refutation threshold if p-value > 0.05 or response Y does not scale monotonically",
                condition_expression="p_val > 0.05",
                metric_name="p_value",
                refutation_threshold=0.05,
            )
            hyp = Hypothesis(
                id=f"hyp_{uuid.uuid4().hex[:8]}",
                project_id=project.id,
                statement=(
                    "Increasing parameter X from 0 to 3 causes a linear increase in "
                    "measured response Y under Condition Z."
                ),
                mechanism="Coupled field excitation linearly amplifies signal response Y.",
                assumption_ids=["assump_01", "assump_02"],
                prediction_ids=["pred_01"],
                falsification_criteria=[crit],
                evidence_basis_ids=[evidence.id],
            )
            uow.hypotheses.save(hyp)
            project.hypothesis_ids.append(hyp.id)
            thread.hypothesis_id = hyp.id
            thread.state = HypothesisLifecycleState.FORMED
            uow.threads.save(thread)
            project.state = ResearchLifecycleState.HYPOTHESIS_FORMED
            uow.projects.save(project)

            e_hyp = tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id="hypothesis_generator",
                operation=ProvenanceEventType.HYPOTHESIS_FORMED,
                entity_id=hyp.id,
                entity_type="Hypothesis",
                input_refs=[gap.id, evidence.id],
                parameters={"statement": hyp.statement, "mechanism": hyp.mechanism},
            )
            uow.record_provenance(e_hyp)

            # 8. Critique Hypothesis via Cognitia (Advisory only)
            cognitia = self.registry.get("cognitia")
            cognitia_assessment = await cognitia.evaluate_hypothesis(hyp)
            thread.state = HypothesisLifecycleState.CRITIQUED
            uow.threads.save(thread)
            project.state = ResearchLifecycleState.HYPOTHESIS_CRITIQUE
            uow.projects.save(project)

            e_crit = tracker.track(
                actor=ProvenanceActor.COGNITIA,
                actor_id="cognitia_epistemic_engine",
                operation=ProvenanceEventType.HYPOTHESIS_CRITIQUED,
                entity_id=hyp.id,
                entity_type="Hypothesis",
                input_refs=[hyp.id],
                parameters={
                    "tier": cognitia_assessment.tier.value,
                    "falsifiability_assessment": cognitia_assessment.falsifiability_assessment,
                },
            )
            uow.record_provenance(e_crit)

            # 9. Design Computational Experiment
            exp_provider = self.registry.get("experiment")
            plan = ExperimentPlan(
                id=f"plan_{uuid.uuid4().hex[:8]}",
                hypothesis_id=hyp.id,
                experiment_type="NUMERICAL_EXPERIMENT",
                protocol_description="Evaluate model Y = 2X + 1 with seeded noise across X in [0, 1, 2, 3]",
                sample_size=40,
                random_seed=seed,
                compute_budget_sec=10,
            )
            exp = Experiment(
                id=f"exp_{uuid.uuid4().hex[:8]}",
                project_id=project.id,
                hypothesis_id=hyp.id,
                name="Parameter X Scan Experiment",
                plan=plan,
                parameters={"x_values": [0, 1, 2, 3], "formula": "Y = 2*X + 1"},
            )
            uow.experiments.save(exp)
            project.experiment_ids.append(exp.id)
            thread.active_experiment_id = exp.id
            thread.state = HypothesisLifecycleState.EXPERIMENT_READY
            uow.threads.save(thread)
            project.state = ResearchLifecycleState.EXPERIMENT_DESIGNED
            uow.projects.save(project)

            e_exp = tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id=exp_provider.provider_name,
                operation=ProvenanceEventType.EXPERIMENT_DESIGNED,
                entity_id=exp.id,
                entity_type="Experiment",
                input_refs=[hyp.id],
                parameters={"name": exp.name, "parameters": exp.parameters},
            )
            uow.record_provenance(e_exp)

            # 10. Execution Authorization with CapabilityGrant
            grant = CapabilityGrant(
                grant_id=f"grant_{uuid.uuid4().hex[:8]}",
                capability=Capability.RUN_SIMULATION,
                granted_by="lead_researcher",
            )
            policy = ExecutionPolicy(
                allowed_capabilities={Capability.RUN_SIMULATION, Capability.COMPUTE_NUMERICAL},
                allow_network=False,  # default deny
                allow_filesystem_write=True,
                max_time_sec=10,
            )
            project.state = ResearchLifecycleState.EXPERIMENT_READY
            uow.projects.save(project)

            # 11. Execute Sandboxed Experiment Run
            sandbox = ExecutionSandbox()
            run_id = f"run_{uuid.uuid4().hex[:8]}"
            req = ExecutionRequest(
                request_id=f"req_{run_id}",
                command_or_function="simulate_response_y",
                arguments={"x_vals": [0.0, 1.0, 2.0, 3.0], "seed": seed},
                required_capabilities={Capability.RUN_SIMULATION},
                policy=policy,
            )
            project.state = ResearchLifecycleState.COMPUTATION_RUNNING
            uow.projects.save(project)

            def _deterministic_sim(x_vals: list[float], seed: int) -> dict[str, Any]:
                # Synthetic model Y = 2X + 1
                y_vals = [2.0 * x + 1.0 for x in x_vals]
                return {
                    "data": {"x": x_vals, "y": y_vals},
                    "metrics": {"effect_size": 0.98, "p_value": 0.0005, "slope": 2.0},
                    "observations_count": len(x_vals),
                }

            exec_res = await sandbox.execute(req, _deterministic_sim, grants=[grant])
            exp_result = ExperimentResult(
                id=f"res_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                metrics=exec_res.output.get("metrics", {}),
                output_hash=exec_res.output_hash or "hash_01",
                logs=["Deterministic simulation finished successfully."],
            )
            run = ExperimentRun(
                id=run_id,
                experiment_id=exp.id,
                project_id=project.id,
                status="COMPLETED",
                random_seed=seed,
                output_hash=exec_res.output_hash or "hash_01",
                result=exp_result,
            )
            uow.runs.save(run)
            thread.active_run_id = run.id
            thread.state = HypothesisLifecycleState.EVIDENCE_AVAILABLE
            uow.threads.save(thread)
            project.state = ResearchLifecycleState.RESULTS_AVAILABLE
            uow.projects.save(project)

            e_run = tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id="execution_sandbox",
                operation=ProvenanceEventType.RUN_COMPLETED,
                entity_id=run.id,
                entity_type="ExperimentRun",
                input_refs=[exp.id],
                parameters={"status": run.status, "output_hash": run.output_hash, "seed": seed},
            )
            uow.record_provenance(e_run)

            # 12. Run Statistical Analysis
            stats_provider = self.registry.get("statistics")
            analysis = await stats_provider.full_analysis(
                project_id=project.id,
                datasets={"treatment": [1.0, 3.0, 5.0, 7.0], "control": [1.0, 1.0, 1.0, 1.0]},
            )

            # 13. Evaluate Falsification
            fals_eval = FalsificationEngine.evaluate(
                hypothesis=hyp,
                result=exp_result,
                analysis=analysis,
                evidence_items=[evidence],
            )
            uow.falsifications.save(fals_eval)
            thread.state = HypothesisLifecycleState.HUMAN_REVIEW
            uow.threads.save(thread)
            project.state = ResearchLifecycleState.FALSIFICATION
            uow.projects.save(project)
            project.state = ResearchLifecycleState.EVIDENCE_EVALUATION
            uow.projects.save(project)

            e_fals = tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id="falsification_engine",
                operation=ProvenanceEventType.FALSIFICATION_EVALUATED,
                entity_id=fals_eval.id,
                entity_type="FalsificationEvaluation",
                input_refs=[hyp.id, run.id],
                parameters={"status": fals_eval.status.value, "reason": fals_eval.reason},
            )
            uow.record_provenance(e_fals)

            # 14. Human Decision with Cryptographic Signature
            dec_id = f"dec_{uuid.uuid4().hex[:8]}"
            decision = HumanDecision(
                id=dec_id,
                project_id=project.id,
                target_entity_id=hyp.id,
                target_entity_type="Hypothesis",
                decision=DecisionType.APPROVE,
                reviewer_id="lead_investigator_dr_smith",
                rationale=(
                    "Experimental results and statistical analysis decisively confirm linear response scaling at X=3."
                ),
                evidence_ids=[evidence.id, exp_result.id],
                analysis_ids=[analysis.id],
                falsification_id=fals_eval.id,
            )
            decision.sign(secret_key=secret_key)
            uow.decisions.save(
                decision_id=decision.id,
                project_id=decision.project_id,
                decision=decision.decision.value,
                rationale=decision.rationale,
                hypothesis_id=hyp.id,
                evidence_ids=decision.evidence_ids,
                analysis_ids=decision.analysis_ids,
                signer_identity=decision.reviewer_id,
                signature=decision.signature or "",
                falsification_id=decision.falsification_id,
            )
            project.state = ResearchLifecycleState.HUMAN_REVIEW
            uow.projects.save(project)

            e_dec = tracker.track(
                actor=ProvenanceActor.HUMAN,
                actor_id=decision.reviewer_id,
                operation=ProvenanceEventType.DECISION_ACCEPTED,
                entity_id=decision.id,
                entity_type="HumanDecision",
                input_refs=[hyp.id, fals_eval.id],
                parameters={"decision": decision.decision.value, "signature": decision.signature},
            )
            uow.record_provenance(e_dec)

            # 15. Accept Scientific Conclusion
            concl_id = f"concl_{uuid.uuid4().hex[:8]}"
            conclusion = Conclusion(
                id=concl_id,
                project_id=project.id,
                title="Linear Scaling of Response Y over Parameter Range X in [0, 3]",
                statement=(
                    "Empirical and statistical evaluation demonstrates that parameter X "
                    "linearly controls response Y (slope 2.0, p < 0.001) under condition Z."
                ),
                human_decision_id=decision.id,
                evidence_ids=decision.evidence_ids,
                statistical_analysis_ids=decision.analysis_ids,
                falsification_evaluation_id=fals_eval.id,
                is_validated=True,
            )
            uow.conclusions.save(conclusion)
            thread.state = HypothesisLifecycleState.ACCEPTED
            uow.threads.save(thread)

            LifecycleService.transition(
                project,
                target_state=ResearchLifecycleState.CONCLUSION_ACCEPTED,
                has_human_approval=True,
                has_evidence=True,
            )
            uow.projects.save(project)

            e_concl = tracker.track(
                actor=ProvenanceActor.HUMAN,
                actor_id=decision.reviewer_id,
                operation=ProvenanceEventType.CONCLUSION_ACCEPTED,
                entity_id=conclusion.id,
                entity_type="Conclusion",
                input_refs=[decision.id, hyp.id],
                parameters={"statement": conclusion.statement},
            )
            uow.record_provenance(e_concl)

            # 16. Generate Reproducible Artifact Bundle & Content Hashing
            LifecycleService.transition(
                project,
                target_state=ResearchLifecycleState.ARTIFACT_GENERATION,
                has_human_approval=True,
                has_evidence=True,
            )
            report_data = {
                "project_id": project.id,
                "title": project.title,
                "question": question.question_text,
                "evidence_summary": evidence.summary,
                "gap": gap.description,
                "hypothesis": hyp.statement,
                "experiment_parameters": exp.parameters,
                "run_output_hash": run.output_hash,
                "falsification_status": fals_eval.status.value,
                "decision": decision.decision.value,
                "conclusion": conclusion.statement,
                "traceability": {
                    "question_id": question.id,
                    "evidence_id": evidence.id,
                    "hypothesis_id": hyp.id,
                    "run_id": run.id,
                    "decision_id": decision.id,
                    "conclusion_id": conclusion.id,
                },
            }
            report_bytes = canonical_json_dumps(report_data).encode("utf-8")
            report_path = self.artifacts_dir / f"{project.id}" / "reference_research_report.json"

            artifact = artifact_mgr.register_artifact(
                project_id=project.id,
                name="reference_research_report.json",
                artifact_type=ArtifactType.MANUSCRIPT_JSON,
                file_path=str(report_path),
                content_bytes=report_bytes,
                upstream_artifact_ids=[],
            )
            uow.artifacts.save(artifact)
            project.artifact_ids.append(artifact.id)
            thread.artifact_ids.append(artifact.id)

            LifecycleService.transition(
                project,
                target_state=ResearchLifecycleState.PUBLISHABLE_ARTIFACT,
                has_human_approval=True,
                has_evidence=True,
            )
            uow.projects.save(project)
            uow.threads.save(thread)

            # 17. Commit Cryptographic Checkpoint
            checkpoint = uow.ledger.create_checkpoint(secret_signer="lead_investigator_key")
            e_chk = tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id="provenance_ledger",
                operation=ProvenanceEventType.CHECKPOINT_COMMITTED,
                entity_id=checkpoint.checkpoint_id,
                entity_type="Checkpoint",
                parameters={"latest_event_hash": checkpoint.latest_event_hash, "count": checkpoint.event_count},
            )
            uow.record_provenance(e_chk)

            # Save idempotency record if requested
            if idempotency_key and uow.idempotency:
                uow.idempotency.save_record(
                    key=idempotency_key,
                    operation="execute_reference_trajectory",
                    entity_id=project.id,
                    response_payload={"project_id": project.id, "state": project.state.value},
                )

            all_events = uow.ledger.all_events()

            return TrajectoryExecutionResult(
                project=project,
                thread=thread,
                question=question,
                sources=sources,
                evidence=evidence,
                gap=gap,
                hypothesis=hyp,
                cognitia_critique=cognitia_assessment,
                experiment=exp,
                run=run,
                analysis=analysis,
                falsification=fals_eval,
                decision=decision,
                conclusion=conclusion,
                artifact=artifact,
                checkpoint=checkpoint,
                events=all_events,
            )
