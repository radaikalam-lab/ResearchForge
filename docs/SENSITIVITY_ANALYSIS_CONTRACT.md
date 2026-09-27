# Sensitivity Analysis Contract (Phase 2.3)

## Overview

This document specifies the contract for sensitivity analysis in ResearchForge Phase 2.3.

Sensitivity analysis measures how changes in input parameters affect selected observables.

## Critical Distinction

**Sensitivity analysis ≠ Uncertainty quantification**

- **Sensitivity analysis**: Varies parameters to measure response. Does not model probability distributions.
- **Uncertainty quantification**: Models parameter uncertainties as probability distributions and propagates them through the model.

ResearchForge Phase 2.3 implements sensitivity analysis only. Uncertainty quantification is a future extension.

## SensitivityStudy Entity

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique study identifier |
| `study_id` | `str` | Unique study identifier (semantic) |
| `name` | `str` | Human-readable study name |
| `model_id` | `str` | Model under study |
| `base_params` | `dict[str, Any]` | Base parameter values |
| `sensitivity_method` | `SensitivityMethod` | Sampling strategy |
| `parameter_names` | `list[str]` | Parameters included |
| `perturbation_strategy` | `dict[str, Any]` | Perturbation magnitudes |
| `observable_names` | `list[str]` | Observables tracked |
| `sample_ids` | `list[str]` | IDs of sample results |
| `sensitivity_metrics` | `dict[str, float]` | Computed sensitivity metrics |
| `is_deterministic` | `bool` | Whether study is deterministic |
| `metadata` | `dict[str, Any]` | Additional metadata |

## Sampling Strategies

| Strategy | Description |
|----------|-------------|
| `ONE_AT_A_TIME` | Vary one parameter while holding others fixed |
| `FINITE_DIFFERENCE` | Use finite difference approximation |
| `LOCAL` | Local sensitivity around baseline |
| `GLOBAL` | Global sensitivity across parameter space |

## SensitivitySample Entity

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique sample identifier |
| `sample_id` | `str` | Unique sample identifier (semantic) |
| `study_id` | `str` | Parent study identifier |
| `parameter_name` | `str` | Parameter perturbed |
| `parameter_value` | `float` | Value used for this sample |
| `baseline_value` | `float` | Baseline parameter value |
| `perturbation` | `float` | Perturbation applied |
| `observables` | `dict[str, float]` | Observable values |
| `metadata` | `dict[str, Any]` | Additional metadata |

## Sensitivity Metrics

For each parameter-observable pair, compute:
```
sensitivity = mean(|delta_observable / perturbation|)
```

This is a local sensitivity indicator, not a probability distribution.

## Determinism

For identical inputs:
- Same model
- Same version
- Same base parameters
- Same perturbation strategy

The sensitivity study must produce canonically equivalent results.

## Critical Rules

1. **Do not call sensitivity analysis "uncertainty quantification" unless probability distributions are modeled.**
2. **Document the perturbation magnitudes explicitly.**
3. **Sensitivity analysis does not establish physical validity.**
