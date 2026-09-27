"""Semantic Graph Invariant & Contract Validator (Phase 0.4)."""

from collections import defaultdict
from dataclasses import dataclass, field

from researchforge.domain.graph.models import ResearchGraph
from researchforge.domain.graph.ontology import ONTOLOGY_RELATION_RULES
from researchforge.domain.graph.types import (
    Cardinality,
    RelationRule,
    ResearchNodeType,
    ResearchRelationType,
)


@dataclass
class GraphValidationResult:
    """Result of semantic graph contract validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_graph(
    graph: ResearchGraph,
    ontology_rules: dict[ResearchRelationType, RelationRule] | None = None,
    strict_provenance: bool = False,
) -> GraphValidationResult:
    """Validate a ResearchGraph against all ontology rules, type constraints, and graph invariants."""
    rules = ontology_rules or ONTOLOGY_RELATION_RULES
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Validate Nodes
    for node_id, node in graph.nodes.items():
        if not node_id or not node.node_id:
            errors.append(f"Node missing node_id: {node}")
            continue
        if node_id != node.node_id:
            errors.append(f"Node key mismatch: dictionary key '{node_id}' != node.node_id '{node.node_id}'")
        if not node.entity_id:
            errors.append(f"Node '{node_id}' has empty entity_id")
        if not isinstance(node.node_type, ResearchNodeType):
            try:
                ResearchNodeType(str(node.node_type))
            except ValueError:
                errors.append(f"Node '{node_id}' has invalid node_type '{node.node_type}'")

    # 2. Validate Edges & Referential Integrity
    outgoing_by_type: dict[ResearchRelationType, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    incoming_by_type: dict[ResearchRelationType, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    seen_edge_signatures: set[tuple[str, str, str]] = set()

    for edge_id, edge in graph.edges.items():
        if not edge_id or not edge.edge_id:
            errors.append(f"Edge missing edge_id: {edge}")
            continue
        if edge_id != edge.edge_id:
            errors.append(f"Edge key mismatch: dictionary key '{edge_id}' != edge.edge_id '{edge.edge_id}'")

        # Referential Integrity
        src_node = graph.nodes.get(edge.source_node_id)
        tgt_node = graph.nodes.get(edge.target_node_id)

        if not src_node:
            errors.append(f"Edge '{edge_id}' references non-existent source node '{edge.source_node_id}'.")
        if not tgt_node:
            errors.append(f"Edge '{edge_id}' references non-existent target node '{edge.target_node_id}'.")

        if not src_node or not tgt_node:
            continue

        # Relation Type Validity
        if not isinstance(edge.relation_type, ResearchRelationType):
            try:
                rel_type = ResearchRelationType(str(edge.relation_type))
            except ValueError:
                errors.append(f"Edge '{edge_id}' has unknown relation_type '{edge.relation_type}'.")
                continue
        else:
            rel_type = edge.relation_type

        rule = rules.get(rel_type)
        if not rule:
            errors.append(f"Edge '{edge_id}' relation '{rel_type}' has no defined ontology rule.")
            continue

        # Type Compatibility (Source & Target)
        if src_node.node_type not in rule.valid_source_types:
            errors.append(
                f"Edge '{edge_id}' ({rel_type}) source '{src_node.node_id}' of type '{src_node.node_type}' "
                f"is not in permitted source types: {[t.value for t in rule.valid_source_types]}"
            )
        if tgt_node.node_type not in rule.valid_target_types:
            errors.append(
                f"Edge '{edge_id}' ({rel_type}) target '{tgt_node.node_id}' of type '{tgt_node.node_type}' "
                f"is not in permitted target types: {[t.value for t in rule.valid_target_types]}"
            )

        # Duplicate Edge Detection (No semantic aliasing)
        sig = (edge.source_node_id, edge.target_node_id, str(rel_type))
        if sig in seen_edge_signatures:
            warnings.append(
                f"Duplicate semantic edge between '{edge.source_node_id}' and '{edge.target_node_id}' "
                f"for relation '{rel_type}' (edge_id: '{edge_id}')."
            )
        seen_edge_signatures.add(sig)

        # Provenance Requirement
        if rule.requires_provenance and not edge.provenance_ref:
            msg = f"Edge '{edge_id}' ({rel_type}) is missing required provenance reference."
            if strict_provenance:
                errors.append(msg)
            else:
                warnings.append(msg)

        # Record for cardinality verification
        outgoing_by_type[rel_type][edge.source_node_id].append(edge.target_node_id)
        incoming_by_type[rel_type][edge.target_node_id].append(edge.source_node_id)

    # 3. Cardinality Verification
    for rel_type, sources_map in outgoing_by_type.items():
        rule = rules.get(rel_type)
        if not rule:
            continue

        targets_map = incoming_by_type[rel_type]

        if rule.cardinality in (Cardinality.ONE_TO_ONE, Cardinality.MANY_TO_ONE):
            # Source can have at most 1 outgoing edge
            for src_id, targets in sources_map.items():
                if len(targets) > 1:
                    errors.append(
                        f"Cardinality violation for relation '{rel_type}' ({rule.cardinality}): "
                        f"source node '{src_id}' has {len(targets)} outgoing edges (max 1)."
                    )

        if rule.cardinality in (Cardinality.ONE_TO_ONE, Cardinality.ONE_TO_MANY):
            # Target can have at most 1 incoming edge
            for tgt_id, sources in targets_map.items():
                if len(sources) > 1:
                    errors.append(
                        f"Cardinality violation for relation '{rel_type}' ({rule.cardinality}): "
                        f"target node '{tgt_id}' has {len(sources)} incoming edges (max 1)."
                    )

    is_valid = len(errors) == 0
    return GraphValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
