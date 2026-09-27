# Numerical Verification Contract (Phase 2.3)

## Overview

This document specifies the contract for numerical verification in ResearchForge Phase 2.3.

Numerical verification asks: **Did we correctly solve the mathematical model we specified?**

This is distinct from physical validation, which asks: **Does the mathematical model adequately represent the real physical system?**

## Verification Types

| Type | Description |
|------|-------------|
| `STABILITY` | Verifies numerical stability under perturbation |
| `CONVERGENCE` | Verifies convergence under refinement |
| `CONSISTENCY` | Verifies consistency with governing equations |
| `CONSERVATION` | Verifies conservation laws |
| `REFERENCE_AGREEMENT` | Verifies agreement with reference solution |
| `MANUFACTURED_SOLUTION` | Verifies against manufactured solution |
| `BOUNDARY_BEHAVIOR` | Verifies boundary condition implementation |
| `ZERO_INPUT` | Verifies zero-input response |
| `DETERMINISM` | Verifies deterministic output |

## NumericalVerification Entity

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique verification identifier |
| `verification_id` | `str` | Unique verification identifier (semantic) |
| `verification_type` | `VerificationType` | Type of verification |
| `model_id` | `str` | Model being verified |
| `passed` | `bool` | Whether verification passed |
| `metric_name` | `str` | Name of verification metric |
| `metric_value` | `float` | Numerical value of metric |
| `threshold` | `float \| None` | Pass/fail threshold |
| `resolution_params` | `dict[str, Any]` | Resolution parameters used |
| `error_category` | `ErrorCategory` | Primary error category if failed |
| `notes` | `str` | Human-readable notes |
| `metadata` | `dict[str, Any]` | Additional metadata |

## Error Categories

| Category | Description |
|----------|-------------|
| `NUMERICAL_ERROR` | General numerical error |
| `PARAMETER_UNCERTAINTY` | Uncertainty in parameter values |
| `MEASUREMENT_ERROR` | Error in measurement process |
| `MODEL_FORM_DISCREPANCY` | Discrepancy between model and reality |
| `IMPLEMENTATION_ERROR` | Error in code implementation |
| `BOUNDARY_ARTIFACT` | Artifact from boundary treatment |
| `DISCRETIZATION_ERROR` | Error from spatial/temporal discretization |
| `TRUNCATION_ERROR` | Error from series truncation |
| `UNKNOWN` | Unknown error type |

## Critical Rules

1. **Do not claim a model is verified because a single simulation completed successfully.**
2. **Numerical verification is necessary but not sufficient for physical validation.**
3. **Each verification type must be explicitly selected and recorded.**
4. **Failed verifications must record the error category.**
