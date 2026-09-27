"""
Model comparison and numerical verification workflow service (Phase 2.3).

Orchestrates:
    - ScientificModel registration in the semantic graph
    - Numerical verification
    - Convergence studies
    - Sensitivity analysis
    - Model comparison
    - Evidence generation for falsification

Architecture:
    API / CLI
        ↓
    ModelComparisonWorkflowService   ← this module
        ↓
    Application Query / Command Service
        ↓
    Semantic Graph  (via UnitOfWork / GraphPersistencePort)
        ↓
    Physical DB

Computational operators (verification_operators.py) are pure functions
with no access to persistence, Cognitia, or network.
"""

from __future__ import annotations

import uuid
from typing import Any

from researchforge.application.workflows.experiment_trajectory import ExperimentPlanningWorkflowService
from researchforge.domain.graph.models import ResearchEdge, ResearchGraph, ResearchNode
from researchforge.domain.graph.types import ResearchNodeType, ResearchRelationType
from researchforge.domain.models.evidence import ScientificModel
from researchforge.domain.models.falsification import FalsificationEvaluation, FalsificationStatus
from researchforge.domain.models.hypothesis import Assumption
from researchforge.domain.models.model_comparison import (
    ComparisonMethod,
    ModelComparison,
    ModelComparisonResult,
    SensitivityStudy,
)
from researchforge.domain.models.model_validation import ModelValidationStatus
from researchforge.domain.models.numerical_verification import (
    ConvergenceStudy,
    NumericalVerification,
    ReferenceSolution,
    VerificationType,
)
from researchforge.domain.models.statistics import StatisticalAnalysis
from researchforge.domain.models.verification_operators import (
    compare_wave_models,
    run_convergence_study,
    run_sensitivity_study,
    verify_wave_lattice,
)
from researchforge.domain.models.wave_lattice import WaveLatticeParameters
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.provenance.event_types import ProvenanceEventType
from researchforge.provenance.models import ProvenanceActor
from researchforge.provenance.tracker import ProvenanceTracker


