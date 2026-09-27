# ADR-024: Literature & Evidence Intelligence Architecture

## Status
Accepted (Phase 1)

## Context
Phase 0.3 froze the core domain contracts, persistence, transactional Unit of Work, and sandboxed execution substrate. Phase 1 introduces scientific literature ingestion, evidence fragment extraction, claim decomposition, contradiction detection, and research gap formulation.

## Decision
1. **Untrusted Literature Boundary**: Treat all incoming literature sources and extraction models as untrusted data inputs. No external source or LLM may advance project state to `CONCLUSION_ACCEPTED` or grant execution capabilities.
2. **Deterministic Identity & Provenance**: Derive source identity via SHA-256 over `(provider_name, provider_record_id)`. Maintain explicit provenance records for `SOURCE_INGESTED`, `DOCUMENT_NORMALIZED`, `CLAIM_CREATED`, `CLAIM_BOUND`, `CONTRADICTION_IDENTIFIED`, `GAP_IDENTIFIED`, and `HYPOTHESIS_GENERATED`.
3. **Decoupled Claim & Evidence Schema**: Implement explicit `EvidenceClaimBinding` and `PotentialContradiction` models separating empirical observations from theoretical claims.
4. **Mandatory Falsification Invariant**: Require explicit falsification criteria on all generated hypothesis candidates.
5. **Advisory Epistemic Plane**: Maintain Cognitia integration purely as an advisory critique plane without domain mutation authority.

## Consequences
- Full provenance traceability from raw publication abstract to hypothesis candidate.
- Trajectory is 100% replayable and verifiable without external network or LLM calls.
- Security against prompt injection and malicious literature metadata is formally preserved.
