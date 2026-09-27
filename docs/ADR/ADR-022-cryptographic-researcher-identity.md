# ADR-022: Cryptographic Researcher Identity and Asymmetric Signature Verification

## Status
Accepted (Frozen in Phase 0.3)

## Context
Scientific authority in ResearchForge is strictly non-delegable to AI agents or unauthenticated actors. In Phase 0.2, human review decisions supported HMAC-SHA256 signatures as an initial proof of concept. However, production research provenance requires non-repudiation, researcher identity lifecycle management (active vs. revoked), and standard asymmetric cryptographic signing (Ed25519) where the private key never leaves the researcher's local key store.

## Decision
1. Standardize on **Ed25519** as the canonical asymmetric signature scheme for human scientific decisions and provenance checkpoints.
2. Maintain `ResearcherIdentity` entities with fields: `researcher_id`, `public_key`, `algorithm`, `key_id`, `status` (`ACTIVE`/`REVOKED`), `created_at`, and `revoked_at`.
3. Require cryptographic verification of researcher signatures before advancing research projects from `HUMAN_REVIEW` to `CONCLUSION_ACCEPTED`.
4. Automatically reject any signature produced by a revoked researcher key.

## Consequences
- Unforgeable, non-repudiable human authorization gatekeeping.
- Strict rejection of unsigned or invalidly signed scientific conclusions.
- Full cryptographic auditability for scientific review pipelines.
