# GRAPH PERSISTENCE CONTRACT

## 1. Principle

The domain layer communicates with persistence via graph-aware contracts. The persistence layer implements this boundary through `GraphPersistencePort`.

```
ResearchGraph
      │
      ▼
GraphPersistencePort
      │
      ▼
GraphPersistenceAdapter
      │
      ▼
PostgreSQL / SQLite
```

---

## 2. Port Interface Specification

```python
class GraphPersistencePort(Protocol):
    def persist_graph(self, graph: ResearchGraph) -> None:
        """Persist a complete validated ResearchGraph atomically."""
        ...

    def load_graph(self, graph_id: str) -> ResearchGraph:
        """Reconstruct and validate a complete ResearchGraph by graph_id."""
        ...

    def append_graph_delta(self, graph_id: str, delta: GraphDelta) -> None:
        """Apply and persist an incremental GraphDelta."""
        ...

    def load_subgraph(self, graph_id: str, node_ids: set[str], depth: int = 1) -> ResearchGraph:
        """Load a neighborhood subgraph around specified seed nodes."""
        ...

    def graph_exists(self, graph_id: str) -> bool:
        """Check if graph exists in storage."""
        ...

    def get_graph_version(self, graph_id: str) -> str:
        """Get the schema version of the persisted graph."""
        ...

    def verify_graph_integrity(self, graph_id: str) -> bool:
        """Verify stored content hashes and structural invariants."""
        ...
```

---

## 3. Guarantees & Constraints

1. **Deterministic Hashing**: `canonical_hash(graph) == canonical_hash(load_graph(graph_id))`
2. **Atomic Transitions**: Graph persistence occurs within the `UnitOfWork` transaction boundary.
3. **Integrity Rejection**: Corrupted or invalid graph structures fail closed upon loading.
