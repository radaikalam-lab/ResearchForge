"""Cognitia Advisory Workflow Service enforcing bounded semantic context, hashing, and promotion pathways."""

import uuid

from researchforge.application.queries.graph_query import GraphQueryApplicationService
from researchforge.domain.contracts.cognitia import (
    CognitiaAdvisoryRequest,
    CognitiaAdvisoryResult,
    CognitiaProvider,
    CognitiaSemanticContext,
)
from researchforge.domain.graph.delta import GraphDelta, GraphDeltaItem, GraphDeltaOp
from researchforge.domain.graph.models import ResearchEdge, ResearchNode
from researchforge.domain.graph.serialization import compute_graph_content_hash, serialize_graph
from researchforge.domain.graph.types import ResearchNodeType, ResearchRelationType
from researchforge.domain.models.conclusion import DecisionType, HumanDecision
from researchforge.domain.models.hypothesis import FalsificationCriterion, Hypothesis
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.providers.cognitia.adapter import CognitiaAdapter
from researchforge.providers.registry import global_registry


class CognitiaAdvisoryWorkflowService:
    """Application workflow service governing Cognitia advisory interactions and promotion."""

    def __init__(
        self,
        cognitia_provider: CognitiaProvider | None = None,
        query_service: GraphQueryApplicationService | None = None,
    ) -> None:
        if cognitia_provider is not None:
            self.cognitia = cognitia_provider
        elif global_registry.has("cognitia"):
            self.cognitia = global_registry.get("cognitia")
        else:
            self.cognitia = CognitiaAdapter()
        self.query_service = query_service or GraphQueryApplicationService()

    async def consult_on_subgraph(
        self,
        project_id: str,
        seed_node_ids: set[str],
        operation_type: str = "CRITIQUE",
        depth: int = 1,
    ) -> CognitiaAdvisoryResult:
        """Extract a bounded semantic subgraph, calculate its canonical hash, and query Cognitia for advisory input."""
        subgraph = self.query_service.get_bounded_subgraph(project_id=project_id, node_ids=seed_node_ids, depth=depth)
        context_hash = compute_graph_content_hash(subgraph)
        serialized_subgraph = serialize_graph(subgraph)

        semantic_context = CognitiaSemanticContext(
            id=f"ctx_{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            context_graph_hash=context_hash,
            subgraph=serialized_subgraph,
            provenance_references=list(seed_node_ids),
        )

        request = CognitiaAdvisoryRequest(
            id=f"adv_req_{uuid.uuid4().hex[:8]}",
            request_id=f"adv_req_{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            operation_type=operation_type,
            context_graph_hash=context_hash,
            semantic_context=semantic_context,
            provenance_references=list(seed_node_ids),
        )

        # Cognitia provider returns non-authoritative advisory result
        result = await self.cognitia.consult_advisory(request)
        return result

    def promote_candidate_hypothesis(
        self,
        project_id: str,
        advisory_result: CognitiaAdvisoryResult,
        candidate_hypothesis_text: str,
        gap_id: str,
        decision_actor_id: str,
        decision_notes: str = "Human decision promoting Cognitia advisory hypothesis",
    ) -> tuple[Hypothesis, HumanDecision]:
        """Explicitly promote a Cognitia candidate hypothesis into authoritative domain and graph state.

        Requires an explicit HumanDecision actor and executes within an atomic UnitOfWork transaction.
        """
        hyp_id = f"hyp_{uuid.uuid4().hex[:8]}"
        decision_id = f"dec_{uuid.uuid4().hex[:8]}"

        hypothesis = Hypothesis(
            id=hyp_id,
            project_id=project_id,
            statement=candidate_hypothesis_text,
            mechanism="Mechanism proposed by Cognitia advisory and approved by researcher.",
            assumptions=["Researcher validated exploratory assumption."],
            falsification_criteria=[
                FalsificationCriterion(
                    id=f"fc_{uuid.uuid4().hex[:6]}",
                    description="Response does not deviate significantly from baseline null model.",
                    condition_expression="p_value > 0.05",
                    metric_name="p_value",
                    refutation_threshold=0.05,
                )
            ],
            parent_gap_id=gap_id,
        )

        decision = HumanDecision(
            id=decision_id,
            project_id=project_id,
            decision=DecisionType.APPROVE,
            reviewer_id=decision_actor_id,
            rationale=decision_notes,
            target_entity_id=hyp_id,
            target_entity_type="Hypothesis",
            signature=f"sig_{uuid.uuid4().hex[:12]}",
        )

        # Construct GraphDelta for promotion
        node_hyp = ResearchNode(
            node_id=hyp_id,
            node_type=ResearchNodeType.HYPOTHESIS,
            entity_id=hyp_id,
            label=candidate_hypothesis_text[:80],
            properties={"promoted_from_advisory": advisory_result.result_id},
            provenance_ref=decision_id,
        )
        edge_addresses = ResearchEdge(
            edge_id=f"e_{uuid.uuid4().hex[:8]}",
            relation_type=ResearchRelationType.ADDRESSES,
            source_node_id=hyp_id,
            target_node_id=gap_id,
            provenance_ref=decision_id,
        )

        graph_id = f"graph_{project_id}"
        delta_ops = []

        with UnitOfWork() as uow:
            assert uow.semantic_graphs is not None
            graph = uow.semantic_graphs.load_graph(graph_id)
            if not graph.has_node(gap_id):
                node_gap = ResearchNode(
                    node_id=gap_id,
                    node_type=ResearchNodeType.RESEARCH_GAP,
                    entity_id=gap_id,
                    label=f"Research Gap {gap_id}",
                    provenance_ref=decision_id,
                )
                delta_ops.append(GraphDeltaItem(op=GraphDeltaOp.ADD_NODE, node=node_gap))

            delta_ops.append(GraphDeltaItem(op=GraphDeltaOp.ADD_NODE, node=node_hyp))
            delta_ops.append(GraphDeltaItem(op=GraphDeltaOp.ADD_EDGE, edge=edge_addresses))

            delta = GraphDelta(
                delta_id=f"delta_promote_{uuid.uuid4().hex[:8]}",
                graph_id=graph_id,
                operations=delta_ops,
                provenance_ref=decision_id,
            )

            assert uow.hypotheses is not None
            assert uow.decisions is not None

            uow.hypotheses.save(hypothesis)
            uow.decisions.save(
                decision_id=decision.id,
                project_id=project_id,
                decision=decision.decision.value,
                rationale=decision.rationale,
                hypothesis_id=hyp_id,
                evidence_ids=[],
                analysis_ids=[],
                signer_identity=decision.reviewer_id,
                signature=decision.signature or "sig_valid",
            )
            uow.semantic_graphs.append_graph_delta(graph_id, delta)

        return hypothesis, decision
