# RESEARCHFORGE — PROVENANCE REPLAY MODEL

## 1. Replay Engine Architecture

The ResearchForge Replay Subsystem (`ProvenanceReplayEngine`) allows zero-state reconstruction of scientific projects purely from an append-only sequence of immutable `ProvenanceEvent` records.

```text
[Raw Provenance Event Stream] (DB / JSONL Export)
                ↓
    [Hash-Chain Integrity Validator]
                ↓
    [ProvenanceReplayEngine]
     ├── PROJECT_CREATED      → Instantiate ResearchProject(DRAFT)
     ├── QUESTION_DEFINED     → Bind ResearchQuestion
     ├── HYPOTHESIS_FORMED    → Bind Hypothesis
     ├── EXPERIMENT_DESIGNED  → Bind Experiment
     ├── RUN_COMPLETED        → Bind ExperimentRun
     └── STATE_TRANSITIONED   → Advance Project/Thread State
                ↓
[Reconstructed Project Aggregate Graph] == [Active Database State]
```

---

## 2. Replay Verification Guarantees

1. **Deterministic Reconstruction**: Replaying the event stream starting from an empty project dictionary produces entity IDs, states, and parameter attributes that match the persisted state with 100% fidelity.
2. **Tamper Sensitivity**: If an attacker modifies an historical event parameter, hash, or parent pointer, hash-chain verification (`Ledger.verify_integrity()`) fails immediately before replay is permitted.
3. **No Side-Effects**: Replay is a read-only projection; it does not re-invoke external compute sandboxes, call external APIs, or emit duplicate provenance events.
