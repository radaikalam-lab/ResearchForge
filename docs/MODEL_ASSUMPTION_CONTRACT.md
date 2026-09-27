# Model Assumption Contract (Phase 2.3)

## Overview

This document specifies the contract for model assumptions in ResearchForge Phase 2.3.

An assumption is an explicit statement that a model depends on. Assumptions must be:
1. Explicitly stated
2. Categorized
3. Tracked for status changes
4. Distinguished from parameters, observations, measurements, results, and conclusions

## Assumption vs Other Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **Assumption** | Explicit condition the model depends on | "Material is homogeneous" |
| **Parameter** | Adjustable value in the model | `density = 1.0` |
| **Observation** | Measured data point | `u(5, 10) = 0.23` |
| **Measurement** | Process of obtaining data | "Laser vibrometer at 1 kHz" |
| **Result** | Computed output | `max_displacement = 0.45` |
| **Conclusion** | Scientific interpretation | "Wave attenuation is significant" |

## Assumption Categories

See `docs/MODEL_CONTRACT.md` for the full list of assumption categories.

## Assumption Status Lifecycle

```
ACTIVE → RELAXED → VIOLATED
   ↓          ↓
 UNKNOWN ←────┘
```

## Implementation

Assumptions are represented as `ModelAssumption` domain objects with:
- `assumption_id: str`
- `statement: str`
- `category: AssumptionCategory`
- `status: str` (ACTIVE, RELAXED, VIOLATED, UNKNOWN)
- `scope: str`
- `source_ref: str` (provenance reference)

## Semantic Graph

Assumptions are represented as `ASSUMPTION` nodes in the semantic graph, linked to `SCIENTIFIC_MODEL` nodes via `HAS_ASSUMPTION` relationships.

## Critical Rule

The implementation must not silently treat assumptions as facts. Every assumption must be:
1. Explicitly recorded
2. Categorized
3. Available for review
4. Tracked for status changes
