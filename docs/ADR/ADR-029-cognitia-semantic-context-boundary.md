# ADR-029: Cognitia Semantic Context and Epistemic Authority Boundary

## Status
Accepted

## Date
2026-09-27

## Context
Cognitia serves as an advisory reasoning plane for exploring hypotheses, detecting hidden assumptions, and critiquing experimental plans. It must operate over explicit, bounded semantic graph contexts without acquiring persistence access, domain authority, or execution capability.

## Decision
1. **Bounded Semantic Context**:
   - Cognitia receives `CognitiaSemanticContext` and `CognitiaAdvisoryRequest` containing a topologically bounded subgraph and its SHA-256 canonical context hash.
2. **Advisory Output Only**:
   - All responses are typed as `CognitiaAdvisoryResult` with `advisory_status="ADVISORY"`.
3. **Explicit Promotion Pathway**:
   - Promotion of advisory candidates to authoritative domain state requires an explicit `HumanDecision` and a validated `GraphDelta` committed in an atomic `UnitOfWork` transaction.
4. **Complete Isolation**:
   - Cognitia adapter code is strictly forbidden from importing or accessing `researchforge.persistence` or `researchforge.execution`.
5. **Replay Independence**:
   - Replay reconstructs state purely from the provenance event stream without consulting Cognitia.

## Consequences
- Prevents unvalidated AI/LLM outputs from polluting authoritative research state.
- Ensures total auditability of what exact graph context was reasoned over via canonical context hashes.
- Preserves full deterministic reproducibility.
