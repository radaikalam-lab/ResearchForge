# Model Contract (Phase 2.3)

## Overview

This document specifies the formal contract for scientific models in ResearchForge Phase 2.3.

A `ScientificModel` is a formal representation of a mathematical, mechanistic, or statistical model. It is distinct from:
- A particular numerical implementation
- A particular experiment run
- A physical validation of the model
- A scientific conclusion drawn from the model

## ScientificModel Entity

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique model identifier |
| `name` | `str` | Human-readable model name |
| `version` | `str` | Semantic version of the model specification |
| `description` | `str` | Detailed description of the model |
| `mathematical_form` | `str` | Governing equations in mathematical notation |
| `equations` | `list[str]` | Explicit equation strings |
| `state_variables` | `list[str]` | State variables (e.g. `u(x,t)`, `v(x,t)`) |
| `parameters` | `dict[str, Any]` | Parameter definitions with types and domains |
| `assumptions` | `list[str]` | Explicit assumption statements |
| `boundary_conditions` | `dict[str, Any]` | Boundary condition specifications |
| `initial_conditions` | `dict[str, Any]` | Initial condition specifications |
| `source_terms` | `dict[str, Any]` | Source term specifications |
| `domain_of_validity` | `str` | Legacy field: domain of validity |
| `validity_scope` | `str` | Domain of applicability |
| `validation_status` | `ModelValidationStatus` | Current validation status |

### Lifecycle

```
UNVERIFIED
    ↓ (numerical verification passes)
NUMERICALLY_VERIFIED
    ↓ (empirical evidence supports)
EMPIRICALLY_SUPPORTED
    ↓ (validated for intended scope)
VALIDATED_FOR_SCOPE
```

Invalidation paths:
- `NUMERICALLY_VERIFIED` → `UNVERIFIED` (verification fails)
- `EMPIRICALLY_SUPPORTED` → `INVALIDATED_FOR_SCOPE` (empirical refutation)
- `VALIDATED_FOR_SCOPE` → `PARTIALLY_VALIDATED` (scope restrictions discovered)

## Model Assumptions

Assumptions are explicit statements that the model depends on. They are distinguishable from:
- Parameters (adjustable values)
- Observations (measured data)
- Measurements (data collection process)
- Results (computed outputs)
- Conclusions (scientific interpretations)

### Assumption Categories

| Category | Description |
|----------|-------------|
| `GEOMETRIC` | Geometric simplifications (1-D, 2-D, symmetry) |
| `MATERIAL` | Material property assumptions (homogeneity, isotropy) |
| `BOUNDARY` | Boundary condition assumptions |
| `INITIAL_CONDITION` | Initial state assumptions |
| `CONSTITUTIVE` | Constitutive relationship assumptions (linear, elastic) |
| `NUMERICAL` | Numerical method assumptions (discretization, stability) |
| `STATISTICAL` | Statistical assumptions (distributions, independence) |
| `MEASUREMENT` | Measurement process assumptions |
| `ENVIRONMENTAL` | Environmental condition assumptions |
| `SCALING` | Scaling or normalization assumptions |
| `LINEARITY` | Linear vs nonlinear assumptions |
| `HOMOGENEITY` | Homogeneity vs heterogeneity assumptions |
| `OTHER` | Uncategorized assumptions |

### Assumption Status

| Status | Description |
|--------|-------------|
| `ACTIVE` | Assumption is currently in effect |
| `RELAXED` | Assumption has been relaxed or modified |
| `VIOLATED` | Assumption has been violated |
| `UNKNOWN` | Assumption status is unknown |

## Semantic Graph Integration

### Node Type

`SCIENTIFIC_MODEL` — represents a `ScientificModel` entity in the semantic graph.

### Relationships

| Relationship | Source | Target | Description |
|--------------|--------|--------|-------------|
| `HAS_ASSUMPTION` | `SCIENTIFIC_MODEL` | `ASSUMPTION` | Explicit assumption underlying the model |
| `USED_BY` | `SCIENTIFIC_MODEL` | `EXPERIMENT` | Model used by experiment |

## Model Validation Status

| Status | Meaning |
|--------|---------|
| `UNVERIFIED` | No verification has been performed |
| `NUMERICALLY_VERIFIED` | Numerical verification tests pass |
| `EMPIRICALLY_SUPPORTED` | Empirical evidence supports the model |
| `VALIDATED_FOR_SCOPE` | Model validated for intended scope |
| `INVALIDATED_FOR_SCOPE` | Model invalidated for intended scope |
| `PARTIALLY_VALIDATED` | Model partially validated with scope restrictions |

**Critical distinction:** `NUMERICALLY_VERIFIED` does NOT imply `VALIDATED_FOR_SCOPE`. Numerical validity is distinct from physical validation.
