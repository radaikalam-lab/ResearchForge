"""
Wave Lattice Experiment Workflow Service (Phase 2.2).

Governs the full lifecycle of a 1-D damped-wave lattice experiment through
the ResearchForge semantic graph and experiment architecture.

Architecture boundary:
    API / CLI
        ↓
    WaveLatticeWorkflowService   ← this module
        ↓
    ExperimentPlanningWorkflowService  (for design/planning)
        ↓
    Semantic Graph  (via UnitOfWork / GraphPersistencePort)
        ↓
    Physical DB

The wave operator itself (domain/models/wave_lattice.py) is pure and has
NO access to persistence, Cognitia, or network.  All persistence is owned
here through the existing UnitOfWork transactional boundary.

Replay is deterministic: given the same WaveLatticeParameters, the operator
produces the same output_hash regardless of Cognitia, network, or LLM state.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from researchforge.application.workflows.experiment_trajectory import ExperimentPlanningWorkflowService
from researchforge.domain.base import canonical_json_dumps
from researchforge.domain.graph.delta import GraphDelta, GraphDeltaItem, GraphDeltaOp
from researchforge.domain.graph.models import ResearchEdge, ResearchNode
from researchforge.domain.graph.types import ResearchNodeType, ResearchRelationType
from researchforge.domain.models.computation_plan import (
    AnalysisSpecification,
    DatasetSpecification,
    ExecutionBackendType,
    ExecutionSpecification,
)
from researchforge.domain.models.experiment import Experiment, ExperimentResult, ExperimentRun, ExperimentType
from researchforge.domain.models.falsification import FalsificationEvaluation, FalsificationStatus
from researchforge.domain.models.parameter_space import (
    ParameterConstraint,
    ParameterDefinition,
    ParameterType,
    SamplingStrategy,
)
from researchforge.domain.models.statistics import StatisticalAnalysis
from researchforge.domain.models.wave_lattice import (
    BoundaryCondition,
    WaveLatticeObservables,
    WaveLatticeParameters,
    simulate_1d_damped_wave_lattice,
)
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.provenance.event_types import ProvenanceEventType
from researchforge.provenance.models import ProvenanceActor
from researchforge.provenance.tracker import ProvenanceTracker

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class WaveLatticeExperimentResult:
    """Container for a completed wave lattice experiment cycle."""

    experiment: Experiment
    run: ExperimentRun
    result: ExperimentResult
    observables: WaveLatticeObservables
    analysis: StatisticalAnalysis
    falsification: FalsificationEvaluation
    graph_delta: GraphDelta
    provenance_event_id: str


# ---------------------------------------------------------------------------
# Wave lattice parameter builder
# ---------------------------------------------------------------------------


def _build_wave_parameter_definitions(
    params: WaveLatticeParameters,
) -> list[ParameterDefinition]:
    """Map WaveLatticeParameters fields to typed ParameterDefinition list."""
    return [
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="nodes",
            parameter_type=ParameterType.DISCRETE,
            default_value=params.nodes,
            min_value=4,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="time_steps",
            parameter_type=ParameterType.DISCRETE,
            default_value=params.time_steps,
            min_value=2,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="dx",
            parameter_type=ParameterType.CONTINUOUS,
            default_value=params.dx,
            min_value=1e-6,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="dt",
            parameter_type=ParameterType.CONTINUOUS,
            default_value=params.dt,
            min_value=1e-9,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="density",
            parameter_type=ParameterType.CONTINUOUS,
            default_value=params.density,
            min_value=1e-9,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="stiffness",
            parameter_type=ParameterType.CONTINUOUS,
            default_value=params.stiffness,
            min_value=1e-9,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="damping",
            parameter_type=ParameterType.CONTINUOUS,
            default_value=params.damping,
            min_value=0.0,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="core_start",
            parameter_type=ParameterType.DISCRETE,
            default_value=params.core_start,
            min_value=0,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="core_end",
            parameter_type=ParameterType.DISCRETE,
            default_value=params.core_end,
            min_value=1,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="core_density",
            parameter_type=ParameterType.CONTINUOUS,
            default_value=params.core_density,
            min_value=1e-9,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="core_stiffness",
            parameter_type=ParameterType.CONTINUOUS,
            default_value=params.core_stiffness,
            min_value=1e-9,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="core_damping",
            parameter_type=ParameterType.CONTINUOUS,
            default_value=params.core_damping,
            min_value=0.0,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="source_amplitude",
            parameter_type=ParameterType.CONTINUOUS,
            default_value=params.source_amplitude,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="source_location",
            parameter_type=ParameterType.DISCRETE,
            default_value=params.source_location,
            min_value=0,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="source_duration",
            parameter_type=ParameterType.DISCRETE,
            default_value=params.source_duration,
            min_value=1,
        ),
        ParameterDefinition(
            id=f"param_{uuid.uuid4().hex[:6]}",
            parameter_name="boundary_condition",
            parameter_type=ParameterType.CATEGORICAL,
            default_value=params.boundary_condition.value,
            allowed_values=[bc.value for bc in BoundaryCondition],
        ),
    ]


def _build_cfl_constraint() -> ParameterConstraint:
    return ParameterConstraint(
        id=f"con_{uuid.uuid4().hex[:8]}",
        name="CFL_stability",
        expression="dt <= dx / sqrt(max(stiffness, core_stiffness) / min(density, core_density))",
        description="Courant-Friedrichs-Lewy stability condition for explicit time-stepping",
        parameters_involved=["dt", "dx", "stiffness", "core_stiffness", "density", "core_density"],
    )


# ---------------------------------------------------------------------------
# Workflow service
# ---------------------------------------------------------------------------


class WaveLatticeWorkflowService:
    """
    Orchestrates end-to-end wave lattice experiment lifecycle through
    the ResearchForge semantic graph and experiment architecture.

    This service:
    - registers experiment, design, parameter space, computation plan in the graph
    - calls the pure wave operator to produce observations
    - records results as ExperimentRun, StatisticalAnalysis, FalsificationEvaluation
    - writes all graph mutations through the existing UnitOfWork / GraphPersistencePort
    - records provenance for every authoritative mutation

    The wave operator (simulate_1d_damped_wave_lattice) is invoked OUTSIDE any
    database transaction to maintain the isolation guarantee.
    """

    def __init__(
        self,
        artifacts_dir: Path | str = "./artifacts",
        db_manager: DatabaseManager | None = None,
    ) -> None:
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._db_manager = db_manager
        self._planner = ExperimentPlanningWorkflowService(
            db_manager=db_manager,
            artifacts_dir=artifacts_dir,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def plan_wave_experiment(
        self,
        project_id: str,
        hypothesis_id: str,
        params: WaveLatticeParameters,
        experiment_name: str = "1-D Damped Wave Lattice Experiment",
    ) -> dict[str, Any]:
        """
        Register the wave lattice experiment design in the semantic graph.

        Returns the ExperimentDesign (as dict) with wave_params attached for provenance.
        """
        param_defs = _build_wave_parameter_definitions(params)
        constraints = [_build_cfl_constraint()]

        exec_spec = ExecutionSpecification(
            id=f"exec_{uuid.uuid4().hex[:8]}",
            backend_type=ExecutionBackendType.LOCAL_SANDBOX,
            entrypoint_command="python -m researchforge.domain.models.wave_lattice",
            deterministic_required=True,
            network_isolated=True,
        )
        ds_specs = [
            DatasetSpecification(
                id=f"ds_{uuid.uuid4().hex[:8]}",
                name="wave_lattice_observables.json",
                schema_format="JSON",
                expected_columns=[
                    "max_displacement",
                    "max_core_displacement",
                    "incident_energy",
                    "reflected_energy",
                    "transmitted_energy",
                    "dissipated_energy",
                    "core_energy",
                    "attenuation_ratio",
                ],
            )
        ]
        an_specs = [
            AnalysisSpecification(
                id=f"an_{uuid.uuid4().hex[:8]}",
                name="Wave Attenuation Analysis",
                analysis_type="RATIO_TEST",
                statistical_tests=["ATTENUATION_RATIO_THRESHOLD"],
                target_variables=["attenuation_ratio", "core_energy", "dissipated_energy"],
            )
        ]

        design = await self._planner.plan_experiment_trajectory(
            project_id=project_id,
            hypothesis_id=hypothesis_id,
            experiment_name=experiment_name,
            parameter_definitions=param_defs,
            constraints=constraints,
            sampling_strategy=SamplingStrategy.MANUAL_LIST,
            sample_count=1,
            execution_spec=exec_spec,
            dataset_specs=ds_specs,
            analysis_specs=an_specs,
        )
        design_dict = design.model_dump(mode="json")
        design_dict["wave_params"] = params.model_dump(mode="json")
        return design_dict

    async def run_wave_experiment(
        self,
        project_id: str,
        hypothesis_id: str,
        params: WaveLatticeParameters,
        db_manager: DatabaseManager | None = None,
        attenuation_threshold: float = 0.5,
        experiment_name: str = "1-D Damped Wave Lattice Run",
    ) -> WaveLatticeExperimentResult:
        """
        Execute the wave lattice computation and record all results through the
        ResearchForge semantic graph.

        attenuation_threshold: falsification criterion — attenuation_ratio > threshold
            means the heterogeneous region does NOT provide sufficient attenuation
            relative to this criterion.

        The wave operator is called OUTSIDE the database transaction to maintain
        the isolation guarantee: computation is independent of persistence.
        """
        # === Step 1: Run the pure wave operator (NO database access) ===
        raw_output = simulate_1d_damped_wave_lattice(params)
        obs_dict = raw_output["observables"]
        observables = WaveLatticeObservables.model_validate(obs_dict)

        # === Step 2: Persist results through UnitOfWork (graph boundary) ===
        effective_db = db_manager or self._db_manager
        result = self._persist_run_results(
            project_id=project_id,
            hypothesis_id=hypothesis_id,
            params=params,
            raw_output=raw_output,
            observables=observables,
            attenuation_threshold=attenuation_threshold,
            experiment_name=experiment_name,
            db_manager=effective_db,
        )
        return result

    # ------------------------------------------------------------------
    # Internal persistence (application boundary)
    # ------------------------------------------------------------------

    def _persist_run_results(
        self,
        project_id: str,
        hypothesis_id: str,
        params: WaveLatticeParameters,
        raw_output: dict[str, Any],
        observables: WaveLatticeObservables,
        attenuation_threshold: float,
        experiment_name: str,
        db_manager: DatabaseManager | None = None,
    ) -> WaveLatticeExperimentResult:
        """Persist wave experiment results atomically via UnitOfWork."""
        exp_id = f"exp_{uuid.uuid4().hex[:8]}"
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        result_id = f"res_{uuid.uuid4().hex[:8]}"
        analysis_id = f"analysis_{uuid.uuid4().hex[:8]}"
        fals_id = f"fals_{uuid.uuid4().hex[:8]}"

        # Canonical input hash (reproducibility)
        param_canonical = canonical_json_dumps(params.model_dump(mode="json"))
        input_hash = hashlib.sha256(param_canonical.encode("utf-8")).hexdigest()

        # Falsification evaluation
        # Criterion: attenuation_ratio > threshold → hypothesis NOT supported
        fals_status = (
            FalsificationStatus.SUPPORTED
            if observables.attenuation_ratio <= attenuation_threshold
            else FalsificationStatus.CONTRADICTED
        )
        falsification = FalsificationEvaluation(
            id=fals_id,
            hypothesis_id=hypothesis_id,
            status=fals_status,
            reason=(
                f"attenuation_ratio={observables.attenuation_ratio:.4f} "
                f"({'≤' if fals_status == FalsificationStatus.SUPPORTED else '>'} "
                f"threshold={attenuation_threshold}). "
                f"core_energy={observables.core_energy:.6f}, "
                f"dissipated_energy={observables.dissipated_energy:.6f}."
            ),
            evidence_refs=[run_id],
        )

        # Statistical analysis
        analysis = StatisticalAnalysis(
            id=analysis_id,
            project_id=project_id,
            experiment_id=exp_id,
            dataset_ids=[run_id],
            summary_findings=[
                f"max_displacement={observables.max_displacement:.6f}",
                f"max_core_displacement={observables.max_core_displacement:.6f}",
                f"attenuation_ratio={observables.attenuation_ratio:.6f}",
                f"incident_energy={observables.incident_energy:.6f}",
                f"dissipated_energy={observables.dissipated_energy:.6f}",
                f"core_energy={observables.core_energy:.6f}",
            ],
            numerical_metrics={
                "max_displacement": observables.max_displacement,
                "max_core_displacement": observables.max_core_displacement,
                "max_velocity": observables.max_velocity,
                "incident_energy": observables.incident_energy,
                "reflected_energy": observables.reflected_energy,
                "transmitted_energy": observables.transmitted_energy,
                "dissipated_energy": observables.dissipated_energy,
                "core_energy": observables.core_energy,
                "attenuation_ratio": observables.attenuation_ratio,
                "attenuation_threshold": attenuation_threshold,
                "falsification_status": fals_status.value,
                "input_hash": observables.input_hash,
                "output_hash": observables.output_hash,
            },
        )

        # ExperimentResult
        experiment_result = ExperimentResult(
            id=result_id,
            run_id=run_id,
            metrics={
                "attenuation_ratio": observables.attenuation_ratio,
                "max_displacement": observables.max_displacement,
                "max_core_displacement": observables.max_core_displacement,
                "core_energy": observables.core_energy,
                "dissipated_energy": observables.dissipated_energy,
                "incident_energy": observables.incident_energy,
            },
            output_hash=observables.output_hash,
        )

        # ExperimentRun
        experiment_run = ExperimentRun(
            id=run_id,
            experiment_id=exp_id,
            project_id=project_id,
            status="COMPLETED",
            input_hash=input_hash,
            output_hash=observables.output_hash,
            result=experiment_result,
            results={"observables": raw_output["observables"]},
            environment_metadata={
                "operator_version": raw_output["operator_version"],
                "computation_version": params.computation_version,
            },
        )

        # Experiment entity
        experiment = Experiment(
            id=exp_id,
            project_id=project_id,
            hypothesis_id=hypothesis_id,
            name=experiment_name,
            description=f"1-D heterogeneous damped-wave experiment. label={params.experiment_label}",
            experiment_type=ExperimentType.NUMERICAL_EXPERIMENT,
            parameters={
                "wave_params": params.model_dump(mode="json"),
                "attenuation_threshold": attenuation_threshold,
            },
            run_ids=[run_id],
        )

        # === Atomic persistence within UnitOfWork ===
        with UnitOfWork(db_manager) as uow:
            assert uow.experiments is not None
            assert uow.semantic_graphs is not None

            tracker = ProvenanceTracker(uow.ledger)

            # Load or create project semantic graph
            graph_id = f"graph_{project_id}"
            if uow.semantic_graphs.graph_exists(graph_id):
                graph = uow.semantic_graphs.load_graph(graph_id)
            else:
                from researchforge.domain.graph.models import ResearchGraph
                graph = ResearchGraph(graph_id=graph_id)

            # Provenance event for this execution
            prov_event = tracker.track(
                actor=ProvenanceActor.RESEARCHFORGE,
                actor_id="wave_lattice_workflow_v1",
                operation=ProvenanceEventType.EXPERIMENT_EXECUTED,
                entity_id=run_id,
                entity_type="ExperimentRun",
                entity_refs=[project_id, hypothesis_id, exp_id],
                parameters={
                    "operator_version": raw_output["operator_version"],
                    "input_hash": input_hash,
                    "output_hash": observables.output_hash,
                    "attenuation_ratio": observables.attenuation_ratio,
                    "falsification_status": fals_status.value,
                },
            )
            uow.record_provenance(prov_event)

            # --- Graph nodes ---
            node_defs: list[tuple[str, ResearchNodeType, str]] = [
                (exp_id, ResearchNodeType.EXPERIMENT, experiment_name),
                (run_id, ResearchNodeType.EXPERIMENT_RUN, f"Run {run_id}"),
                (analysis_id, ResearchNodeType.STATISTICAL_ANALYSIS, "Wave Attenuation Analysis"),
                (fals_id, ResearchNodeType.FALSIFICATION_EVALUATION, f"Falsification {fals_status.value}"),
            ]
            for nid, ntype, nlabel in node_defs:
                if not graph.has_node(nid):
                    graph.add_node(
                        ResearchNode(
                            node_id=nid,
                            node_type=ntype,
                            entity_id=nid,
                            label=nlabel,
                            provenance_ref=prov_event.event_id,
                        )
                    )

            # --- Graph edges ---
            def _edge(src: str, rel: ResearchRelationType, tgt: str) -> ResearchEdge:
                return ResearchEdge(
                    edge_id=f"edge_{rel.value.lower()}_{src[:8]}_{tgt[:8]}_{uuid.uuid4().hex[:4]}",
                    relation_type=rel,
                    source_node_id=src,
                    target_node_id=tgt,
                    provenance_ref=prov_event.event_id,
                )

            edges_to_add: list[tuple[str, ResearchRelationType, str]] = []

            # Hypothesis ↔ Experiment
            if graph.has_node(hypothesis_id):
                edges_to_add.append((hypothesis_id, ResearchRelationType.TESTED_BY, exp_id))
                edges_to_add.append((exp_id, ResearchRelationType.TESTS, hypothesis_id))

            # Experiment → Run
            edges_to_add.append((exp_id, ResearchRelationType.EXECUTED_AS, run_id))

            # Analysis → Falsification
            edges_to_add.append((analysis_id, ResearchRelationType.INFORMS_FALSIFICATION, fals_id))

            # Falsification → Hypothesis
            if graph.has_node(hypothesis_id):
                edges_to_add.append((fals_id, ResearchRelationType.EVALUATES, hypothesis_id))

            # Falsification → Run
            edges_to_add.append((fals_id, ResearchRelationType.EVALUATES, run_id))

            delta_ops = []
            for (src, rel, tgt) in edges_to_add:
                if graph.has_node(src) and graph.has_node(tgt):
                    edge = _edge(src, rel, tgt)
                    delta_ops.append(GraphDeltaItem(op=GraphDeltaOp.ADD_EDGE, edge=edge))
                    graph.add_edge(edge, validate_nodes=False)

            delta = GraphDelta(
                delta_id=f"delta_wave_{uuid.uuid4().hex[:8]}",
                graph_id=graph_id,
                operations=delta_ops,
                provenance_ref=prov_event.event_id,
            )

            # Persist
            uow.experiments.save(experiment)
            uow.semantic_graphs.persist_graph(graph)

        return WaveLatticeExperimentResult(
            experiment=experiment,
            run=experiment_run,
            result=experiment_result,
            observables=observables,
            analysis=analysis,
            falsification=falsification,
            graph_delta=delta,
            provenance_event_id=prov_event.event_id,
        )
