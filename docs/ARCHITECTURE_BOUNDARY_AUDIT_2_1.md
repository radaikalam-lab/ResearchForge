# ARCHITECTURE BOUNDARY AUDIT REPORT (Phase 2.1)

## 1. Boundary Audit Summary

A comprehensive static AST inspection and dependency audit was performed across all modules in `backend/researchforge/`:

| Source Layer | Target Layer | Status | Enforcement Mechanism |
|---|---|---|---|
| `api/` | `persistence.models` (ORM) | **BLOCKED (PASS)** | Static AST check in `test_layer_boundaries.py` |
| `api/` | `sqlalchemy` | **BLOCKED (PASS)** | Static AST check in `test_layer_boundaries.py` |
| `api/` | `persistence.unit_of_work` | **BLOCKED (PASS)** | Static AST check in `test_layer_boundaries.py` (added 2026-09-27); endpoints refactored to application services |
| `domain/` | `persistence` | **BLOCKED (PASS)** | Static AST check in `test_layer_boundaries.py` |
| `domain/` | `sqlalchemy` | **BLOCKED (PASS)** | Static AST check in `test_layer_boundaries.py` |
| `providers/cognitia/` | `persistence` | **BLOCKED (PASS)** | Static AST check in `test_layer_boundaries.py` |
| `providers/cognitia/` | `execution` | **BLOCKED (PASS)** | Static AST check in `test_layer_boundaries.py` |
| `api/` | `application/queries/graph_query` | **ENFORCED (PASS)** | API endpoints delegate to application services |
| `application/` | `GraphPersistencePort` | **ENFORCED (PASS)** | Graph query/workflow services interact via port protocol |

---

## 2. Verified Data Flow Paths

### Read Flow
`HTTP GET` → `API Request` → `GraphQueryApplicationService` → `GraphQueryEngine` → `ResearchGraph` → `GraphPersistencePort` → `GraphPersistenceAdapter` → `SQLite/PostgreSQL` → `Domain/API DTO Projection` → `HTTP JSON Response`

### Mutation Flow
`HTTP POST` → `API DTO` → `Workflow Service` → `Domain Model Validation` → `GraphDelta` → `Graph Validation (validate_graph)` → `UnitOfWork` (`GraphPersistenceAdapter` + `Repository` + `Provenance`) → `COMMIT` → `API DTO Response`

### Cognitia Advisory Flow
`HTTP POST /cognitia/consult` → `CognitiaAdvisoryWorkflowService` → `GraphQueryApplicationService.get_bounded_subgraph` → `Canonical Hash Verification` → `CognitiaAdapter.consult_advisory` → `CognitiaAdvisoryResult (ADVISORY)` → `Human Review / Promotion` → `GraphDelta` → `Authoritative State`
