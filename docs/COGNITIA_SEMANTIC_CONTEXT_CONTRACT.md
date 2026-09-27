# COGNITIA SEMANTIC CONTEXT CONTRACT

## 1. Scope & Purpose

Cognitia participates in ResearchForge as an external epistemic advisory plane. To prevent context leakage, hallucination of mutable persistence state, and breach of authority boundaries, Cognitia interacts only through bounded, hashed **Semantic Graph Contexts**.

---

## 2. Model Contracts

```python
class CognitiaSemanticContext(DomainModel):
    """Bounded semantic graph context extracted for Cognitia advisory reasoning."""

    project_id: str
    context_graph_hash: str
    subgraph: dict[str, Any]
    semantic_contract_version: str = "0.4.0"
    provenance_references: list[str]

class CognitiaAdvisoryRequest(DomainModel):
    """Formal advisory request payload sent to Cognitia reasoning plane."""

    request_id: str
    project_id: str
    operation_type: str
    context_graph_hash: str
    semantic_contract_version: str = "0.4.0"
    semantic_context: CognitiaSemanticContext
    provenance_references: list[str]
    constraints: dict[str, Any]
    capabilities: list[str]

class CognitiaAdvisoryResult(DomainModel):
    """Advisory-only result emitted by Cognitia reasoning plane."""

    result_id: str
    request_id: str
    context_graph_hash: str
    recommendations: list[str]
    criticisms: list[str]
    candidate_hypotheses: list[str]
    candidate_relationships: list[dict[str, Any]]
    uncertainty: float
    provenance: dict[str, Any]
    model_metadata: dict[str, Any]
    advisory_status: str = "ADVISORY"
```

---

## 3. Invariants & Context Hashing

1. **Context Boundedness**: Cognitia receives only the subgraph relevant to the seed nodes and specified traversal depth, not the entire repository or database.
2. **Deterministic Context Hash**: `context_graph_hash == compute_graph_content_hash(subgraph)`.
3. **No Persistence or Execution Data**: Contexts must never include SQL handles, database credentials, active transactions, filesystem paths, or execution backend hooks.
