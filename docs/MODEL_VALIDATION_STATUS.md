# Model Validation Status (Phase 2.3)

## Overview

This document specifies the model validation status vocabulary for ResearchForge Phase 2.3.

## Validation Statuses

| Status | Meaning |
|--------|---------|
| `UNVERIFIED` | No verification has been performed |
| `NUMERICALLY_VERIFIED` | Numerical verification tests pass |
| `EMPIRICALLY_SUPPORTED` | Empirical evidence supports the model |
| `VALIDATED_FOR_SCOPE` | Model validated for intended scope |
| `INVALIDATED_FOR_SCOPE` | Model invalidated for intended scope |
| `PARTIALLY_VALIDATED` | Model partially validated with scope restrictions |

## Critical Distinction

### Numerical Validity ≠ Physical Validation

```
NUMERICALLY_VERIFIED
    ≠
VALIDATED_FOR_SCOPE
```

- **NUMERICALLY_VERIFIED**: The numerical implementation correctly solves the mathematical model.
- **VALIDATED_FOR_SCOPE**: The mathematical model adequately represents the real physical system for a specified scope.

A model can be numerically correct without being physically validated.

## Enforcement

This distinction is enforced by:
1. Separate enum values in `ModelValidationStatus`
2. Separate fields in `ModelComparisonResult` (`validation_status` vs `physical_validation_status`)
3. Explicit tests verifying the distinction
4. Documentation in all relevant contracts

## Usage

### In ScientificModel

```python
model = ScientificModel(
    validation_status=ModelValidationStatus.NUMERICALLY_VERIFIED,
)
```

### In ModelComparisonResult

```python
result = ModelComparisonResult(
    validation_status=ModelValidationStatus.NUMERICALLY_VERIFIED,
    physical_validation_status=ModelValidationStatus.UNVERIFIED,
)
```

## Promotion Pathway

```
UNVERIFIED
    → NUMERICALLY_VERIFIED (numerical verification passes)
    → EMPIRICALLY_SUPPORTED (empirical evidence collected)
    → VALIDATED_FOR_SCOPE (validated for intended scope)
```

Invalidation:
```
NUMERICALLY_VERIFIED → UNVERIFIED (verification fails)
EMPIRICALLY_SUPPORTED → INVALIDATED_FOR_SCOPE (empirical refutation)
VALIDATED_FOR_SCOPE → PARTIALLY_VALIDATED (scope restrictions)
```
