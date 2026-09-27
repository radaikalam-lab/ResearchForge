"""
Experimental Design and Candidate Exploration Workflow Service (Phase 2.4).

Orchestrates:
    - Candidate experimental design generation across parameter spaces
    - Multi-model discrimination evaluation and numerical uncertainty accounting
    - Pareto non-dominated candidate set calculation
    - Human-authorized candidate promotion to authoritative ExperimentDesign

Architecture:
    API / CLI
        ↓
    ExperimentalDesignWorkflowService   ← this module
        ↓
    Domain Models & Pure Operators (design_exploration_operators.py)
        ↓
    Semantic Graph  (via UnitOfWork / GraphPersistencePort)
        ↓
    Physical DB

Computational operators are strictly pure: zero DB, zero Cognitia, zero side effects.
"""

from __future__ import annotations

import uuid
from typing import Any

from researchforge.domain.graph.models import ResearchEdge, ResearchGraph, ResearchNode
from researchforge.domain.graph.types import ResearchNodeType, ResearchRelationType
from researchforge.domain.models.computation_plan import ComputationPlan
from researchforge.domain.models.conclusion import DecisionType, HumanDecision
from researchforge.domain.models.design_exploration_operators import (
    compute_pareto_frontier,
    evaluate_candidate_for_model_discrimination,
)
from researchforge.domain.models.design_exploration_operators import (
    generate_candidate_designs as pure_generate_candidate_designs,
)
from researchforge.domain.models.experiment_design import ExperimentDesign
from researchforge.domain.models.experimental_design_candidate import (
    CandidateDesignEvaluation,
    DesignCandidateStatus,
    DesignObjective,
    ExperimentalDesignCandidate,
    ParetoCandidateSet,
    ResourceRequirements,
)
from researchforge.domain.models.model_comparison import SensitivityStudy
from researchforge.domain.models.parameter_space import (
    ParameterDefinition,
    ParameterSpace,
    ParameterType,
    SamplingStrategy,
)
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.provenance.event_types import ProvenanceEventType
from researchforge.provenance.models import ProvenanceActor
from researchforge.provenance.tracker import ProvenanceTracker


