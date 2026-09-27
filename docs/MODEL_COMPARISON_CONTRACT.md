# Model Comparison Contract (Phase 2.3)

## Overview

This document specifies the contract for model comparison in ResearchForge Phase 2.3.

Model comparison produces evidence about differences between models. It does NOT automatically declare a winner.

## Critical Principle

> **Model comparison produces evidence. Human/domain authority determines the scientific conclusion.**

## ModelComparison Entity

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique comparison identifier |
| `comparison_id` | `str` | Unique comparison identifier (semantic) |
| `name` | `str` | Human-readable comparison name |
| `description` | `str` | Purpose and scope |
| `model_ids` | `list[str]` | Models being compared |
| `comparison_method` | `ComparisonMethod` | Primary comparison method |
| `experiment_ids` | `list[str]` | Comparable experiments used |
| `reference_solution_ids` | `list[str]` | Reference solutions used |
| `convergence_study_ids` | `list[str]` | Supporting convergence studies |
| `sensitivity_study_ids` | `list[str]` | Supporting sensitivity studies |
| `numerical_verification_ids` | `list[str]` | Supporting numerical verifications |
| `result_id` | `str \| None` | ID of ModelComparisonResult |
| `status` | `str` | PENDING, COMPLETED, FAILED |
| `metadata` | `dict[str, Any]` | Additional metadata |

## ModelComparisonResult Entity

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique result identifier |
| `result_id` | `str` | Unique result identifier (semantic) |
| `comparison_id` | `str` | Parent comparison identifier |
| `model_ids` | `list[str]` | Models included |
| `observable_differences` | `dict[str, float]` | Observable differences |
| `error_metrics` | `dict[str, float]` | Error metrics |
| `numerical_verifications` | `list[str]` | Supporting verification IDs |
| `convergence_studies` | `list[str]` | Supporting convergence study IDs |
| `sensitivity_studies` | `list[str]` | Supporting sensitivity study IDs |
| `assumption_differences` | `list[str]` | Assumption differences |
| `validation_status` | `ModelValidationStatus` | Numerical validation status |
| `physical_validation_status` | `ModelValidationStatus` | Physical validation status |
| `notes` | `str` | Interpretation notes |
| `metadata` | `dict[str, Any]` | Additional metadata |

## Comparison Methods

| Method | Description |
|--------|-------------|
| `OBSERVABLE_DIFFERENCE` | Direct observable comparison |
| `ERROR_METRIC` | Error metric comparison |
| `RESIDUAL_ANALYSIS` | Residual analysis |
| `FIT_METRIC` | Fit quality comparison |
| `CONVERGENCE_COMPARISON` | Convergence behavior comparison |
| `SENSITIVITY_COMPARISON` | Sensitivity profile comparison |

## Evidence-Centric Output

A comparison result must contain:
1. Observable differences (not a verdict)
2. Error metrics
3. Numerical verification status
4. Physical validation status (must be explicit)
5. Assumption differences
6. Notes (must not declare a winner)

## Critical Rules

1. **Do not automatically declare a winner.**
2. **Always report physical validation status separately from numerical validation status.**
3. **Include supporting numerical verifications and convergence studies.**
4. **Model comparison is evidence for falsification, not a substitute for it.**
