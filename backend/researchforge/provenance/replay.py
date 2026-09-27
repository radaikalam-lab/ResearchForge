from researchforge.domain.graph.models import ResearchEdge, ResearchGraph, ResearchNode
from researchforge.domain.graph.types import ResearchNodeType, ResearchRelationType
from researchforge.domain.models.artifact import ArtifactType, ResearchArtifact
from researchforge.domain.models.conclusion import Conclusion, DecisionType, HumanDecision
from researchforge.domain.models.evidence import Claim, Evidence, EvidenceClaimBinding, PotentialContradiction
from researchforge.domain.models.experiment import Experiment, ExperimentRun
from researchforge.domain.models.experiment_design import ExperimentDesign
from researchforge.domain.models.falsification import FalsificationEvaluation, FalsificationStatus
from researchforge.domain.models.gap import ResearchGap
from researchforge.domain.models.hypothesis import FalsificationCriterion, Hypothesis
from researchforge.domain.models.literature import Source
from researchforge.domain.models.project import ResearchProject, ResearchQuestion
from researchforge.domain.models.thread import ResearchThread
from researchforge.domain.state_machine import ResearchLifecycleState
from researchforge.provenance.event_types import ProvenanceEventType
from researchforge.provenance.models import ProvenanceEvent


class ReconstructedResearchState:
    """The aggregate research domain state reconstructed from replaying provenance events."""

    def __init__(self) -> None:
        self.projects: dict[str, ResearchProject] = {}
        self.threads: dict[str, ResearchThread] = {}
        self.questions: dict[str, ResearchQuestion] = {}
        self.sources: dict[str, Source] = {}
        self.evidence: dict[str, Evidence] = {}
        self.claims: dict[str, Claim] = {}
        self.bindings: dict[str, EvidenceClaimBinding] = {}
        self.contradictions: dict[str, PotentialContradiction] = {}
        self.gaps: dict[str, ResearchGap] = {}
        self.hypotheses: dict[str, Hypothesis] = {}
        self.experiments: dict[str, Experiment] = {}
        self.experiment_designs: dict[str, ExperimentDesign] = {}
        self.runs: dict[str, ExperimentRun] = {}
        self.falsifications: dict[str, FalsificationEvaluation] = {}
        self.decisions: dict[str, HumanDecision] = {}
        self.conclusions: dict[str, Conclusion] = {}
        self.artifacts: dict[str, ResearchArtifact] = {}
        self.semantic_graph: ResearchGraph = ResearchGraph(graph_id="replayed_semantic_graph")
        self.replayed_events_count: int = 0


