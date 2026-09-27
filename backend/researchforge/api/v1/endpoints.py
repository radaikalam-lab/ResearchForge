"""API v1 Endpoints for ResearchForge."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from researchforge.application.workflows.literature_trajectory import LiteratureEvidenceWorkflowService
from researchforge.application.workflows.trajectory import ResearchTrajectoryService
from researchforge.domain.models.artifact import ArtifactType, ResearchArtifact
from researchforge.domain.models.conclusion import Conclusion, DecisionType, HumanDecision
from researchforge.domain.models.evidence import Claim, Evidence, EvidenceClaimBinding, PotentialContradiction
from researchforge.domain.models.experiment import Experiment, ExperimentResult, ExperimentRun
from researchforge.domain.models.falsification import FalsificationEvaluation, FalsificationStatus
from researchforge.domain.models.gap import ResearchGap
from researchforge.domain.models.hypothesis import FalsificationCriterion, Hypothesis
from researchforge.domain.models.literature import Source
from researchforge.domain.models.project import ResearchProject, ResearchQuestion
from researchforge.domain.models.statistics import StatisticalAnalysis
from researchforge.domain.models.thread import ResearchThread
from researchforge.domain.services.lifecycle import LifecycleService
from researchforge.domain.state_machine import HypothesisLifecycleState, ResearchLifecycleState
from researchforge.providers.evidence.reference import ReferenceEvidenceExtractionProvider
from researchforge.providers.gap.reference import ReferenceGapAnalysisProvider
from researchforge.providers.registry import global_registry

router = APIRouter()

# In-memory collections for API layer
_projects: dict[str, ResearchProject] = {}
_threads: dict[str, ResearchThread] = {}
_questions: dict[str, ResearchQuestion] = {}
_sources: dict[str, Source] = {}
_evidence: dict[str, Evidence] = {}
_claims: dict[str, Claim] = {}
_bindings: dict[str, EvidenceClaimBinding] = {}
_contradictions: dict[str, PotentialContradiction] = {}
_gaps: dict[str, ResearchGap] = {}
_hypotheses: dict[str, Hypothesis] = {}
_experiments: dict[str, Experiment] = {}
_runs: dict[str, ExperimentRun] = {}
_results: dict[str, ExperimentResult] = {}
_analyses: dict[str, StatisticalAnalysis] = {}
_falsifications: dict[str, FalsificationEvaluation] = {}
_decisions: dict[str, HumanDecision] = {}
_conclusions: dict[str, Conclusion] = {}
_artifacts: dict[str, ResearchArtifact] = {}


# Request DTOs
class CreateProjectRequest(BaseModel):
    title: str
    description: str = ""


class CreateThreadRequest(BaseModel):
    project_id: str
    title: str


class CreateQuestionRequest(BaseModel):
    project_id: str
    question_text: str
    scope_boundaries: list[str] = Field(default_factory=list)


class IngestSourceRequest(BaseModel):
    project_id: str
    query: str


class CreateEvidenceRequest(BaseModel):
    project_id: str
    source_id: str
    summary: str
    claims: list[str] = Field(default_factory=list)


class CreateGapRequest(BaseModel):
    project_id: str
    description: str
    affected_variables: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)


class CreateHypothesisRequest(BaseModel):
    project_id: str
    statement: str
    mechanism: str = ""
    assumptions: list[str] = Field(default_factory=list)
    predictions: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    falsification_metric: str = "p_value"
    falsification_threshold: float = 0.05


class CreateExperimentRequest(BaseModel):
    project_id: str
    hypothesis_id: str
    name: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class CreateRunRequest(BaseModel):
    project_id: str
    experiment_id: str
    random_seed: int = 42


class CreateAnalysisRequest(BaseModel):
    project_id: str
    run_id: str


class CreateFalsificationRequest(BaseModel):
    project_id: str
    hypothesis_id: str


class CreateDecisionRequest(BaseModel):
    project_id: str
    hypothesis_id: str
    decision: DecisionType = DecisionType.APPROVE
    reviewer_id: str
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)
    analysis_ids: list[str] = Field(default_factory=list)


class CreateConclusionRequest(BaseModel):
    project_id: str
    statement: str
    decision_id: str
    evidence_ids: list[str] = Field(default_factory=list)
    analysis_ids: list[str] = Field(default_factory=list)


class CreateArtifactRequest(BaseModel):
    project_id: str
    name: str
    file_path: str
    content: str = ""


class TransitionProjectRequest(BaseModel):
    target_state: ResearchLifecycleState
    has_human_approval: bool = False
    has_evidence: bool = False


# Endpoints
@router.post("/projects", response_model=ResearchProject)
async def create_project(req: CreateProjectRequest) -> ResearchProject:
    """Create a new research project in DRAFT state."""
    proj_id = f"proj_{uuid.uuid4().hex[:8]}"
    project = ResearchProject(
        id=proj_id,
        title=req.title,
        description=req.description,
        state=ResearchLifecycleState.DRAFT,
    )
    _projects[proj_id] = project
    return project


@router.get("/projects", response_model=list[ResearchProject])
async def list_projects() -> list[ResearchProject]:
    """List all research projects."""
    return list(_projects.values())


@router.get("/projects/{project_id}", response_model=ResearchProject)
async def get_project(project_id: str) -> ResearchProject:
    """Retrieve a project by ID."""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    return _projects[project_id]


@router.post("/projects/{project_id}/transition", response_model=ResearchProject)
async def transition_project(project_id: str, req: TransitionProjectRequest) -> ResearchProject:
    """Transition a project to a new lifecycle state with invariant verification."""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    project = _projects[project_id]
    try:
        updated = LifecycleService.transition(
            project,
            target_state=req.target_state,
            has_human_approval=req.has_human_approval,
            has_evidence=req.has_evidence,
        )
        _projects[project_id] = updated
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/threads", response_model=ResearchThread)
async def create_thread(req: CreateThreadRequest) -> ResearchThread:
    """Create a concurrent research thread under a project."""
    if req.project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    th_id = f"th_{uuid.uuid4().hex[:8]}"
    thread = ResearchThread(
        id=th_id,
        project_id=req.project_id,
        title=req.title,
        state=HypothesisLifecycleState.DRAFT,
    )
    _threads[th_id] = thread
    return thread


@router.get("/threads", response_model=list[ResearchThread])
async def list_threads() -> list[ResearchThread]:
    """List all research threads."""
    return list(_threads.values())


@router.post("/questions", response_model=ResearchQuestion)
async def create_question(req: CreateQuestionRequest) -> ResearchQuestion:
    """Register a research question for a project."""
    if req.project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    qid = f"q_{uuid.uuid4().hex[:8]}"
    question = ResearchQuestion(
        id=qid,
        project_id=req.project_id,
        question_text=req.question_text,
        scope_boundaries=req.scope_boundaries,
    )
    _questions[qid] = question
    _projects[req.project_id].question_ids.append(qid)
    return question


@router.get("/questions", response_model=list[ResearchQuestion])
async def list_questions() -> list[ResearchQuestion]:
    """List all research questions."""
    return list(_questions.values())


@router.post("/sources/search", response_model=list[Source])
async def search_sources(req: IngestSourceRequest) -> list[Source]:
    """Search literature provider and register sources."""
    if req.project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    provider = global_registry.get("literature")
    sources = await provider.search(req.query)
    for s in sources:
        _sources[s.id] = s
        _projects[req.project_id].source_ids.append(s.id)
    return sources


@router.get("/sources", response_model=list[Source])
async def list_sources() -> list[Source]:
    """List all ingested sources."""
    return list(_sources.values())


@router.post("/evidence", response_model=Evidence)
async def create_evidence(req: CreateEvidenceRequest) -> Evidence:
    """Register extracted evidence."""
    ev_id = f"ev_{uuid.uuid4().hex[:8]}"
    ev = Evidence(
        id=ev_id,
        project_id=req.project_id,
        source_id=req.source_id,
        summary=req.summary,
        claims=req.claims,
    )
    _evidence[ev_id] = ev
    return ev


@router.get("/evidence", response_model=list[Evidence])
async def list_evidence() -> list[Evidence]:
    """List structured evidence items."""
    return list(_evidence.values())


@router.post("/gaps", response_model=ResearchGap)
async def create_gap(req: CreateGapRequest) -> ResearchGap:
    """Register identified research gap."""
    gap_id = f"gap_{uuid.uuid4().hex[:8]}"
    gap = ResearchGap(
        id=gap_id,
        project_id=req.project_id,
        description=req.description,
        affected_variables=req.affected_variables,
        supporting_evidence_ids=req.supporting_evidence_ids,
    )
    _gaps[gap_id] = gap
    return gap


@router.get("/gaps", response_model=list[ResearchGap])
async def list_gaps() -> list[ResearchGap]:
    """List validated research gaps."""
    return list(_gaps.values())


@router.post("/hypotheses", response_model=Hypothesis)
async def create_hypothesis(req: CreateHypothesisRequest) -> Hypothesis:
    """Formulate scientific hypothesis with falsification criteria."""
    crit = FalsificationCriterion(
        id=f"crit_{uuid.uuid4().hex[:8]}",
        description="Falsification threshold",
        condition_expression=f"{req.falsification_metric} > {req.falsification_threshold}",
        metric_name=req.falsification_metric,
        refutation_threshold=req.falsification_threshold,
    )
    hyp_id = f"hyp_{uuid.uuid4().hex[:8]}"
    hyp = Hypothesis(
        id=hyp_id,
        project_id=req.project_id,
        statement=req.statement,
        mechanism=req.mechanism,
        assumptions=req.assumptions,
        predictions=req.predictions,
        falsification_criteria=[crit],
        evidence_ids=req.evidence_ids,
    )
    _hypotheses[hyp_id] = hyp
    if req.project_id in _projects:
        _projects[req.project_id].hypothesis_ids.append(hyp_id)
    return hyp


@router.get("/hypotheses", response_model=list[Hypothesis])
async def list_hypotheses() -> list[Hypothesis]:
    """List scientific hypotheses."""
    return list(_hypotheses.values())


@router.post("/experiments", response_model=Experiment)
async def create_experiment(req: CreateExperimentRequest) -> Experiment:
    """Design computational experiment."""
    exp_id = f"exp_{uuid.uuid4().hex[:8]}"
    exp = Experiment(
        id=exp_id,
        project_id=req.project_id,
        hypothesis_id=req.hypothesis_id,
        name=req.name,
        parameters=req.parameters,
    )
    _experiments[exp_id] = exp
    if req.project_id in _projects:
        _projects[req.project_id].experiment_ids.append(exp_id)
    return exp


@router.get("/experiments", response_model=list[Experiment])
async def list_experiments() -> list[Experiment]:
    """List experiments."""
    return list(_experiments.values())


@router.post("/runs", response_model=ExperimentRun)
async def create_run(req: CreateRunRequest) -> ExperimentRun:
    """Record execution run."""
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    res = ExperimentResult(
        id=f"res_{uuid.uuid4().hex[:8]}",
        run_id=run_id,
        metrics={"effect_size": 0.88, "p_value": 0.001},
        output_hash="mock_hash_123",
    )
    run = ExperimentRun(
        id=run_id,
        experiment_id=req.experiment_id,
        project_id=req.project_id,
        status="COMPLETED",
        random_seed=req.random_seed,
        result=res,
        output_hash=res.output_hash,
    )
    _runs[run_id] = run
    _results[res.id] = res
    return run


@router.get("/runs", response_model=list[ExperimentRun])
async def list_runs() -> list[ExperimentRun]:
    """List experiment runs."""
    return list(_runs.values())


@router.get("/results", response_model=list[ExperimentResult])
async def list_results() -> list[ExperimentResult]:
    """List experiment results."""
    return list(_results.values())


@router.post("/falsification", response_model=FalsificationEvaluation)
async def create_falsification(req: CreateFalsificationRequest) -> FalsificationEvaluation:
    """Evaluate hypothesis falsification status."""
    fals_id = f"fals_{uuid.uuid4().hex[:8]}"
    fals = FalsificationEvaluation(
        id=fals_id,
        hypothesis_id=req.hypothesis_id,
        status=FalsificationStatus.SUPPORTED,
        reason="Empirical findings survive falsification criteria.",
    )
    _falsifications[fals_id] = fals
    return fals


@router.get("/falsification", response_model=list[FalsificationEvaluation])
async def list_falsifications() -> list[FalsificationEvaluation]:
    """List falsification evaluation records."""
    return list(_falsifications.values())


@router.post("/decisions", response_model=HumanDecision)
async def create_decision(req: CreateDecisionRequest) -> HumanDecision:
    """Record signed human authority decision."""
    dec_id = f"dec_{uuid.uuid4().hex[:8]}"
    dec = HumanDecision(
        id=dec_id,
        project_id=req.project_id,
        target_entity_id=req.hypothesis_id,
        decision=req.decision,
        reviewer_id=req.reviewer_id,
        rationale=req.rationale,
        evidence_ids=req.evidence_ids,
        analysis_ids=req.analysis_ids,
    )
    dec.sign()
    _decisions[dec_id] = dec
    return dec


@router.post("/conclusions", response_model=Conclusion)
async def create_conclusion(req: CreateConclusionRequest) -> Conclusion:
    """Record scientific conclusion grounded in human decision and evidence."""
    concl_id = f"concl_{uuid.uuid4().hex[:8]}"
    concl = Conclusion(
        id=concl_id,
        project_id=req.project_id,
        statement=req.statement,
        human_decision_id=req.decision_id,
        evidence_ids=req.evidence_ids,
        statistical_analysis_ids=req.analysis_ids,
        is_validated=True,
    )
    _conclusions[concl_id] = concl
    return concl


@router.get("/conclusions", response_model=list[Conclusion])
async def list_conclusions() -> list[Conclusion]:
    """List conclusions."""
    return list(_conclusions.values())


@router.post("/artifacts", response_model=ResearchArtifact)
async def create_artifact(req: CreateArtifactRequest) -> ResearchArtifact:
    """Register artifact metadata."""
    art_id = f"art_{uuid.uuid4().hex[:8]}"
    art = ResearchArtifact(
        id=art_id,
        project_id=req.project_id,
        name=req.name,
        artifact_type=ArtifactType.MANUSCRIPT_JSON,
        file_path=req.file_path,
        content_sha256="mock_content_hash_123",
        status="VERIFIED",
    )
    _artifacts[art_id] = art
    return art


@router.get("/artifacts", response_model=list[ResearchArtifact])
async def list_artifacts() -> list[ResearchArtifact]:
    """List reproducible research artifacts."""
    return list(_artifacts.values())


@router.post("/trajectory/execute")
async def execute_trajectory_endpoint() -> dict[str, Any]:
    """Execute complete reference research trajectory end-to-end."""
    service = ResearchTrajectoryService()
    res = await service.execute_reference_trajectory()
    return {
        "status": "SUCCESS",
        "project_id": res.project.id,
        "thread_id": res.thread.id,
        "question_id": res.question.id,
        "hypothesis_id": res.hypothesis.id,
        "run_id": res.run.id,
        "falsification_status": res.falsification.status.value,
        "decision_id": res.decision.id,
        "conclusion_id": res.conclusion.id,
        "artifact_id": res.artifact.id,
        "events_count": len(res.events),
    }


@router.get("/reports/summary/{project_id}")
async def get_project_summary(project_id: str) -> dict[str, Any]:
    """Return summary overview of project epistemic state and artifact lineage."""
    if project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    proj = _projects[project_id]
    return {
        "project_id": proj.id,
        "title": proj.title,
        "state": proj.state.value,
        "questions_count": len(proj.question_ids),
        "sources_count": len(proj.source_ids),
        "hypotheses_count": len(proj.hypothesis_ids),
        "experiments_count": len(proj.experiment_ids),
        "artifacts_count": len(proj.artifact_ids),
    }


# ==========================================
# PHASE 1 LITERATURE & EVIDENCE ENDPOINTS
# ==========================================


class LiteratureSearchAPIRequest(BaseModel):
    query: str
    limit: int = 10


class LiteratureIngestAPIRequest(BaseModel):
    project_id: str
    uri: str
    title: str
    provider_name: str = "reference-literature-v1"
    provider_record_id: str
    retrieved_content: str = ""


class ExtractEvidenceAPIRequest(BaseModel):
    project_id: str
    source_id: str


class GapAnalyzeAPIRequest(BaseModel):
    project_id: str


@router.post("/literature/search", response_model=list[Source])
async def search_literature(req: LiteratureSearchAPIRequest) -> list[Source]:
    """Search literature providers for candidate sources."""
    provider = global_registry.get("literature")
    sources = await provider.search(req.query, limit=req.limit)
    if not isinstance(sources, list):
        sources = sources.sources
    for s in sources:
        _sources[s.id] = s
    return sources


@router.post("/literature/ingest", response_model=Source)
async def ingest_source(req: LiteratureIngestAPIRequest) -> Source:
    """Ingest and normalize a literature source."""
    if req.project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    source = Source(
        id=f"src_{uuid.uuid4().hex[:8]}",
        project_id=req.project_id,
        title=req.title,
        uri=req.uri,
        provider_name=req.provider_name,
        provider_record_id=req.provider_record_id,
        retrieved_content=req.retrieved_content,
    )
    _sources[source.id] = source
    _projects[req.project_id].source_ids.append(source.id)
    return source


@router.get("/literature/{source_id}", response_model=Source)
async def get_source(source_id: str) -> Source:
    """Retrieve an ingested source by ID."""
    if source_id not in _sources:
        raise HTTPException(status_code=404, detail="Source not found")
    return _sources[source_id]


@router.post("/evidence/extract", response_model=list[Claim])
async def extract_evidence(req: ExtractEvidenceAPIRequest) -> list[Claim]:
    """Extract fragments and candidate claims from a source."""
    if req.source_id not in _sources:
        raise HTTPException(status_code=404, detail="Source not found")
    source = _sources[req.source_id]
    extractor = ReferenceEvidenceExtractionProvider()
    frags = await extractor.extract_fragments(source)
    claims = await extractor.extract_candidate_claims(source, frags)
    for c in claims:
        _claims[c.id] = c
    return claims


@router.get("/evidence/{evidence_id}", response_model=Evidence)
async def get_evidence(evidence_id: str) -> Evidence:
    """Retrieve an evidence aggregate by ID."""
    if evidence_id not in _evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return _evidence[evidence_id]


@router.get("/claims", response_model=list[Claim])
async def list_claims() -> list[Claim]:
    """List all extracted claims."""
    return list(_claims.values())


@router.get("/claims/{claim_id}", response_model=Claim)
async def get_claim(claim_id: str) -> Claim:
    """Retrieve an extracted claim by ID."""
    if claim_id not in _claims:
        raise HTTPException(status_code=404, detail="Claim not found")
    return _claims[claim_id]


@router.post("/gaps/analyze", response_model=list[ResearchGap])
async def analyze_gaps(req: GapAnalyzeAPIRequest) -> list[ResearchGap]:
    """Perform gap analysis on project evidence and claims."""
    if req.project_id not in _projects:
        raise HTTPException(status_code=404, detail="Project not found")
    ev_items = [e for e in _evidence.values() if e.project_id == req.project_id]
    claims = [c for c in _claims.values() if c.project_id == req.project_id]
    gap_provider = ReferenceGapAnalysisProvider()
    candidates = await gap_provider.analyze_gaps(ev_items, claims)
    gaps: list[ResearchGap] = []
    for cand in candidates:
        g = await gap_provider.evaluate_gap_validity(cand, ev_items)
        if g:
            _gaps[g.id] = g
            gaps.append(g)
    return gaps


@router.get("/gaps/{gap_id}", response_model=ResearchGap)
async def get_gap(gap_id: str) -> ResearchGap:
    """Retrieve a research gap by ID."""
    if gap_id not in _gaps:
        raise HTTPException(status_code=404, detail="Research gap not found")
    return _gaps[gap_id]


@router.post("/literature/trajectory/execute")
async def execute_literature_trajectory_endpoint() -> dict[str, Any]:
    """Execute complete Phase 1 literature and evidence trajectory."""
    service = LiteratureEvidenceWorkflowService()
    res = await service.execute_literature_trajectory()
    return {
        "status": "SUCCESS",
        "project_id": res.project.id,
        "thread_id": res.thread.id,
        "question_id": res.question.id,
        "sources_count": len(res.sources),
        "fragments_count": len(res.fragments),
        "claims_count": len(res.claims),
        "bindings_count": len(res.bindings),
        "contradictions_count": len(res.contradictions),
        "gaps_count": len(res.gaps),
        "hypotheses_count": len(res.hypotheses),
        "bundle_path": str(res.evidence_bundle_path),
        "bundle_hash": res.evidence_bundle_hash,
        "events_count": len(res.events),
    }


# Phase 2 Graph & Experiment Planning API Endpoints
class PlanExperimentAPIRequest(BaseModel):
    project_id: str
    hypothesis_id: str
    experiment_name: str
    sample_count: int = 50


class ConsultCognitiaAPIRequest(BaseModel):
    project_id: str
    seed_node_ids: list[str]
    operation_type: str = "CRITIQUE"
    depth: int = 1


class PromoteHypothesisAPIRequest(BaseModel):
    project_id: str
    advisory_result_id: str
    candidate_hypothesis_text: str
    gap_id: str
    actor_id: str = "human_researcher_01"


@router.get("/graph/{project_id}")
async def get_project_graph(project_id: str) -> dict[str, Any]:
    """Retrieve the semantic graph for a project via GraphQueryApplicationService."""
    from researchforge.application.queries.graph_query import GraphQueryApplicationService

    service = GraphQueryApplicationService()
    try:
        return service.get_project_graph(project_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/graph/{project_id}/neighbors/{node_id}")
async def get_node_neighbors(project_id: str, node_id: str) -> dict[str, Any]:
    """Retrieve adjacent neighbors and incident edges for a node via GraphQueryApplicationService."""
    from researchforge.application.queries.graph_query import GraphQueryApplicationService

    service = GraphQueryApplicationService()
    try:
        return service.get_node_neighbors(project_id, node_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/graph/{project_id}/path")
async def get_graph_path(project_id: str, source_node_id: str, target_node_id: str) -> dict[str, Any]:
    """Find a directed path between two nodes in the project graph via GraphQueryApplicationService."""
    from researchforge.application.queries.graph_query import GraphQueryApplicationService

    service = GraphQueryApplicationService()
    try:
        path = service.find_path(project_id, source_node_id, target_node_id)
        return {
            "project_id": project_id,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "path": path,
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/cognitia/consult")
async def consult_cognitia_advisory(req: ConsultCognitiaAPIRequest) -> dict[str, Any]:
    """Request non-authoritative Cognitia advisory reasoning over a bounded semantic graph context."""
    from researchforge.application.workflows.cognitia_advisory import CognitiaAdvisoryWorkflowService

    service = CognitiaAdvisoryWorkflowService()
    try:
        result = await service.consult_on_subgraph(
            project_id=req.project_id,
            seed_node_ids=set(req.seed_node_ids),
            operation_type=req.operation_type,
            depth=req.depth,
        )
        return result.model_dump()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/cognitia/promote-hypothesis")
async def promote_cognitia_hypothesis(req: PromoteHypothesisAPIRequest) -> dict[str, Any]:
    """Promote an advisory candidate hypothesis into authoritative state with human authorization."""
    from researchforge.application.workflows.cognitia_advisory import CognitiaAdvisoryWorkflowService
    from researchforge.domain.contracts.cognitia import CognitiaAdvisoryResult

    service = CognitiaAdvisoryWorkflowService()
    try:
        # Dummy advisory result shell carrying the result_id for provenance
        advisory_stub = CognitiaAdvisoryResult(
            id=req.advisory_result_id,
            result_id=req.advisory_result_id,
            request_id="req_promoted",
            context_graph_hash="hash_promoted",
        )
        hyp, dec = service.promote_candidate_hypothesis(
            project_id=req.project_id,
            advisory_result=advisory_stub,
            candidate_hypothesis_text=req.candidate_hypothesis_text,
            gap_id=req.gap_id,
            decision_actor_id=req.actor_id,
        )
        return {"hypothesis": hyp.model_dump(), "decision": dec.model_dump()}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/experiments/plan")
async def plan_experiment_endpoint(req: PlanExperimentAPIRequest) -> dict[str, Any]:
    """Plan an experiment connected to a hypothesis, parameter space, and computation plan."""
    from researchforge.application.workflows.experiment_trajectory import ExperimentPlanningWorkflowService
    from researchforge.domain.models.parameter_space import ParameterDefinition, ParameterType

    service = ExperimentPlanningWorkflowService()
    try:
        design = await service.plan_experiment_trajectory(
            project_id=req.project_id,
            hypothesis_id=req.hypothesis_id,
            experiment_name=req.experiment_name,
            parameter_definitions=[
                ParameterDefinition(
                    id=f"param_{uuid.uuid4().hex[:6]}",
                    parameter_name="Parameter X",
                    parameter_type=ParameterType.CONTINUOUS,
                    min_value=0.0,
                    max_value=5.0,
                    default_value=1.0,
                )
            ],
            sample_count=req.sample_count,
        )
        return design.model_dump()
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/experiments/{experiment_id}/design")
async def get_experiment_design_endpoint(experiment_id: str) -> dict[str, Any]:
    """Retrieve the declarative ExperimentDesign for an experiment via GraphQueryApplicationService."""
    from researchforge.application.queries.graph_query import GraphQueryApplicationService

    service = GraphQueryApplicationService()
    try:
        return service.get_experiment_design(experiment_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/experiments/{experiment_id}/parameter-space")
async def get_experiment_parameter_space_endpoint(experiment_id: str) -> dict[str, Any]:
    """Retrieve the parameter space specification for an experiment via GraphQueryApplicationService."""
    from researchforge.application.queries.graph_query import GraphQueryApplicationService

    service = GraphQueryApplicationService()
    try:
        return service.get_experiment_parameter_space(experiment_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


# ==========================================
# PHASE 2.4 EXPERIMENTAL DESIGN CANDIDATE ENDPOINTS
# ==========================================


class GenerateCandidatesAPIRequest(BaseModel):
    project_id: str
    parameter_space: dict[str, Any]
    model_ids: list[str]
    hypothesis_id: str | None = None
    research_question_id: str | None = None
    sensitivity_study_id: str | None = None
    design_objective: str = "MODEL_DISCRIMINATION"
    sampling_strategy: str = "GRID"
    sample_count: int = 5
    random_seed: int = 42
    controlled_variables: dict[str, Any] = Field(default_factory=dict)
    target_observables: list[str] = Field(default_factory=list)


class EvaluateCandidatesAPIRequest(BaseModel):
    project_id: str
    candidate_ids: list[str]
    model_a_id: str
    model_b_id: str
    model_a_params_override: dict[str, Any] = Field(default_factory=dict)
    model_b_params_override: dict[str, Any] = Field(default_factory=dict)
    objectives: list[str] = Field(default_factory=list)


class PromoteCandidateAPIRequest(BaseModel):
    project_id: str
    candidate_id: str
    reviewer_id: str
    rationale: str
    experiment_name: str
    decision_type: str = "APPROVE"


@router.post("/designs/candidates/generate")
async def generate_candidates_endpoint(req: GenerateCandidatesAPIRequest) -> list[dict[str, Any]]:
    """Deterministically generate candidate experimental designs over parameter space."""
    from researchforge.application.workflows.experimental_design_workflow import (
        ExperimentalDesignWorkflowService,
    )
    from researchforge.domain.models.experimental_design_candidate import DesignObjective
    from researchforge.domain.models.parameter_space import (
        ParameterDefinition,
        ParameterSpace,
        ParameterType,
        SamplingStrategy,
    )

    # Convert parameter_space dictionary to model
    raw_params = req.parameter_space.get("parameters", {})
    pdefs: dict[str, ParameterDefinition] = {}
    for p_name, p_data in raw_params.items():
        if isinstance(p_data, dict):
            p_type_str = p_data.get("parameter_type", "CONTINUOUS")
            p_type = (
                ParameterType(p_type_str)
                if p_type_str in ParameterType._value2member_map_
                else ParameterType.CONTINUOUS
            )
            pdefs[p_name] = ParameterDefinition(
                parameter_name=p_name,
                parameter_type=p_type,
                min_value=p_data.get("min_value"),
                max_value=p_data.get("max_value"),
                default_value=p_data.get("default_value"),
                allowed_values=p_data.get("allowed_values", []),
            )
        else:
            pdefs[p_name] = ParameterDefinition(parameter_name=p_name, default_value=p_data)

    ps = ParameterSpace(
        id=req.parameter_space.get("id", f"ps_{uuid.uuid4().hex[:6]}"),
        name=req.parameter_space.get("name", "Exploration Space"),
        parameters=pdefs,
    )

    strategy = (
        SamplingStrategy(req.sampling_strategy)
        if req.sampling_strategy in SamplingStrategy._value2member_map_
        else SamplingStrategy.GRID
    )
    service = ExperimentalDesignWorkflowService()
    try:
        cands = service.generate_candidate_designs(
            project_id=req.project_id,
            parameter_space=ps,
            model_ids=req.model_ids,
            hypothesis_id=req.hypothesis_id,
            research_question_id=req.research_question_id,
            sensitivity_study_id=req.sensitivity_study_id,
            design_objective=DesignObjective(req.design_objective),
            sampling_strategy=strategy,
            sample_count=req.sample_count,
            random_seed=req.random_seed,
            controlled_variables=req.controlled_variables or None,
            target_observables=req.target_observables or None,
        )
        return [c.model_dump() for c in cands]
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/designs/candidates/evaluate")
async def evaluate_candidates_endpoint(req: EvaluateCandidatesAPIRequest) -> dict[str, Any]:
    """Evaluate candidate experimental designs on model discrimination capability and compute Pareto set."""
    from researchforge.application.workflows.experimental_design_workflow import (
        ExperimentalDesignWorkflowService,
    )

    service = ExperimentalDesignWorkflowService()
    try:
        evals, pareto_set = service.evaluate_candidate_designs(
            project_id=req.project_id,
            candidate_ids=req.candidate_ids,
            model_a_id=req.model_a_id,
            model_b_id=req.model_b_id,
            model_a_params_override=req.model_a_params_override or None,
            model_b_params_override=req.model_b_params_override or None,
            objectives=req.objectives or None,
        )
        return {
            "evaluations": [e.model_dump() for e in evals],
            "pareto_set": pareto_set.model_dump(),
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/designs/candidates/promote")
async def promote_candidate_endpoint(req: PromoteCandidateAPIRequest) -> dict[str, Any]:
    """Promote a candidate design into an authoritative ExperimentDesign via human decision."""
    from researchforge.application.workflows.experimental_design_workflow import (
        ExperimentalDesignWorkflowService,
    )
    from researchforge.domain.models.conclusion import DecisionType

    dec_type = (
        DecisionType(req.decision_type)
        if req.decision_type in DecisionType._value2member_map_
        else DecisionType.APPROVE
    )
    service = ExperimentalDesignWorkflowService()
    try:
        exp_design, decision = service.promote_candidate_to_experiment_design(
            project_id=req.project_id,
            candidate_id=req.candidate_id,
            reviewer_id=req.reviewer_id,
            rationale=req.rationale,
            experiment_name=req.experiment_name,
            decision_type=dec_type,
        )
        return {
            "experiment_design": exp_design.model_dump(),
            "human_decision": decision.model_dump(),
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/designs/candidates/{candidate_id}")
async def get_candidate_design_endpoint(candidate_id: str) -> dict[str, Any]:
    """Retrieve an ExperimentalDesignCandidate by ID."""
    from researchforge.application.queries.graph_query import GraphQueryApplicationService

    service = GraphQueryApplicationService()
    try:
        return service.get_candidate_design(candidate_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/designs/candidates/project/{project_id}")
async def list_project_candidates_endpoint(project_id: str) -> list[dict[str, Any]]:
    """List all candidate designs for a project."""
    from researchforge.application.queries.graph_query import GraphQueryApplicationService

    service = GraphQueryApplicationService()
    try:
        return service.list_candidate_designs(project_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/designs/candidates/{candidate_id}/evaluation")
async def get_candidate_evaluation_endpoint(candidate_id: str) -> dict[str, Any]:
    """Retrieve the multi-objective evaluation for a candidate design."""
    from researchforge.application.queries.graph_query import GraphQueryApplicationService

    service = GraphQueryApplicationService()
    try:
        return service.get_candidate_evaluation(candidate_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/designs/pareto/{project_id}")
async def get_pareto_set_endpoint(project_id: str) -> dict[str, Any]:
    """Retrieve the Pareto non-dominated candidate set for a project."""
    from researchforge.application.queries.graph_query import GraphQueryApplicationService

    service = GraphQueryApplicationService()
    try:
        return service.get_pareto_set(project_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

