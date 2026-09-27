# Claim Model & Controlled Vocabulary (Phase 1)

## 1. Separation of Claim and Evidence

A **Claim** represents a proposition asserted in the literature or by an extractor. It is distinct from the underlying **Evidence** and requires explicit binding.

```text
EvidenceFragment
       ↕ [EvidenceClaimBinding]
     Claim
```

## 2. Claim Vocabulary (`ClaimType`)

- `OBSERVATION`: Direct empirical recording.
- `MEASUREMENT`: Quantitative metric evaluation.
- `METHOD`: Experimental or computational technique.
- `CAUSAL_CLAIM`: Asserted causal relation.
- `CORRELATION`: Statistical association.
- `PARAMETER_RELATIONSHIP`: Mathematical functional relationship between variables.
- `LIMITATION`: Methodological, noise, or sample-size boundary.
- `NEGATIVE_RESULT`: Null effect observation or failed replication.
- `BOUNDARY_CONDITION`: Range or regime boundary where relationship changes.
- `CONTRADICTION`: Identified discrepancy between two or more claims.

## 3. Confidence Decomposition

Confidence is never collapsed into an opaque float. It is decomposed into:
1. `extraction_confidence`: Reliability of the extraction parser/LLM.
2. `source_reported_confidence`: Statistical confidence or p-value reported by authors.
3. `domain_assessment`: Evaluated status (`PENDING`, `ACCEPTED`, `DISPUTED`, `REFUTED`).
