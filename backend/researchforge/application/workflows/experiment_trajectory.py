"""Experiment and Computation Planning Workflow Service (Phase 2)."""

import uuid
from pathlib import Path

from researchforge.domain.graph.models import ResearchEdge, ResearchGraph, ResearchNode
from researchforge.domain.graph.types import ResearchNodeType, ResearchRelationType
from researchforge.domain.graph.validator import validate_graph
from researchforge.domain.models.computation_plan import (
    AnalysisSpecification,
    ComputationPlan,
    DatasetSpecification,
    ExecutionSpecification,
)
from researchforge.domain.models.experiment import Experiment, ExperimentType
from researchforge.domain.models.experiment_design import ExperimentDesign
from researchforge.domain.models.parameter_space import (
    ParameterConstraint,
    ParameterDefinition,
    ParameterSpace,
    SamplingStrategy,
)
from researchforge.domain.state_machine import ResearchLifecycleState
from researchforge.persistence.database import DatabaseManager, get_db_manager
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.provenance.event_types import ProvenanceEventType
from researchforge.provenance.models import ProvenanceActor
from researchforge.provenance.tracker import ProvenanceTracker


class ExperimentPlanningWorkflowService:
    """Orchestrates Phase 2 experiment design, parameter space, and computation planning."""

    def __init__(
        self,
        db_manager: DatabaseManager | None = None,
        artifacts_dir: Path | str = "./artifacts",
    ) -> None:
        self.db_manager = db_manager or get_db_manager()
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    async def plan_experiment_trajectory(
        self,
        project_id: str,
        hypothesis_id: str,
        experiment_name: str,
        parameter_definitions: list[ParameterDefinition] | None = None,
        constraints: list[ParameterConstraint] | None = None,
        sampling_strategy: SamplingStrategy = SamplingStrategy.GRID,
        sample_count: int = 50,
        execution_spec: ExecutionSpecification | None = None,
        dataset_specs: list[DatasetSpecification] | None = None,
        analysis_specs: list[AnalysisSpecification] | None = None,
    ) -> ExperimentDesign:
        """Design an experiment connected to a hypothesis, parameter space, and computation plan."""
        with UnitOfWork(self.db_manager) as uow:
            tracker = ProvenanceTracker(uow.ledger) if uow.ledger else None
            # 1. Verify existence of project and hypothesis
            assert uow.projects is not None
            assert uow.hypotheses is not None
            assert uow.experiments is not None
            assert uow.experiment_designs is not None
            assert uow.semantic_graphs is not None
            assert tracker is not None

            proj = uow.projects.get(project_id)
            if not proj:
                raise KeyError(f"Project '{project_id}' not found.")

            hyp = uow.hypotheses.get(hypothesis_id)
            if not hyp:
                raise KeyError(f"Hypothesis '{hypothesis_id}' not found.")

            # Load or initialize project semantic graph
            graph_id = f"graph_{project_id}"
            if uow.semantic_graphs.graph_exists(graph_id):
                graph = uow.semantic_graphs.load_graph(graph_id)
            else:
                graph = ResearchGraph(graph_id=graph_id)
                # Seed with project and hypothesis nodes
                graph.add_node(
                    ResearchNode(
                        node_id=proj.id,
                        node_type=ResearchNodeType.PROJECT,
                        entity_id=proj.id,
                        label=proj.title,
                    )
                )
                graph.add_node(
                    ResearchNode(
                        node_id=hyp.id,
                        node_type=ResearchNodeType.HYPOTHESIS,
                        entity_id=hyp.id,
                        label=hyp.statement,
                    )
                )

            # 2. Construct ParameterSpace
            ps_id = f"ps_{uuid.uuid4().hex[:8]}"
            params_dict = {p.parameter_name: p for p in (parameter_definitions or [])}
            param_space = ParameterSpace(
                id=ps_id,
                name=f"{experiment_name} Parameter Space",
                description=f"Exploration parameter space for {experiment_name}",
                parameters=params_dict,
                constraints=constraints or [],
                sampling_strategy=sampling_strategy,
                sample_count=sample_count,
            )

            # 3. Construct ComputationPlan
            cp_id = f"cp_{uuid.uuid4().hex[:8]}"
            exec_spec = execution_spec or ExecutionSpecification(
                id=f"exec_{uuid.uuid4().hex[:8]}",
                entrypoint_command="python -m simulation.run",
            )
            ds_specs = dataset_specs or [
                DatasetSpecification(
                    id=f"ds_{uuid.uuid4().hex[:8]}",
                    name="run_measurements.csv",
                    expected_columns=["parameter_x", "response_y", "residual"],
                )
            ]
            an_specs = analysis_specs or [
                AnalysisSpecification(
                    id=f"an_{uuid.uuid4().hex[:8]}",
                    name="OLS Falsification Regression",
                    target_variables=["response_y"],
                )
            ]

            comp_plan = ComputationPlan(
                id=cp_id,
                name=f"{experiment_name} Computation Plan",
                execution_spec=exec_spec,
                dataset_specs=ds_specs,
                analysis_specs=an_specs,
            )

            # 4. Construct Experiment & ExperimentDesign
            design_id = f"design_{uuid.uuid4().hex[:8]}"
            crit_ids = [c.id for c in hyp.falsification_criteria]
            design = ExperimentDesign(
                id=design_id,
                project_id=project_id,
                hypothesis_id=hypothesis_id,
                name=f"{experiment_name} Design",
                description=f"Declarative design protocol for {experiment_name}",
                parameter_space=param_space,
                computation_plan=comp_plan,
                falsification_criteria_refs=crit_ids,
            )

            exp_id = f"exp_{uuid.uuid4().hex[:8]}"
            experiment = Experiment(
                id=exp_id,
                project_id=project_id,
                hypothesis_id=hypothesis_id,
                name=experiment_name,
                description=design.description,
                experiment_type=ExperimentType.NUMERICAL_EXPERIMENT,
                parameters={"design_id": design_id, "sample_count": sample_count},
            )

            # 5. Build Semantic Graph Nodes & Edges
            # Ensure Project and Hypothesis Nodes are present
            if not graph.has_node(proj.id):
                graph.add_node(ResearchNode(node_id=proj.id, node_type=ResearchNodeType.PROJECT, entity_id=proj.id))
            if not graph.has_node(hyp.id):
                graph.add_node(ResearchNode(node_id=hyp.id, node_type=ResearchNodeType.HYPOTHESIS, entity_id=hyp.id))

            # Add Experiment & Design Nodes
            graph.add_node(
                ResearchNode(
                    node_id=exp_id,
                    node_type=ResearchNodeType.EXPERIMENT,
                    entity_id=exp_id,
                    label=experiment.name,
                )
            )
            graph.add_node(
                ResearchNode(
                    node_id=design_id,
                    node_type=ResearchNodeType.EXPERIMENT_DESIGN,
                    entity_id=design_id,
                    label=design.name,
                )
            )
            graph.add_node(
                ResearchNode(
                    node_id=ps_id,
                    node_type=ResearchNodeType.PARAMETER_SPACE,
                    entity_id=ps_id,
                    label=param_space.name,
                )
            )
            graph.add_node(
                ResearchNode(
                    node_id=cp_id,
                    node_type=ResearchNodeType.COMPUTATION_PLAN,
                    entity_id=cp_id,
                    label=comp_plan.name,
                )
            )
            graph.add_node(
                ResearchNode(
                    node_id=exec_spec.id,
                    node_type=ResearchNodeType.EXECUTION_SPECIFICATION,
                    entity_id=exec_spec.id,
                    label=exec_spec.backend_type.value,
                )
            )

            # Add Parameter Definition & Constraint Nodes
            for p_def in param_space.parameters.values():
                p_node_id = f"param_{p_def.id}"
                graph.add_node(
                    ResearchNode(
                        node_id=p_node_id,
                        node_type=ResearchNodeType.PARAMETER_DEFINITION,
                        entity_id=p_def.id,
                        label=p_def.parameter_name,
                    )
                )
                graph.add_edge(
                    ResearchEdge(
                        edge_id=f"edge_ps_param_{ps_id}_{p_node_id}",
                        relation_type=ResearchRelationType.CONTAINS_PARAMETER,
                        source_node_id=ps_id,
                        target_node_id=p_node_id,
                        provenance_ref=f"prov_param_{p_def.id}",
                    ),
                    validate_nodes=False,
                )

            for p_con in param_space.constraints:
                c_node_id = f"con_{p_con.id}"
                graph.add_node(
                    ResearchNode(
                        node_id=c_node_id,
                        node_type=ResearchNodeType.PARAMETER_CONSTRAINT,
                        entity_id=p_con.id,
                        label=p_con.name,
                    )
                )
                graph.add_edge(
                    ResearchEdge(
                        edge_id=f"edge_ps_con_{ps_id}_{c_node_id}",
                        relation_type=ResearchRelationType.CONSTRAINED_BY,
                        source_node_id=ps_id,
                        target_node_id=c_node_id,
                        provenance_ref=f"prov_con_{p_con.id}",
                    ),
                    validate_nodes=False,
                )

            # Add Dataset & Analysis Specification Nodes
            for ds in ds_specs:
                graph.add_node(
                    ResearchNode(
                        node_id=ds.id,
                        node_type=ResearchNodeType.DATASET_SPECIFICATION,
                        entity_id=ds.id,
                        label=ds.name,
                    )
                )
                graph.add_edge(
                    ResearchEdge(
                        edge_id=f"edge_cp_ds_{cp_id}_{ds.id}",
                        relation_type=ResearchRelationType.SPECIFIES_DATASET,
                        source_node_id=cp_id,
                        target_node_id=ds.id,
                        provenance_ref=f"prov_ds_{ds.id}",
                    ),
                    validate_nodes=False,
                )

            for an in an_specs:
                graph.add_node(
                    ResearchNode(
                        node_id=an.id,
                        node_type=ResearchNodeType.ANALYSIS_SPECIFICATION,
                        entity_id=an.id,
                        label=an.name,
                    )
                )
                graph.add_edge(
                    ResearchEdge(
                        edge_id=f"edge_cp_an_{cp_id}_{an.id}",
                        relation_type=ResearchRelationType.SPECIFIES_ANALYSIS,
                        source_node_id=cp_id,
                        target_node_id=an.id,
                        provenance_ref=f"prov_an_{an.id}",
                    ),
                    validate_nodes=False,
                )

            # Link Primary Semantic Relationships
            # 1. Hypothesis <-> Experiment
            e_prov = tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id="experiment_planner_v2",
                operation=ProvenanceEventType.EXPERIMENT_DESIGNED,
                entity_id=exp_id,
                entity_type="Experiment",
                entity_refs=[project_id, hypothesis_id, design_id],
                parameters={"name": experiment_name, "sample_count": sample_count},
            )
            uow.record_provenance(e_prov)

            graph.add_edge(
                ResearchEdge(
                    edge_id=f"edge_hyp_tested_{hyp.id}_{exp_id}",
                    relation_type=ResearchRelationType.TESTED_BY,
                    source_node_id=hyp.id,
                    target_node_id=exp_id,
                    provenance_ref=e_prov.event_id,
                ),
                validate_nodes=False,
            )
            graph.add_edge(
                ResearchEdge(
                    edge_id=f"edge_exp_tests_{exp_id}_{hyp.id}",
                    relation_type=ResearchRelationType.TESTS,
                    source_node_id=exp_id,
                    target_node_id=hyp.id,
                    provenance_ref=e_prov.event_id,
                ),
                validate_nodes=False,
            )
            graph.add_edge(
                ResearchEdge(
                    edge_id=f"edge_exp_design_{exp_id}_{design_id}",
                    relation_type=ResearchRelationType.HAS_DESIGN,
                    source_node_id=exp_id,
                    target_node_id=design_id,
                    provenance_ref=e_prov.event_id,
                ),
                validate_nodes=False,
            )
            graph.add_edge(
                ResearchEdge(
                    edge_id=f"edge_design_ps_{design_id}_{ps_id}",
                    relation_type=ResearchRelationType.HAS_PARAMETER_SPACE,
                    source_node_id=design_id,
                    target_node_id=ps_id,
                    provenance_ref=e_prov.event_id,
                ),
                validate_nodes=False,
            )
            graph.add_edge(
                ResearchEdge(
                    edge_id=f"edge_design_cp_{design_id}_{cp_id}",
                    relation_type=ResearchRelationType.HAS_COMPUTATION_PLAN,
                    source_node_id=design_id,
                    target_node_id=cp_id,
                    provenance_ref=e_prov.event_id,
                ),
                validate_nodes=False,
            )
            graph.add_edge(
                ResearchEdge(
                    edge_id=f"edge_cp_exec_{cp_id}_{exec_spec.id}",
                    relation_type=ResearchRelationType.SPECIFIES_EXECUTION,
                    source_node_id=cp_id,
                    target_node_id=exec_spec.id,
                    provenance_ref=e_prov.event_id,
                ),
                validate_nodes=False,
            )

            # 6. Validate Graph Invariants
            val_res = validate_graph(graph)
            if not val_res.is_valid:
                raise ValueError(f"Generated experiment semantic graph failed validation: {'; '.join(val_res.errors)}")

            # 7. Persist Graph and Domain Entities
            uow.semantic_graphs.persist_graph(graph)
            uow.experiments.save(experiment)
            uow.experiment_designs.save(design)

            proj.state = ResearchLifecycleState.EXPERIMENT_DESIGNED
            uow.projects.save(proj)

            return design
