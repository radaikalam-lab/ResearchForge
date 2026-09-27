# COMPUTATION PLAN CONTRACT

## 1. Scope & Purpose

A `ComputationPlan` specifies the declarative workflow, transformations, resource requirements, and analytical downstream steps for an experiment.

---

## 2. Model Structure

```python
class ExecutionBackendType(str, Enum):
    LOCAL_PROCESS = "LOCAL_PROCESS"
    SANDBOX_DOCKER = "SANDBOX_DOCKER"
    SLURM_CLUSTER = "SLURM_CLUSTER"
    REMOTE_GPU = "REMOTE_GPU"

class ExecutionSpecification(DomainModel):
    backend: ExecutionBackendType
    cpu_cores: int
    memory_mb: int
    gpu_required: bool
    timeout_seconds: int
    environment_variables: dict[str, str]

class DatasetSpecification(DomainModel):
    name: str
    schema_version: str
    format: str
    expected_fields: list[str]

class AnalysisSpecification(DomainModel):
    statistical_test: str
    significance_level: float
    target_metrics: list[str]
    falsification_threshold: float | None

class ComputationPlan(DomainModel):
    plan_name: str
    execution_spec: ExecutionSpecification
    dataset_spec: DatasetSpecification
    analysis_spec: AnalysisSpecification
    deterministic: bool
    seed: int | None
    pipeline_steps: list[dict[str, Any]]
```

---

## 3. Invariants

1. **Determinism Specification**: If `deterministic` is `True`, a valid integer `seed` must be specified.
2. **Resource Boundaries**: `timeout_seconds > 0`, `cpu_cores >= 1`, `memory_mb >= 128`.
3. **Graph Mapping**: A `ComputationPlan` connects to `EXECUTION_SPECIFICATION`, `DATASET_SPECIFICATION`, and `ANALYSIS_SPECIFICATION` nodes via `SPECIFIES_EXECUTION`, `SPECIFIES_DATASET`, and `SPECIFIES_ANALYSIS` edges.
