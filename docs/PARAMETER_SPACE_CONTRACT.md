# PARAMETER SPACE CONTRACT

## 1. Scope & Purpose

The `ParameterSpace` defines the multidimensional domain of parameters explored in an experiment. It separates the **declarative exploration space** from concrete runtime assignments.

---

## 2. Core Schema

```python
class ParameterType(str, Enum):
    CONTINUOUS = "CONTINUOUS"
    DISCRETE = "DISCRETE"
    CATEGORICAL = "CATEGORICAL"
    GRID = "GRID"

class SamplingStrategy(str, Enum):
    GRID = "GRID"
    RANDOM = "RANDOM"
    LATIN_HYPERCUBE = "LATIN_HYPERCUBE"
    SOBOL = "SOBOL"
    CUSTOM = "CUSTOM"

class ParameterConstraint(DomainModel):
    constraint_name: str
    expression: str
    parameters_involved: list[str]

class ParameterDefinition(DomainModel):
    parameter_name: str
    parameter_type: ParameterType
    unit: str | None
    min_value: float | None
    max_value: float | None
    step_size: float | None
    allowed_values: list[Any] | None
    default_value: Any | None
    constraints: list[ParameterConstraint]

class ParameterSpace(DomainModel):
    name: str
    parameters: list[ParameterDefinition]
    sampling_strategy: SamplingStrategy
    global_constraints: list[ParameterConstraint]
```

---

## 3. Invariants & Validation

1. **Unique Names**: Parameter names within a single space must be unique.
2. **Bound Consistency**: For `CONTINUOUS` and `DISCRETE` parameters, `min_value <= max_value`.
3. **Categorical Consistency**: For `CATEGORICAL` parameters, `allowed_values` must be non-empty.
4. **Graph Projection**: Parameter spaces project to `PARAMETER_SPACE`, `PARAMETER_DEFINITION`, and `PARAMETER_CONSTRAINT` nodes in the semantic graph connected via `CONTAINS_PARAMETER` and `CONSTRAINED_BY` edges.
