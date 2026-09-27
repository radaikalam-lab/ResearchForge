# EXPERIMENT DESIGN CONTRACT

## 1. Specification Contract

The `ExperimentDesign` represents the authoritative scientific specification for an experiment, completely detached from physical execution runtime state.

```python
class ExperimentDesign(DomainModel):
    experiment_id: str
    hypothesis_id: str
    design_name: str
    parameter_space: ParameterSpace
    computation_plan: ComputationPlan
    falsification_criteria_refs: list[str]
    sample_count: int
    replication_policy: dict[str, Any]
    content_hash: str
```

---

## 2. Invariants

1. **Hypothesis Association**: Every `ExperimentDesign` must explicitly reference an existing `Hypothesis` (`hypothesis_id`).
2. **Content Hash Determinism**: The `content_hash` is computed from the canonical representation of the parameter space, computation plan, and replication policy.
3. **Graph Alignment**: When an `ExperimentDesign` is persisted or modified, an `EXPERIMENT_DESIGN` node and corresponding `HAS_DESIGN` edge from the `EXPERIMENT` node must be recorded in the semantic graph.
4. **Falsification Linkage**: Falsification criteria referenced by the hypothesis must be compatible with the metrics produced by the design's computation plan.
5. **No Execution Authority**: The design describes *what* to explore and compute, but does not trigger executions.
