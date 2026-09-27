# ADR-020: Human Decision Signatures

## Status
Accepted (Phase 0.2)

## Context
A core architectural invariant of ResearchForge is that automated systems and AI agents (including Cognitia) cannot accept scientific conclusions or authorize publication without explicit human verification.

## Decision
1. Require a cryptographic signature on `HumanDecision` records using HMAC-SHA256 / Ed25519 signatures.
2. The signature binds the `decision_id`, `project_id`, `decision`, `hypothesis_id`, and `evidence_ids`.
3. The state machine transition `HUMAN_REVIEW -> CONCLUSION_ACCEPTED` enforces valid signature verification against the authorized reviewer's key.

## Consequences
* Prevents unauthorized or synthetic promotion of unverified scientific hypotheses into accepted conclusions.
* Creates non-repudiable accountability for scientific publication.
