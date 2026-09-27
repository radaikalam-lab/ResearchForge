# Research Thread Model (Section 34, 35)

Research investigations rarely proceed as a single linear sequence. Different hypotheses within the same overall project explore alternate mechanistic paths concurrently.

---

## 1. The Hierarchical Thread Architecture

```text
                               +------------------------------------+
                               |          ResearchProject           |
                               | (Overall Goal / Aggregate Program) |
                               +-----------------+------------------+
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   ▼                             ▼                             ▼
         +-------------------+         +-------------------+         +-------------------+
         |  ResearchThread A |         |  ResearchThread B |         |  ResearchThread C |
         | State: UNDER_TEST |         | State: CRITIQUED  |         | State: REJECTED   |
         +---------+---------+         +---------+---------+         +---------+---------+
                   │                             │                             │
         ┌─────────┴─────────┐                   │                             │
         ▼                   ▼                   ▼                             ▼
   +------------+     +------------+       +------------+                +------------+
   | Hypothesis |     | Experiment |       | Hypothesis |                | Hypothesis |
   |     A1     |     |     A1     |       |     B1     |                |     C1     |
   +------------+     +------------+       +------------+                +------------+
```

---

## 2. Invariants of the Thread Model

1. **Independent Lifecycles**: The failure, rejection, or invalidation of `ResearchThread C` does NOT invalidate active progress on `ResearchThread A`.
2. **Project State Aggregation**: `ResearchProject.derive_aggregate_state()` derives its status from active threads without falsely reporting all hypotheses at the same stage.
3. **Optimistic Concurrency**: Both `ResearchProject` and `ResearchThread` maintain an integer `version` field incremented on each mutation to prevent race conditions during parallel exploration.
