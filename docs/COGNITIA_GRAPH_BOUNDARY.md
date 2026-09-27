# COGNITIA GRAPH BOUNDARY & AUTHORITY RULES

## 1. Epistemic Role of Cognitia

Cognitia is strictly an **Advisory Epistemic Plane**.

```
ResearchForge Semantic Graph
          │
          ▼
   Cognitia Adapter
          │
          ▼
  Advisory Cognitia Request
          │
          ▼
  Cognitia Advisory Result
          │
          ▼
  ResearchForge Application Layer
          │
          ▼
  Human / Domain Review
          │
          ▼
  GraphDelta + Provenance
          │
          ▼
  Authoritative Graph State
```

---

## 2. Strict Architectural Safeguards

1. **No Production Authority**: `advisory_status == "ADVISORY"`. Cognitia proposals are non-authoritative hypotheses or critiques.
2. **No Autonomous Mutation**: Cognitia cannot directly execute `append_graph_delta`, write to repositories, or mutate the database.
3. **No Execution Capability**: Cognitia has zero connection to execution backends (`LocalProcessBackend`, `DockerSandboxBackend`, `SlurmClusterBackend`).
4. **Explicit Promotion Pathway**: Promotion of a Cognitia candidate into authoritative domain and graph state requires:
   - An explicit `HumanDecision` signed by an authorized researcher identity.
   - Construction of a validated `GraphDelta`.
   - Execution within an atomic `UnitOfWork` transaction recording both the domain entity and graph delta.
5. **Replay Independence**: Provenance replay reconstructs graph state without making network or LLM calls to Cognitia.
