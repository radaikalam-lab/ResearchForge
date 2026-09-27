# RESEARCHFORGE — CONCURRENCY MODEL & THREAD ISOLATION

## 1. Multi-Thread Branching

A single `ResearchProject` aggregate root can supervise multiple independent `ResearchThread` branches:
* **Thread A**: Explores Hypothesis $H_A$ via Experiment $E_A$.
* **Thread B**: Explores Hypothesis $H_B$ via Experiment $E_B$.

---

## 2. Isolation Invariants

1. **State Independence**: Mutations to Thread A (e.g. state advancement, run executions, falsification results) cannot alter Thread B's internal state machine or active experiment pointers.
2. **Entity Scoping**: Experiments, runs, and thread-level artifacts are tied to specific thread and project IDs.
3. **Aggregate Summary**: The parent `ResearchProject` derives its aggregate lifecycle state dynamically from the collection of threads (`derive_aggregate_state()`). The project only advances to terminal completion when all active research threads have terminated.
