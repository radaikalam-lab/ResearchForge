# ADR-005: Evidence vs Claim Separation

## Status
Accepted

## Context
In ungrounded systems, AI-generated assertions or paper citations are often treated as empirical evidence. A paper or a citation is not evidence; evidence consists of concrete fragments (text excerpts, data tables, figures, measurements).

## Decision
Represent `Evidence` and `EvidenceFragment` as distinct, first-class entities with explicit extraction methods, source locations, and validation statuses. A scientific claim cannot enter accepted state without direct evidence linking.

## Consequences
- Prevents hallucinated or ungrounded claims from propagating into accepted findings.