class ProvenanceReplayEngine:
    """Deterministic state rebuilder that replays a sequence of provenance events from genesis."""

    @staticmethod
    def replay(events: list[ProvenanceEvent]) -> ReconstructedResearchState:
        """Reconstruct full domain entity graph and semantic graph by sequentially applying provenance events."""
        state = ReconstructedResearchState()
        graph = state.semantic_graph

        for event in events:
            op = event.operation or event.event_type.value
            params = event.parameters or {}

            if op in (ProvenanceEventType.PROJECT_CREATED.value, "PROJECT_CREATED"):
                proj = ResearchProject(
                    id=event.entity_id,
                    title=params.get("title", f"Project {event.entity_id}"),
                    description=params.get("description", ""),
                    state=ResearchLifecycleState(params.get("state", "DRAFT")),
                    provenance_refs=[event.event_id],
                )
                state.projects[proj.id] = proj
                graph.add_node(
                    ResearchNode(
                        node_id=proj.id,
                        node_type=ResearchNodeType.PROJECT,
                        entity_id=proj.id,
                        label=proj.title,
                    )
                )

            elif op in (ProvenanceEventType.QUESTION_DEFINED.value, "QUESTION_DEFINED"):
                proj_id = (
                    params.get("project_id")
                    or (event.entity_refs[0] if event.entity_refs else None)
                    or (event.input_refs[0] if event.input_refs else "default")
                )
                q = ResearchQuestion(
                    id=event.entity_id,
                    project_id=proj_id,
                    question_text=params.get("question_text", "Reconstructed Question"),
                    scope_boundaries=params.get("scope_boundaries", []),
                    provenance_refs=[event.event_id],
                )
                state.questions[q.id] = q
                if q.project_id in state.projects:
                    state.projects[q.project_id].question_ids.append(q.id)

                graph.add_node(
                    ResearchNode(
                        node_id=q.id,
                        node_type=ResearchNodeType.QUESTION,
                        entity_id=q.id,
                        label=q.question_text,
                    )
                )
                if graph.has_node(q.project_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_asks_{q.project_id}_{q.id}",
                            relation_type=ResearchRelationType.ASKS,
                            source_node_id=q.project_id,
                            target_node_id=q.id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )

            elif op in (ProvenanceEventType.SOURCE_INGESTED.value, "SOURCE_INGESTED"):
                src = Source(
                    id=event.entity_id,
                    uri=params.get("uri", ""),
                    provider_name=params.get("provider_name", "literature_provider"),
                    provider_record_id=params.get("provider_record_id", ""),
                    provenance_refs=[event.event_id],
                )
                state.sources[src.id] = src
                graph.add_node(
                    ResearchNode(
                        node_id=src.id,
                        node_type=ResearchNodeType.SOURCE,
                        entity_id=src.id,
                        label=src.uri,
                    )
                )

            elif op in (ProvenanceEventType.CLAIM_CREATED.value, "CLAIM_CREATED"):
                c = Claim(
                    id=event.entity_id,
                    statement=params.get("statement", "Reconstructed Claim"),
                    claim_type=params.get("claim_type", "EMPIRICAL"),
                    provenance_refs=[event.event_id],
                )
                state.claims[c.id] = c
                graph.add_node(
                    ResearchNode(
                        node_id=c.id,
                        node_type=ResearchNodeType.CLAIM,
                        entity_id=c.id,
                        label=c.statement,
                    )
                )
                if event.entity_refs:
                    for src_id in event.entity_refs:
                        if graph.has_node(src_id):
                            graph.add_edge(
                                ResearchEdge(
                                    edge_id=f"edge_claim_src_{c.id}_{src_id}",
                                    relation_type=ResearchRelationType.DERIVED_FROM,
                                    source_node_id=c.id,
                                    target_node_id=src_id,
                                    provenance_ref=event.event_id,
                                ),
                                validate_nodes=False,
                            )

            elif op in (ProvenanceEventType.CLAIM_BOUND.value, "CLAIM_BOUND"):
                b = EvidenceClaimBinding(
                    id=event.entity_id,
                    project_id=params.get("project_id", "default"),
                    evidence_id=event.entity_refs[0] if event.entity_refs else "",
                    claim_id=event.entity_refs[1] if len(event.entity_refs) > 1 else "",
                    source_id=event.entity_refs[2] if len(event.entity_refs) > 2 else "",
                    binding_type=params.get("binding_type", "SUPPORTS"),
                    provenance_refs=[event.event_id],
                )
                state.bindings[b.id] = b
                rel = ResearchRelationType.SUPPORTS if b.binding_type == "SUPPORTS" else ResearchRelationType.REFUTES
                if b.evidence_id and not graph.has_node(b.evidence_id):
                    graph.add_node(
                        ResearchNode(
                            node_id=b.evidence_id,
                            node_type=ResearchNodeType.EVIDENCE,
                            entity_id=b.evidence_id,
                        )
                    )
                if b.claim_id and not graph.has_node(b.claim_id):
                    graph.add_node(
                        ResearchNode(
                            node_id=b.claim_id,
                            node_type=ResearchNodeType.CLAIM,
                            entity_id=b.claim_id,
                        )
                    )
                if graph.has_node(b.evidence_id) and graph.has_node(b.claim_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_bind_{b.id}",
                            relation_type=rel,
                            source_node_id=b.evidence_id,
                            target_node_id=b.claim_id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )

            elif op in (ProvenanceEventType.CONTRADICTION_IDENTIFIED.value, "CONTRADICTION_IDENTIFIED"):
                con = PotentialContradiction(
                    id=event.entity_id,
                    project_id=params.get("project_id", "default"),
                    claim_a_id=event.entity_refs[0] if event.entity_refs else "",
                    claim_b_id=event.entity_refs[1] if len(event.entity_refs) > 1 else "",
                    contradiction_type=params.get("contradiction_type", "DIRECT_OPPOSITION"),
                    description=params.get("description", ""),
                    provenance_refs=[event.event_id],
                )
                state.contradictions[con.id] = con
                graph.add_node(
                    ResearchNode(
                        node_id=con.id,
                        node_type=ResearchNodeType.CONTRADICTION,
                        entity_id=con.id,
                        label=con.description,
                    )
                )
                if graph.has_node(con.claim_a_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_contra_a_{con.id}_{con.claim_a_id}",
                            relation_type=ResearchRelationType.CONTRADICTS,
                            source_node_id=con.id,
                            target_node_id=con.claim_a_id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )
                if graph.has_node(con.claim_b_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_contra_b_{con.id}_{con.claim_b_id}",
                            relation_type=ResearchRelationType.CONTRADICTS,
                            source_node_id=con.id,
                            target_node_id=con.claim_b_id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )

            elif op in (ProvenanceEventType.EVIDENCE_EXTRACTED.value, "EVIDENCE_EXTRACTED"):
                ev = Evidence(
                    id=event.entity_id,
                    project_id=params.get("project_id", "default"),
                    source_id=params.get("source_id", event.entity_refs[0] if event.entity_refs else "src_01"),
                    summary=params.get("summary", "Reconstructed Evidence"),
                    claims=params.get("claims", []),
                    provenance_refs=[event.event_id],
                )
                state.evidence[ev.id] = ev
                graph.add_node(
                    ResearchNode(
                        node_id=ev.id,
                        node_type=ResearchNodeType.EVIDENCE,
                        entity_id=ev.id,
                        label=ev.summary,
                    )
                )
                if graph.has_node(ev.source_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_ev_src_{ev.id}_{ev.source_id}",
                            relation_type=ResearchRelationType.SOURCED_FROM,
                            source_node_id=ev.id,
                            target_node_id=ev.source_id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )

            elif op in (ProvenanceEventType.GAP_IDENTIFIED.value, "GAP_IDENTIFIED"):
                gap = ResearchGap(
                    id=event.entity_id,
                    project_id=params.get("project_id", "default"),
                    title=params.get("title", "Reconstructed Gap"),
                    description=params.get("description", "Reconstructed Gap Description"),
                    affected_variables=params.get("affected_variables", []),
                    supporting_evidence_ids=event.input_refs or [event.entity_id],
                    provenance_refs=[event.event_id],
                )
                state.gaps[gap.id] = gap
                graph.add_node(
                    ResearchNode(
                        node_id=gap.id,
                        node_type=ResearchNodeType.RESEARCH_GAP,
                        entity_id=gap.id,
                        label=gap.title,
                    )
                )
                for ev_id in gap.supporting_evidence_ids:
                    if graph.has_node(ev_id):
                        graph.add_edge(
                            ResearchEdge(
                                edge_id=f"edge_gap_ev_{gap.id}_{ev_id}",
                                relation_type=ResearchRelationType.DERIVED_FROM,
                                source_node_id=gap.id,
                                target_node_id=ev_id,
                                provenance_ref=event.event_id,
                            ),
                            validate_nodes=False,
                        )

            elif op in (
                ProvenanceEventType.HYPOTHESIS_FORMED.value,
                ProvenanceEventType.HYPOTHESIS_CREATED.value,
                ProvenanceEventType.HYPOTHESIS_GENERATED.value,
                "HYPOTHESIS_FORMED",
                "HYPOTHESIS_CREATED",
                "HYPOTHESIS_GENERATED",
            ):
                crit_list = [
                    FalsificationCriterion(
                        id=f"crit_{event.entity_id}",
                        description=params.get("criterion_description", "Falsification test"),
                        condition_expression=params.get("condition_expression", "p_val > 0.05"),
                        metric_name=params.get("metric_name", "p_val"),
                        refutation_threshold=float(params.get("refutation_threshold", 0.05)),
                    )
                ]
                hyp = Hypothesis(
                    id=event.entity_id,
                    project_id=params.get("project_id", "default"),
                    statement=params.get("statement", "Reconstructed Hypothesis"),
                    mechanism=params.get("mechanism", ""),
                    falsification_criteria=crit_list,
                    evidence_ids=event.input_refs,
                    provenance_refs=[event.event_id],
                )
                state.hypotheses[hyp.id] = hyp
                if hyp.project_id in state.projects:
                    state.projects[hyp.project_id].hypothesis_ids.append(hyp.id)

                graph.add_node(
                    ResearchNode(
                        node_id=hyp.id,
                        node_type=ResearchNodeType.HYPOTHESIS,
                        entity_id=hyp.id,
                        label=hyp.statement,
                    )
                )
                if event.entity_refs:
                    for ref_id in event.entity_refs:
                        if graph.has_node(ref_id):
                            graph.add_edge(
                                ResearchEdge(
                                    edge_id=f"edge_hyp_gap_{ref_id}_{hyp.id}",
                                    relation_type=ResearchRelationType.MOTIVATES,
                                    source_node_id=ref_id,
                                    target_node_id=hyp.id,
                                    provenance_ref=event.event_id,
                                ),
                                validate_nodes=False,
                            )

            elif op in (ProvenanceEventType.EXPERIMENT_DESIGNED.value, "EXPERIMENT_DESIGNED"):
                proj_id = params.get("project_id") or (event.entity_refs[0] if event.entity_refs else "default")
                hyp_id = (
                    params.get("hypothesis_id")
                    or (event.entity_refs[1] if len(event.entity_refs) > 1 else "")
                    or (event.input_refs[0] if event.input_refs else "")
                )
                design_id = params.get("design_id") or (event.entity_refs[2] if len(event.entity_refs) > 2 else None)

                exp = Experiment(
                    id=event.entity_id,
                    project_id=proj_id,
                    hypothesis_id=hyp_id,
                    name=params.get("name", "Reconstructed Experiment"),
                    parameters=params.get("parameters", {}),
                    provenance_refs=[event.event_id],
                )
                state.experiments[exp.id] = exp
                if exp.project_id in state.projects:
                    state.projects[exp.project_id].experiment_ids.append(exp.id)

                graph.add_node(
                    ResearchNode(
                        node_id=exp.id,
                        node_type=ResearchNodeType.EXPERIMENT,
                        entity_id=exp.id,
                        label=exp.name,
                    )
                )
                if exp.hypothesis_id and graph.has_node(exp.hypothesis_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_exp_hyp_{exp.id}_{exp.hypothesis_id}",
                            relation_type=ResearchRelationType.TESTS,
                            source_node_id=exp.id,
                            target_node_id=exp.hypothesis_id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_hyp_tested_{exp.hypothesis_id}_{exp.id}",
                            relation_type=ResearchRelationType.TESTED_BY,
                            source_node_id=exp.hypothesis_id,
                            target_node_id=exp.id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )
                if design_id:
                    design = ExperimentDesign(
                        id=design_id,
                        project_id=proj_id,
                        hypothesis_id=hyp_id,
                        name=f"{exp.name} Design",
                        description=f"Reconstructed Design for {exp.name}",
                        provenance_refs=[event.event_id],
                    )
                    state.experiment_designs[design.id] = design
                    graph.add_node(
                        ResearchNode(
                            node_id=design.id,
                            node_type=ResearchNodeType.EXPERIMENT_DESIGN,
                            entity_id=design.id,
                            label=design.name,
                        )
                    )
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_exp_design_{exp.id}_{design.id}",
                            relation_type=ResearchRelationType.HAS_DESIGN,
                            source_node_id=exp.id,
                            target_node_id=design.id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )

            elif op in (
                ProvenanceEventType.RUN_STARTED.value,
                ProvenanceEventType.RUN_COMPLETED.value,
                ProvenanceEventType.EXPERIMENT_EXECUTED.value,
                "RUN_STARTED",
                "RUN_COMPLETED",
                "EXPERIMENT_EXECUTED",
            ):
                run = ExperimentRun(
                    id=event.entity_id,
                    experiment_id=params.get("experiment_id", event.input_refs[0] if event.input_refs else ""),
                    project_id=params.get("project_id", "default"),
                    status=params.get("status", "COMPLETED"),
                    output_hash=params.get("output_hash", ""),
                    random_seed=params.get("random_seed", 42),
                    provenance_refs=[event.event_id],
                )
                state.runs[run.id] = run
                graph.add_node(
                    ResearchNode(
                        node_id=run.id,
                        node_type=ResearchNodeType.EXPERIMENT_RUN,
                        entity_id=run.id,
                    )
                )
                if run.experiment_id and graph.has_node(run.experiment_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_exp_run_{run.experiment_id}_{run.id}",
                            relation_type=ResearchRelationType.PRODUCES,
                            source_node_id=run.experiment_id,
                            target_node_id=run.id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )

            elif op in (ProvenanceEventType.RESULTS_RECORDED.value, "RESULTS_RECORDED"):
                if event.entity_id in state.runs:
                    state.runs[event.entity_id].output_hash = params.get("output_hash", "")
                    state.runs[event.entity_id].results = params.get("results", {})

            elif op in (ProvenanceEventType.FALSIFICATION_EVALUATED.value, "FALSIFICATION_EVALUATED"):
                fals = FalsificationEvaluation(
                    id=event.entity_id,
                    hypothesis_id=params.get("hypothesis_id", event.input_refs[0] if event.input_refs else ""),
                    status=FalsificationStatus(params.get("status", "SUPPORTED")),
                    reason=params.get("reason", "Replayed evaluation"),
                    evidence_refs=event.input_refs,
                    provenance_refs=[event.event_id],
                )
                state.falsifications[fals.id] = fals
                graph.add_node(
                    ResearchNode(
                        node_id=fals.id,
                        node_type=ResearchNodeType.FALSIFICATION_EVALUATION,
                        entity_id=fals.id,
                    )
                )
                if fals.hypothesis_id and graph.has_node(fals.hypothesis_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_fals_hyp_{fals.id}_{fals.hypothesis_id}",
                            relation_type=ResearchRelationType.EVALUATES,
                            source_node_id=fals.id,
                            target_node_id=fals.hypothesis_id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )

            elif op in (ProvenanceEventType.DECISION_ACCEPTED.value, "DECISION_ACCEPTED"):
                dec = HumanDecision(
                    id=event.entity_id,
                    project_id=params.get("project_id", "default"),
                    target_entity_id=params.get("target_entity_id", "hyp_01"),
                    decision=DecisionType(params.get("decision", "APPROVE")),
                    reviewer_id=event.actor_id,
                    rationale=params.get("rationale", "Approved by human investigator"),
                    provenance_refs=[event.event_id],
                )
                state.decisions[dec.id] = dec
                graph.add_node(
                    ResearchNode(
                        node_id=dec.id,
                        node_type=ResearchNodeType.HUMAN_DECISION,
                        entity_id=dec.id,
                    )
                )
                if dec.target_entity_id and graph.has_node(dec.target_entity_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_informs_dec_{dec.target_entity_id}_{dec.id}",
                            relation_type=ResearchRelationType.INFORMS,
                            source_node_id=dec.target_entity_id,
                            target_node_id=dec.id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )

            elif op in (ProvenanceEventType.CONCLUSION_ACCEPTED.value, "CONCLUSION_ACCEPTED"):
                concl = Conclusion(
                    id=event.entity_id,
                    project_id=params.get("project_id", "default"),
                    title=params.get("title", "Reconstructed Conclusion"),
                    statement=params.get("statement", "Scientific conclusion"),
                    human_decision_id=params.get("decision_id", "dec_01"),
                    evidence_ids=event.input_refs,
                    provenance_refs=[event.event_id],
                )
                state.conclusions[concl.id] = concl
                graph.add_node(
                    ResearchNode(
                        node_id=concl.id,
                        node_type=ResearchNodeType.CONCLUSION,
                        entity_id=concl.id,
                        label=concl.statement,
                    )
                )
                if concl.human_decision_id and graph.has_node(concl.human_decision_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_establishes_{concl.human_decision_id}_{concl.id}",
                            relation_type=ResearchRelationType.ESTABLISHES,
                            source_node_id=concl.human_decision_id,
                            target_node_id=concl.id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )

            elif op in (ProvenanceEventType.ARTIFACT_GENERATED.value, "ARTIFACT_GENERATED"):
                art = ResearchArtifact(
                    id=event.entity_id,
                    project_id=params.get("project_id", "default"),
                    name=params.get("name", "artifact.json"),
                    artifact_type=ArtifactType.MANUSCRIPT_JSON,
                    file_path=params.get("file_path", "./artifacts/report.json"),
                    content_sha256=params.get("content_sha256", ""),
                    status="VERIFIED",
                    upstream_artifact_ids=event.input_refs,
                    provenance_refs=[event.event_id],
                )
                state.artifacts[art.id] = art
                if art.project_id in state.projects:
                    state.projects[art.project_id].artifact_ids.append(art.id)

                graph.add_node(
                    ResearchNode(
                        node_id=art.id,
                        node_type=ResearchNodeType.ARTIFACT,
                        entity_id=art.id,
                        label=art.name,
                    )
                )
                if art.project_id and graph.has_node(art.project_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_mat_art_{art.project_id}_{art.id}",
                            relation_type=ResearchRelationType.MATERIALIZES_AS,
                            source_node_id=art.project_id,
                            target_node_id=art.id,
                            provenance_ref=event.event_id,
                        ),
                        validate_nodes=False,
                    )

            elif op in (ProvenanceEventType.STATE_TRANSITIONED.value, "STATE_TRANSITIONED"):
                proj_id = params.get("project_id", event.entity_id)
                target_state = params.get("target_state")
                if proj_id in state.projects and target_state:
                    state.projects[proj_id].state = ResearchLifecycleState(target_state)

            state.replayed_events_count += 1

        return state
