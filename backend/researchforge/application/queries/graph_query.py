"""Graph Query Application Service implementing graph query use-cases over GraphPersistencePort."""

from typing import Any

from researchforge.domain.graph.models import ResearchGraph
from researchforge.domain.graph.query import GraphQueryEngine
from researchforge.domain.graph.serialization import serialize_graph
from researchforge.persistence.unit_of_work import UnitOfWork


class GraphQueryApplicationService:
    """Application query service mediating read access to semantic graphs."""

    def __init__(self, uow: UnitOfWork | None = None) -> None:
        self._uow = uow

    # ------------------------------------------------------------------
    # Experiment design read projections
    # ------------------------------------------------------------------

    def get_experiment_design(self, experiment_id: str) -> dict[str, Any]:
        """Retrieve the declarative ExperimentDesign for an experiment."""
        with (self._uow or UnitOfWork()) as uow:
            assert uow.experiments is not None
            assert uow.experiment_designs is not None
            exp = uow.experiments.get(experiment_id)
            if not exp:
                raise KeyError(f"Experiment '{experiment_id}' not found.")
            design_id = exp.parameters.get("design_id")
            if not design_id:
                raise KeyError(f"No design found for experiment '{experiment_id}'.")
            design = uow.experiment_designs.get(design_id)
            if not design:
                raise KeyError(f"Experiment design '{design_id}' not found.")
            return design.model_dump()

    def get_experiment_parameter_space(self, experiment_id: str) -> dict[str, Any]:
        """Retrieve the parameter space specification for an experiment."""
        with (self._uow or UnitOfWork()) as uow:
            assert uow.experiments is not None
            assert uow.experiment_designs is not None
            exp = uow.experiments.get(experiment_id)
            if not exp:
                raise KeyError(f"Experiment '{experiment_id}' not found.")
            design_id = exp.parameters.get("design_id")
            if not design_id:
                raise KeyError(f"No design found for experiment '{experiment_id}'.")
            design = uow.experiment_designs.get(design_id)
            if not design:
                raise KeyError(f"Experiment design '{design_id}' not found.")
            return design.parameter_space.model_dump()

    # ------------------------------------------------------------------
    # Experimental design candidate read projections (Phase 2.4)
    # ------------------------------------------------------------------

    def get_candidate_design(self, candidate_id: str) -> dict[str, Any]:
        """Retrieve an ExperimentalDesignCandidate by ID."""
        with (self._uow or UnitOfWork()) as uow:
            assert uow.candidates is not None
            cand = uow.candidates.get(candidate_id)
            if not cand:
                raise KeyError(f"ExperimentalDesignCandidate '{candidate_id}' not found.")
            return cand.model_dump()

    def list_candidate_designs(self, project_id: str) -> list[dict[str, Any]]:
        """List all candidate designs for a project."""
        with (self._uow or UnitOfWork()) as uow:
            assert uow.candidates is not None
            cands = uow.candidates.list_by_project(project_id)
            return [c.model_dump() for c in cands]

    def get_candidate_evaluation(self, candidate_id: str) -> dict[str, Any]:
        """Retrieve the multi-objective evaluation for a candidate design."""
        with (self._uow or UnitOfWork()) as uow:
            assert uow.evaluations is not None
            ev = uow.evaluations.get_by_candidate(candidate_id)
            if not ev:
                raise KeyError(f"CandidateDesignEvaluation for candidate '{candidate_id}' not found.")
            return ev.model_dump()

    def get_pareto_set(self, project_id: str) -> dict[str, Any]:
        """Retrieve the Pareto non-dominated candidate set for a project."""
        with (self._uow or UnitOfWork()) as uow:
            assert uow.pareto_sets is not None
            ps = uow.pareto_sets.get_by_project(project_id)
            if not ps:
                raise KeyError(f"ParetoCandidateSet for project '{project_id}' not found.")
            return ps.model_dump()

    def get_project_graph(self, project_id: str) -> dict[str, Any]:
        """Retrieve and serialize the complete semantic graph for a project."""
        graph_id = f"graph_{project_id}"
        with (self._uow or UnitOfWork()) as uow:
            assert uow.semantic_graphs is not None
            if not uow.semantic_graphs.graph_exists(graph_id):
                raise KeyError(f"Graph for project '{project_id}' not found.")
            graph = uow.semantic_graphs.load_graph(graph_id)
            return serialize_graph(graph)

    def get_node_neighbors(self, project_id: str, node_id: str) -> dict[str, Any]:
        """Retrieve neighbors and incident edges for a node in a project's semantic graph."""
        graph_id = f"graph_{project_id}"
        with (self._uow or UnitOfWork()) as uow:
            assert uow.semantic_graphs is not None
            if not uow.semantic_graphs.graph_exists(graph_id):
                raise KeyError(f"Graph for project '{project_id}' not found.")
            graph = uow.semantic_graphs.load_graph(graph_id)
            if not graph.has_node(node_id):
                raise KeyError(f"Node '{node_id}' not found in project graph.")

            neighbors = GraphQueryEngine.neighbors(graph, node_id)
            outgoing = GraphQueryEngine.outgoing(graph, node_id)
            incoming = GraphQueryEngine.incoming(graph, node_id)
            return {
                "node_id": node_id,
                "neighbors": [n.model_dump() for n in neighbors],
                "outgoing_edges": [e.model_dump() for e in outgoing],
                "incoming_edges": [e.model_dump() for e in incoming],
            }

    def find_path(self, project_id: str, source_node_id: str, target_node_id: str) -> list[str] | None:
        """Find a directed path between two nodes in the project semantic graph."""
        graph_id = f"graph_{project_id}"
        with (self._uow or UnitOfWork()) as uow:
            assert uow.semantic_graphs is not None
            if not uow.semantic_graphs.graph_exists(graph_id):
                raise KeyError(f"Graph for project '{project_id}' not found.")
            graph = uow.semantic_graphs.load_graph(graph_id)
            return GraphQueryEngine.find_path(graph, source_node_id, target_node_id)

    def get_bounded_subgraph(self, project_id: str, node_ids: set[str], depth: int = 1) -> ResearchGraph:
        """Extract a bounded subgraph around seed nodes."""
        graph_id = f"graph_{project_id}"
        with (self._uow or UnitOfWork()) as uow:
            assert uow.semantic_graphs is not None
            if not uow.semantic_graphs.graph_exists(graph_id):
                raise KeyError(f"Graph for project '{project_id}' not found.")
            return uow.semantic_graphs.load_subgraph(graph_id, root_node_ids=list(node_ids), max_depth=depth)

    def verify_graph_integrity(self, project_id: str) -> bool:
        """Verify the integrity and hash validity of a persisted semantic graph."""
        graph_id = f"graph_{project_id}"
        with (self._uow or UnitOfWork()) as uow:
            assert uow.semantic_graphs is not None
            if not uow.semantic_graphs.graph_exists(graph_id):
                raise KeyError(f"Graph for project '{project_id}' not found.")
            return uow.semantic_graphs.verify_graph_integrity(graph_id)