class ModelComparisonWorkflowService:
    """
    Orchestrates model comparison, numerical verification, and sensitivity
    analysis through the ResearchForge semantic graph.
    """

    def __init__(
        self,
        artifacts_dir: str | None = None,
        db_manager: DatabaseManager | None = None,
    ) -> None:
        self.artifacts_dir = artifacts_dir or "./artifacts"
        self._db_manager = db_manager
        self._planner = ExperimentPlanningWorkflowService(
            db_manager=db_manager,
            artifacts_dir=self.artifacts_dir,
        )

    # ------------------------------------------------------------------
    # Scientific model registration
    # ------------------------------------------------------------------

    def register_scientific_model(
        self,
        project_id: str,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        mathematical_form: str = "",
        equations: list[str] | None = None,
        state_variables: list[str] | None = None,
        parameters: dict[str, Any] | None = None,
        assumptions: list[Assumption] | None = None,
        boundary_conditions: dict[str, Any] | None = None,
        initial_conditions: dict[str, Any] | None = None,
        source_terms: dict[str, Any] | None = None,
        validity_scope: str = "",
        validation_status: str = "UNVERIFIED",
    ) -> ScientificModel:
        """
        Register a ScientificModel in the semantic graph.
        """
        model_id = f"model_{uuid.uuid4().hex[:8]}"
        model = ScientificModel(
            id=model_id,
            name=name,
            version=version,
            description=description,
            mathematical_form=mathematical_form,
            equations=equations or [],
            state_variables=state_variables or [],
            parameters=parameters or {},
            assumptions=[a.statement for a in (assumptions or [])],
            boundary_conditions=boundary_conditions or {},
            initial_conditions=initial_conditions or {},
            source_terms=source_terms or {},
            validity_scope=validity_scope,
            validation_status=validation_status,
        )

        with UnitOfWork(self._db_manager) as uow:
            assert uow.semantic_graphs is not None
            graph_id = f"graph_{project_id}"
            if uow.semantic_graphs.graph_exists(graph_id):
                graph = uow.semantic_graphs.load_graph(graph_id)
            else:
                graph = ResearchGraph(graph_id=graph_id)

            tracker = ProvenanceTracker(uow.ledger) if uow.ledger else None
            prov_event = None
            if tracker is not None:
                prov_event = tracker.track(
                    actor=ProvenanceActor.RESEARCHFORGE,
                    actor_id="model_comparison_workflow_v1",
                    operation=ProvenanceEventType.EXPERIMENT_DESIGNED,
                    entity_id=model_id,
                    entity_type="ScientificModel",
                    entity_refs=[project_id],
                    parameters={"name": name, "version": version},
                )
                uow.record_provenance(prov_event)

            node = ResearchNode(
                node_id=model_id,
                node_type=ResearchNodeType.SCIENTIFIC_MODEL,
                entity_id=model_id,
                label=name,
                provenance_ref=prov_event.event_id if prov_event else None,
            )
            graph.add_node(node)

            for assumption in assumptions or []:
                assumption_id = f"assump_{uuid.uuid4().hex[:8]}"
                graph.add_node(
                    ResearchNode(
                        node_id=assumption_id,
                        node_type=ResearchNodeType.ASSUMPTION,
                        entity_id=assumption_id,
                        label=assumption.statement[:80],
                        provenance_ref=prov_event.event_id if prov_event else None,
                    )
                )
                graph.add_edge(
                    ResearchEdge(
                        edge_id=f"edge_model_assump_{model_id}_{assumption_id}",
                        relation_type=ResearchRelationType.HAS_ASSUMPTION,
                        source_node_id=model_id,
                        target_node_id=assumption_id,
                        provenance_ref=prov_event.event_id if prov_event else None,
                    ),
                    validate_nodes=False,
                )

            uow.semantic_graphs.persist_graph(graph)

        return model

    # ------------------------------------------------------------------
    # Numerical verification
    # ------------------------------------------------------------------

    def run_numerical_verification(
        self,
        project_id: str,
        params: WaveLatticeParameters,
        verification_type: VerificationType = VerificationType.ZERO_INPUT,
    ) -> NumericalVerification:
        """
        Run a deterministic numerical verification on the wave lattice operator.
        """
        verification = verify_wave_lattice(params, verification_type=verification_type)

        with UnitOfWork(self._db_manager) as uow:
            assert uow.semantic_graphs is not None
            graph_id = f"graph_{project_id}"
            if uow.semantic_graphs.graph_exists(graph_id):
                graph = uow.semantic_graphs.load_graph(graph_id)
            else:
                from researchforge.domain.graph.models import ResearchGraph
                graph = ResearchGraph(graph_id=graph_id)

            tracker = ProvenanceTracker(uow.ledger) if uow.ledger else None
            prov_event = None
            if tracker is not None:
                prov_event = tracker.track(
                    actor=ProvenanceActor.RESEARCHFORGE,
                    actor_id="model_comparison_workflow_v1",
                    operation=ProvenanceEventType.EXPERIMENT_EXECUTED,
                    entity_id=verification.verification_id,
                    entity_type="NumericalVerification",
                    entity_refs=[project_id],
                    parameters={
                        "verification_type": verification_type.value,
                        "passed": verification.passed,
                    },
                )
                uow.record_provenance(prov_event)

            node = ResearchNode(
                node_id=verification.verification_id,
                node_type=ResearchNodeType.NUMERICAL_VERIFICATION,
                entity_id=verification.verification_id,
                label=f"Verification {verification_type.value}",
                provenance_ref=prov_event.event_id if prov_event else None,
            )
            graph.add_node(node)
            uow.semantic_graphs.persist_graph(graph)

        return verification

    # ------------------------------------------------------------------
    # Convergence study
    # ------------------------------------------------------------------

    def run_convergence_study(
        self,
        project_id: str,
        base_params: WaveLatticeParameters,
        refinement_factors: list[float],
        reference_solution: ReferenceSolution | None = None,
        metric_name: str = "max_displacement",
    ) -> ConvergenceStudy:
        """
        Run a convergence study and record results in the semantic graph.
        """
        study = run_convergence_study(
            base_params=base_params,
            refinement_factors=refinement_factors,
            reference_solution=reference_solution,
            metric_name=metric_name,
        )

        with UnitOfWork(self._db_manager) as uow:
            assert uow.semantic_graphs is not None
            graph_id = f"graph_{project_id}"
            if uow.semantic_graphs.graph_exists(graph_id):
                graph = uow.semantic_graphs.load_graph(graph_id)
            else:
                from researchforge.domain.graph.models import ResearchGraph
                graph = ResearchGraph(graph_id=graph_id)

            tracker = ProvenanceTracker(uow.ledger) if uow.ledger else None
            prov_event = None
            if tracker is not None:
                prov_event = tracker.track(
                    actor=ProvenanceActor.RESEARCHFORGE,
                    actor_id="model_comparison_workflow_v1",
                    operation=ProvenanceEventType.EXPERIMENT_EXECUTED,
                    entity_id=study.study_id,
                    entity_type="ConvergenceStudy",
                    entity_refs=[project_id],
                    parameters={
                        "metric_name": metric_name,
                        "is_convergent": study.is_convergent,
                        "convergence_order": study.convergence_order,
                    },
                )
                uow.record_provenance(prov_event)

            node = ResearchNode(
                node_id=study.study_id,
                node_type=ResearchNodeType.CONVERGENCE_STUDY,
                entity_id=study.study_id,
                label=f"Convergence study ({metric_name})",
                provenance_ref=prov_event.event_id if prov_event else None,
            )
            graph.add_node(node)
            uow.semantic_graphs.persist_graph(graph)

        return study

    # ------------------------------------------------------------------
    # Sensitivity study
    # ------------------------------------------------------------------

    def run_sensitivity_study(
        self,
        project_id: str,
        base_params: WaveLatticeParameters,
        parameter_names: list[str],
        perturbations: dict[str, list[float]],
        observable_names: list[str],
    ) -> SensitivityStudy:
        """
        Run a deterministic sensitivity study and record results.
        """
        study_id = f"sens_{base_params.id}"
        study = run_sensitivity_study(
            base_params=base_params,
            parameter_names=parameter_names,
            perturbations=perturbations,
            observable_names=observable_names,
            study_id=study_id,
        )

        with UnitOfWork(self._db_manager) as uow:
            assert uow.semantic_graphs is not None
            graph_id = f"graph_{project_id}"
            if uow.semantic_graphs.graph_exists(graph_id):
                graph = uow.semantic_graphs.load_graph(graph_id)
            else:
                from researchforge.domain.graph.models import ResearchGraph
                graph = ResearchGraph(graph_id=graph_id)

            tracker = ProvenanceTracker(uow.ledger) if uow.ledger else None
            prov_event = None
            if tracker is not None:
                prov_event = tracker.track(
                    actor=ProvenanceActor.RESEARCHFORGE,
                    actor_id="model_comparison_workflow_v1",
                    operation=ProvenanceEventType.EXPERIMENT_EXECUTED,
                    entity_id=study.study_id,
                    entity_type="SensitivityStudy",
                    entity_refs=[project_id],
                    parameters={
                        "parameter_names": parameter_names,
                        "observable_names": observable_names,
                    },
                )
                uow.record_provenance(prov_event)

            node = ResearchNode(
                node_id=study.study_id,
                node_type=ResearchNodeType.SENSITIVITY_STUDY,
                entity_id=study.study_id,
                label=f"Sensitivity study ({', '.join(parameter_names)})",
                provenance_ref=prov_event.event_id if prov_event else None,
            )
            graph.add_node(node)
            uow.semantic_graphs.persist_graph(graph)

        return study

    # ------------------------------------------------------------------
    # Model comparison
    # ------------------------------------------------------------------

    def compare_models(
        self,
        project_id: str,
        params_a: WaveLatticeParameters,
        params_b: WaveLatticeParameters,
        hypothesis_id: str,
        model_a_id: str,
        model_b_id: str,
        attenuation_threshold: float = 0.9,
    ) -> ModelComparisonResult:
        """
        Compare two wave-lattice model configurations and produce evidence.
        Does NOT automatically declare a winner.
        """
        comparison_id = f"comp_{params_a.id}_{params_b.id}"
        result = compare_wave_models(params_a, params_b)

        # Falsification evaluation based on attenuation_ratio difference
        diff = result.observable_differences.get("attenuation_ratio", 0.0)
        fals_status = (
            FalsificationStatus.SUPPORTED
            if abs(diff) <= attenuation_threshold
            else FalsificationStatus.CONTRADICTED
        )
        falsification = FalsificationEvaluation(
            id=f"fals_{comparison_id}",
            hypothesis_id=hypothesis_id,
            status=fals_status,
            reason=(
                f"Model comparison: attenuation_ratio difference = {diff:.6f} "
                f"({'≤' if fals_status == FalsificationStatus.SUPPORTED else '>'} "
                f"threshold={attenuation_threshold}). "
                f"Physical validation status: {ModelValidationStatus.UNVERIFIED.value}. "
                f"Numerical validation status: {result.validation_status.value}."
            ),
            evidence_refs=[comparison_id],
        )

        analysis = StatisticalAnalysis(
            id=f"analysis_{comparison_id}",
            project_id=project_id,
            experiment_id=comparison_id,
            summary_findings=[
                f"observable_differences: {result.observable_differences}",
                f"error_metrics: {result.error_metrics}",
                f"validation_status: {result.validation_status.value}",
                f"physical_validation_status: {result.physical_validation_status.value}",
            ],
            numerical_metrics={
                **result.observable_differences,
                **result.error_metrics,
            },
        )

        with UnitOfWork(self._db_manager) as uow:
            assert uow.semantic_graphs is not None
            graph_id = f"graph_{project_id}"
            if uow.semantic_graphs.graph_exists(graph_id):
                graph = uow.semantic_graphs.load_graph(graph_id)
            else:
                from researchforge.domain.graph.models import ResearchGraph
                graph = ResearchGraph(graph_id=graph_id)

            tracker = ProvenanceTracker(uow.ledger) if uow.ledger else None
            prov_event = None
            if tracker is not None:
                prov_event = tracker.track(
                    actor=ProvenanceActor.RESEARCHFORGE,
                    actor_id="model_comparison_workflow_v1",
                    operation=ProvenanceEventType.EXPERIMENT_EXECUTED,
                    entity_id=comparison_id,
                    entity_type="ModelComparison",
                    entity_refs=[project_id, hypothesis_id],
                    parameters={
                        "model_a_id": model_a_id,
                        "model_b_id": model_b_id,
                        "comparison_method": ComparisonMethod.OBSERVABLE_DIFFERENCE.value,
                        "attenuation_difference": diff,
                        "falsification_status": fals_status.value,
                    },
                )
                uow.record_provenance(prov_event)

            comparison = ModelComparison(
                id=comparison_id,
                comparison_id=comparison_id,
                name=f"Model comparison: {model_a_id} vs {model_b_id}",
                description="Evidence-centric model comparison; no automatic winner declared.",
                model_ids=[model_a_id, model_b_id],
                comparison_method=ComparisonMethod.OBSERVABLE_DIFFERENCE,
                result_id=result.result_id,
                status="COMPLETED",
            )

            graph.add_node(
                ResearchNode(
                    node_id=comparison_id,
                    node_type=ResearchNodeType.MODEL_COMPARISON,
                    entity_id=comparison_id,
                    label=comparison.name,
                    provenance_ref=prov_event.event_id if prov_event else None,
                )
            )
            for mid in [model_a_id, model_b_id]:
                if graph.has_node(mid):
                    graph.add_edge(
                        ResearchEdge(
                            edge_id=f"edge_comp_{comparison_id}_{mid}",
                            relation_type=ResearchRelationType.COMPARES,
                            source_node_id=comparison_id,
                            target_node_id=mid,
                            provenance_ref=prov_event.event_id if prov_event else None,
                        ),
                        validate_nodes=False,
                    )

            graph.add_node(
                ResearchNode(
                    node_id=analysis.id,
                    node_type=ResearchNodeType.STATISTICAL_ANALYSIS,
                    entity_id=analysis.id,
                    label="Model comparison analysis",
                    provenance_ref=prov_event.event_id if prov_event else None,
                )
            )
            graph.add_node(
                ResearchNode(
                    node_id=falsification.id,
                    node_type=ResearchNodeType.FALSIFICATION_EVALUATION,
                    entity_id=falsification.id,
                    label=f"Falsification {fals_status.value}",
                    provenance_ref=prov_event.event_id if prov_event else None,
                )
            )

            uow.semantic_graphs.persist_graph(graph)

        return result
