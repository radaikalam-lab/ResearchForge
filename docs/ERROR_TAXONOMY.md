# Error Taxonomy (Phase 2.3)

## Overview

This document specifies the explicit error taxonomy for ResearchForge Phase 2.3.

All error categories must remain distinct. Do not collapse them into a single generic "error".

## Error Categories

| Category | Description | Example |
|----------|-------------|---------|
| `NUMERICAL_ERROR` | General numerical error | Round-off error accumulation |
| `PARAMETER_UNCERTAINTY` | Uncertainty in parameter values | `density = 1.0 ± 0.1` |
| `MEASUREMENT_ERROR` | Error in measurement process | Sensor calibration error |
| `MODEL_FORM_DISCREPANCY` | Discrepancy between model and reality | Model assumes linearity but material is nonlinear |
| `IMPLEMENTATION_ERROR` | Error in code implementation | Bug in solver |
| `BOUNDARY_ARTIFACT` | Artifact from boundary treatment | Spurious reflection from absorbing boundary |
| `DISCRETIZATION_ERROR` | Error from spatial/temporal discretization | `O(dx²)` truncation error |
| `TRUNCATION_ERROR` | Error from series truncation | Taylor series truncation |
| `UNKNOWN` | Unknown error type | Unclassified error |

## Error Budget

The system should be able to state:
- Known numerical error
- Unknown physical discrepancy
- Unmeasured uncertainty

Rather than silently combining them into a single "error" term.

## Usage in Verification

When a numerical verification fails, the error category must be recorded:

```python
verification = NumericalVerification(
    error_category=ErrorCategory.IMPLEMENTATION_ERROR,
    ...
)
```

## Critical Rules

1. **Do not collapse all errors into one generic category.**
2. **Document what is known and what is unknown.**
3. **Separate numerical error from model discrepancy from measurement error.**