class ExperimentalDesignWorkflowService:
    """
    Application workflow service coordinating candidate design generation,
    model discrimination evaluation, and human-gated promotion.
    """

    def __init__(
        self,
        artifacts_dir: str | None = None,
        db_manager: DatabaseManager | None = None,
    ) -> None:
        self.artifacts_dir = artifacts_dir or "./artifacts"
        self._db_manager = db_manager

    # ------------------------------------------------------------------
    # Candidate design generation
    # ------------------------------------------------------------------

    def generate_candidate_designs(
        self,
        project_id: str,
        parameter_space: ParameterSpace,
        model_ids: list[str],
        hypothesis_id: str | None = None,
        research_question_id: str | None = None,
        sensitivity_study_id: str | None = None,
        design_objective: DesignObjective = DesignObjective.MODEL_DISCRIMINATION,
        sampling_strategy: SamplingStrategy | str = SamplingStrategy.GRID,
        sample_count: int = 5,
        random_seed: int | None = 42,
        controlled_variables: dict[str, Any] | None = None,
        target_observables: list[str] | None = None,
        resource_limits: ResourceRequirements | None = None,
    ) -> list[ExperimentalDesignCandidate]:
        """
        Deterministically generate candidate experimental designs and register them in the graph.
        """
        sensitivity_study: SensitivityStudy | None = None

        with UnitOfWork(self._db_manager) as uow:
            # If sensitivity study id provided, look for it in existing graph/records
            if sensitivity_study_id:
                sensitivity_study = SensitivityStudy(
                    study_id=sensitivity_study_id,
                    name="Consumed Sensitivity Study",
                    model_id=model_ids[0] if model_ids else "model_default",
                    base_params={},
                    parameter_names=list(parameter_space.parameters.keys()),
                    observable_names=target_observables or ["transmitted_energy"],
                    sensitivity_metrics=dict.fromkeys(parameter_space.parameters, 1.0),
                )

        # Call pure generator operator
        candidates = pure_generate_candidate_designs(
            project_id=project_id,
            parameter_space=parameter_space,
            model_ids=model_ids,
            hypothesis_id=hypothesis_id,
            research_question_id=research_question_id,
            design_objective=design_objective,
            sampling_strategy=sampling_strategy,
            sample_count=sample_count,
            random_seed=random_seed,
            controlled_variables=controlled_variables,
            target_observables=target_observables,
            sensitivity_study=sensitivity_study,
            resource_limits=resource_limits,
        )

        with UnitOfWork(self._db_manager) as uow:
            assert uow.semantic_graphs is not None
            assert uow.candidates is not None

            graph_id = f"graph_{project_id}"
            if uow.semantic_graphs.graph_exists(graph_id):
                graph = uow.semantic_graphs.load_graph(graph_id)
            else:
                graph = ResearchGraph(graph_id=graph_id)

            tracker = ProvenanceTracker(uow.ledger) if uow.ledger else None

            # Ensure ParameterSpace node exists
            ps_node_id = parameter_space.id if parameter_space.id else f"ps_{project_id}_space"
            if not graph.has_node(ps_node_id):
                graph.add_node(
                    ResearchNode(
                        node_id=ps_node_id,
                        node_type=ResearchNodeType.PARAMETER_SPACE,
                        entity_id=ps_node_id,
                        label=parameter_space.name or "Parameter Space",
                    )
                )

            for cand in candidates:
                prov_event = None
                if tracker is not None:
                    prov_event = tracker.track(
                        actor=ProvenanceActor.RESEARCHFORGE,
                        actor_id="experimental_design_workflow_v1",
                        operation=ProvenanceEventType.EXPERIMENT_DESIGNED,
                        entity_id=cand.candidate_design_id,
                        entity_type="ExperimentalDesignCandidate",
                        entity_refs=[project_id] + ([hypothesis_id] if hypothesis_id else []),
                        parameters={
                            "strategy": cand.design_strategy,
                            "parameters": cand.parameter_assignments,
                            "seed": cand.random_seed,
                        },
                    )
                    uow.record_provenance(prov_event)
                    cand.provenance_ref = prov_event.event_id

                # Save candidate to relational DB
                uow.candidates.save(cand)

                # Add candidate node
                cand_node = ResearchNode(
                    node_id=cand.candidate_design_id,
                    node_type=ResearchNodeType.EXPERIMENTAL_DESIGN_CANDIDATE,
                    entity_id=cand.candidate_design_id,
                    label=f"Candidate {cand.candidate_design_id}",
                    provenance_ref=prov_event.event_id if prov_event else None,
                    metadata={"objective": str(cand.design_objective), "status": str(cand.design_status)},
                )
                graph.add_node(cand_node)

                # Link to ParameterSpace
                edge_id = f"edge_cand_ps_{cand.candidate_design_id}_{ps_node_id}"
                has_ps_edge = any(
                    e.relation_type == ResearchRelationType.HAS_PARAMETER_SPACE
                    and e.source_node_id == cand.candidate_design_id
                    for e in graph.edges.values()
                )
                if not graph.has_edge(edge_id) and not has_ps_edge:
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=edge_id,
                            relation_type=ResearchRelationType.HAS_PARAMETER_SPACE,
                            source_node_id=cand.candidate_design_id,
                            target_node_id=ps_node_id,
                            provenance_ref=prov_event.event_id if prov_event else None,
                        ),
                        validate_nodes=False,
                    )

                # Link from Hypothesis if present
                if hypothesis_id and graph.has_node(hypothesis_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_hyp_cand_{hypothesis_id}_{cand.candidate_design_id}",
                            relation_type=ResearchRelationType.INFORMS_DESIGN,
                            source_node_id=hypothesis_id,
                            target_node_id=cand.candidate_design_id,
                            provenance_ref=prov_event.event_id if prov_event else None,
                        ),
                        validate_nodes=False,
                    )

                # Link from SensitivityStudy if present
                if sensitivity_study_id and graph.has_node(sensitivity_study_id):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_sens_cand_{sensitivity_study_id}_{cand.candidate_design_id}",
                            relation_type=ResearchRelationType.INFORMS_DESIGN,
                            source_node_id=sensitivity_study_id,
                            target_node_id=cand.candidate_design_id,
                            provenance_ref=prov_event.event_id if prov_event else None,
                        ),
                        validate_nodes=False,
                    )

            uow.semantic_graphs.persist_graph(graph)

        return candidates

    # ------------------------------------------------------------------
    # Model discrimination evaluation
    # ------------------------------------------------------------------

    def evaluate_candidate_designs(
        self,
        project_id: str,
        candidate_ids: list[str],
        model_a_id: str,
        model_b_id: str,
        model_a_params_override: dict[str, Any] | None = None,
        model_b_params_override: dict[str, Any] | None = None,
        objectives: list[str] | None = None,
    ) -> tuple[list[CandidateDesignEvaluation], ParetoCandidateSet]:
        """
        Evaluate candidate designs on their model discrimination capability and calculate Pareto frontier.
        """
        evaluations: list[CandidateDesignEvaluation] = []

        with UnitOfWork(self._db_manager) as uow:
            assert uow.semantic_graphs is not None
            assert uow.candidates is not None
            assert uow.evaluations is not None
            assert uow.pareto_sets is not None

            graph_id = f"graph_{project_id}"
            if uow.semantic_graphs.graph_exists(graph_id):
                graph = uow.semantic_graphs.load_graph(graph_id)
            else:
                graph = ResearchGraph(graph_id=graph_id)

            tracker = ProvenanceTracker(uow.ledger) if uow.ledger else None

            # 1. Evaluate each candidate
            for cand_id in candidate_ids:
                cand = uow.candidates.get(cand_id)
                if not cand:
                    raise KeyError(f"ExperimentalDesignCandidate '{cand_id}' not found.")

                ev = evaluate_candidate_for_model_discrimination(
                    candidate=cand,
                    model_a_id=model_a_id,
                    model_b_id=model_b_id,
                    model_a_params_override=model_a_params_override,
                    model_b_params_override=model_b_params_override,
                )

                prov_event = None
                if tracker is not None:
                    prov_event = tracker.track(
                        actor=ProvenanceActor.RESEARCHFORGE,
                        actor_id="experimental_design_workflow_v1",
                        operation=ProvenanceEventType.EXPERIMENT_EXECUTED,
                        entity_id=ev.evaluation_id,
                        entity_type="CandidateDesignEvaluation",
                        entity_refs=[project_id, cand_id, model_a_id, model_b_id],
                        parameters={
                            "discrimination_score": ev.discrimination_score,
                            "expected_difference": ev.expected_observable_difference,
                        },
                    )
                    uow.record_provenance(prov_event)
                    ev.provenance_ref = prov_event.event_id

                # Save evaluation and update candidate status
                uow.evaluations.save(ev)
                cand.design_status = DesignCandidateStatus.EVALUATED
                uow.candidates.save(cand)

                # Add evaluation node and link
                eval_node = ResearchNode(
                    node_id=ev.evaluation_id,
                    node_type=ResearchNodeType.CANDIDATE_DESIGN_EVALUATION,
                    entity_id=ev.evaluation_id,
                    label=f"Evaluation {ev.evaluation_id} (D={ev.discrimination_score:.2f})",
                    provenance_ref=prov_event.event_id if prov_event else None,
                )
                graph.add_node(eval_node)

                graph.add_edge(
                    ResearchEdge(
                        edge_id=f"edge_eval_cand_{ev.evaluation_id}_{cand_id}",
                        relation_type=ResearchRelationType.EVALUATES_CANDIDATE,
                        source_node_id=ev.evaluation_id,
                        target_node_id=cand_id,
                        provenance_ref=prov_event.event_id if prov_event else None,
                    ),
                    validate_nodes=False,
                )
                evaluations.append(ev)

            # 2. Compute Pareto Frontier
            pareto_set = compute_pareto_frontier(
                project_id=project_id,
                evaluations=evaluations,
                objectives=objectives,
            )
            uow.pareto_sets.save(pareto_set)

            # Add Pareto node and link to non-dominated candidates
            pareto_node = ResearchNode(
                node_id=pareto_set.set_id,
                node_type=ResearchNodeType.PARETO_CANDIDATE_SET,
                entity_id=pareto_set.set_id,
                label=f"Pareto Set ({len(pareto_set.non_dominated_candidate_ids)} non-dominated)",
                metadata={"non_dominated_ids": pareto_set.non_dominated_candidate_ids},
            )
            graph.add_node(pareto_node)

            for non_dom_id in pareto_set.non_dominated_candidate_ids:
                graph.add_edge(
                    ResearchEdge(
                        edge_id=f"edge_pareto_cand_{pareto_set.set_id}_{non_dom_id}",
                        relation_type=ResearchRelationType.INCLUDES_CANDIDATE,
                        source_node_id=pareto_set.set_id,
                        target_node_id=non_dom_id,
                    ),
                    validate_nodes=False,
                )

            uow.semantic_graphs.persist_graph(graph)

        return evaluations, pareto_set

    # ------------------------------------------------------------------
    # Human-gated candidate promotion
    # ------------------------------------------------------------------

    def promote_candidate_to_experiment_design(
        self,
        project_id: str,
        candidate_id: str,
        reviewer_id: str,
        rationale: str,
        experiment_name: str,
        decision_type: DecisionType = DecisionType.APPROVE,
    ) -> tuple[ExperimentDesign, HumanDecision]:
        """
        Promote a candidate design into an authoritative ExperimentDesign via explicit human authorization.
        """
        with UnitOfWork(self._db_manager) as uow:
            assert uow.semantic_graphs is not None
            assert uow.candidates is not None
            assert uow.decisions is not None
            assert uow.experiment_designs is not None
            assert uow.experiments is not None

            cand = uow.candidates.get(candidate_id)
            if not cand:
                raise KeyError(f"ExperimentalDesignCandidate '{candidate_id}' not found.")

            # Record signed HumanDecision
            decision_id = f"dec_{uuid.uuid4().hex[:8]}"
            decision = HumanDecision(
                id=decision_id,
                project_id=project_id,
                decision=decision_type,
                target_entity_id=candidate_id,
                reviewer_id=reviewer_id,
                rationale=rationale,
            )
            decision.sign()
            uow.decisions.save(decision)

            # Construct authoritative ExperimentDesign
            design_id = f"des_{uuid.uuid4().hex[:8]}"
            all_params = {**cand.controlled_variables, **cand.parameter_assignments}

            pdefs: dict[str, ParameterDefinition] = {}
            for k, v in all_params.items():
                pdefs[k] = ParameterDefinition(
                    parameter_name=k,
                    parameter_type=ParameterType.CONTINUOUS if isinstance(v, float) else ParameterType.DISCRETE,
                    default_value=v,
                )

            p_space = ParameterSpace(
                id=f"ps_{uuid.uuid4().hex[:8]}",
                name=f"{experiment_name} Parameter Space",
                parameters=pdefs,
            )

            exp_design = ExperimentDesign(
                id=design_id,
                project_id=project_id,
                hypothesis_id=cand.hypothesis_id or f"hyp_{project_id}_default",
                name=experiment_name,
                description=f"Authoritative design promoted from candidate {candidate_id}. Rationale: {rationale}",
                parameter_space=p_space,
                computation_plan=ComputationPlan(
                    id=f"cp_{uuid.uuid4().hex[:8]}",
                    name=f"{experiment_name} Computation Plan",
                ),
            )
            uow.experiment_designs.save(exp_design)

            # Create operational Experiment
            exp_id = f"exp_{uuid.uuid4().hex[:8]}"
            from researchforge.domain.models.experiment import Experiment

            experiment = Experiment(
                id=exp_id,
                project_id=project_id,
                hypothesis_id=exp_design.hypothesis_id,
                name=experiment_name,
                parameters={"design_id": design_id, **all_params},
            )
            uow.experiments.save(experiment)

            # Update candidate status
            cand.design_status = DesignCandidateStatus.PROMOTED
            uow.candidates.save(cand)

            # Record provenance
            tracker = ProvenanceTracker(uow.ledger) if uow.ledger else None
            prov_event = None
            if tracker is not None:
                prov_event = tracker.track(
                    actor=ProvenanceActor.HUMAN,
                    actor_id=reviewer_id,
                    operation=ProvenanceEventType.DECISION_ACCEPTED,
                    entity_id=design_id,
                    entity_type="ExperimentDesign",
                    entity_refs=[project_id, candidate_id, decision_id],
                    parameters={"rationale": rationale, "experiment_name": experiment_name},
                )
                uow.record_provenance(prov_event)

            # Update Semantic Graph
            graph_id = f"graph_{project_id}"
            if uow.semantic_graphs.graph_exists(graph_id):
                graph = uow.semantic_graphs.load_graph(graph_id)
            else:
                graph = ResearchGraph(graph_id=graph_id)

            # Add decision node
            dec_node = ResearchNode(
                node_id=decision_id,
                node_type=ResearchNodeType.HUMAN_DECISION,
                entity_id=decision_id,
                label=f"Human Decision: {decision_type.value}",
                provenance_ref=prov_event.event_id if prov_event else None,
            )
            graph.add_node(dec_node)

            # Add experiment design node
            des_node = ResearchNode(
                node_id=design_id,
                node_type=ResearchNodeType.EXPERIMENT_DESIGN,
                entity_id=design_id,
                label=experiment_name,
                provenance_ref=prov_event.event_id if prov_event else None,
            )
            graph.add_node(des_node)

            # Link candidate PROMOTED_TO ExperimentDesign
            graph.add_edge(
                ResearchEdge(
                    edge_id=f"edge_cand_promoted_{candidate_id}_{design_id}",
                    relation_type=ResearchRelationType.PROMOTED_TO,
                    source_node_id=candidate_id,
                    target_node_id=design_id,
                    provenance_ref=prov_event.event_id if prov_event else None,
                ),
                validate_nodes=False,
            )

            # Link HumanDecision INFORMS design / decision
            graph.add_edge(
                ResearchEdge(
                    edge_id=f"edge_dec_des_{decision_id}_{design_id}",
                    relation_type=ResearchRelationType.ESTABLISHES,
                    source_node_id=decision_id,
                    target_node_id=des_node.node_id,
                    provenance_ref=prov_event.event_id if prov_event else None,
                ),
                validate_nodes=False,
            )

            uow.semantic_graphs.persist_graph(graph)

        return exp_design, decision
