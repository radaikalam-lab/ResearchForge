# API GRAPH BOUNDARY CONTRACT

## 1. Principle & Core Law

The API layer communicates with ResearchForge scientific state strictly through **Application Services**, **Domain Projections**, and the **Semantic Graph Boundary**. 

```
HTTP Request
     ↓
API Request DTO
     ↓
Application Service (e.g. GraphQueryApplicationService / ExperimentPlanningWorkflowService)
     ↓
Semantic Graph / Domain Projections
     ↓
Graph Persistence Port
     ↓
Graph Persistence Adapter
     ↓
PostgreSQL / SQLite
     ↓
API Response DTO
     ↓
HTTP Response
```

---

## 2. Forbidden API Dependencies

The API layer is strictly forbidden from importing or referencing:
1. `researchforge.persistence.models` (SQLAlchemy ORM models like `GraphNodeRecord`, `ExperimentRecord`, etc.)
2. `sqlalchemy` (Engines, Sessions, select statements, or table metadata)
3. Direct raw database queries bypassing `UnitOfWork` or `GraphPersistencePort`

---

## 3. Endpoints & Application Service Mappings

| Endpoint | Method | Application Service | Contract Output |
|---|---|---|---|
| `/api/v1/graph/{project_id}` | GET | `GraphQueryApplicationService.get_project_graph` | Canonical serialized graph dict |
| `/api/v1/graph/{project_id}/neighbors/{node_id}` | GET | `GraphQueryApplicationService.get_node_neighbors` | Neighbor nodes & incident edges |
| `/api/v1/graph/{project_id}/path` | GET | `GraphQueryApplicationService.find_path` | Node path list or null |
| `/api/v1/cognitia/consult` | POST | `CognitiaAdvisoryWorkflowService.consult_on_subgraph` | `CognitiaAdvisoryResult` (ADVISORY) |
| `/api/v1/cognitia/promote-hypothesis` | POST | `CognitiaAdvisoryWorkflowService.promote_candidate_hypothesis` | Promoted `Hypothesis` + `HumanDecision` |
| `/api/v1/experiments/plan` | POST | `ExperimentPlanningWorkflowService.plan_experiment_trajectory` | `ExperimentDesign` |
| `/api/v1/experiments/{experiment_id}/design` | GET | `ExperimentPlanningWorkflowService` / `UnitOfWork` | `ExperimentDesign` |
| `/api/v1/experiments/{experiment_id}/parameter-space` | GET | `ExperimentPlanningWorkflowService` / `UnitOfWork` | `ParameterSpace` |

---

## 4. Invariants

1. **DTO Decoupling**: API request/response models are external representation contracts and never direct database entities.
2. **Fail-Closed Semantics**: Missing entities or corrupted graph states return clean HTTP 404/400 errors without leaking internal stack traces or connection details.
3. **Deterministic Serialization**: Graph responses match the Phase 0.4 canonical graph serialization schema (`schema_version="0.4.0"`).
