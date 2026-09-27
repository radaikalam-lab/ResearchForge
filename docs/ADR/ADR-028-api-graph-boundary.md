# ADR-028: API Layer Graph Boundary and Application Service Decoupling

## Status
Accepted

## Date
2026-09-27

## Context
Prior to Phase 2.1, some API endpoints directly opened `UnitOfWork` sessions and serialized graph instances. To enforce the architectural law that the API layer must remain independent of physical persistence and communicate through application services and domain projections, a strict boundary was audited and hardened.

## Decision
1. **Application Service Delegation**:
   - Introduce `GraphQueryApplicationService` in `backend/researchforge/application/queries/graph_query.py` to handle graph loading, neighbor queries, path finding, and subgraph extraction.
   - API endpoints (`GET /api/v1/graph/...`) must delegate directly to `GraphQueryApplicationService`.
2. **Forbidden Imports**:
   - Enforce via automated AST architecture tests (`tests/architecture/test_layer_boundaries.py`) that `researchforge.api` never imports `persistence.models` or `sqlalchemy`.
3. **Response DTO Projection**:
   - API responses must return explicit DTO projections or canonical serializations, never SQLAlchemy ORM models or database cursors.

## Consequences
- Clean separation between HTTP contracts and internal persistence layout.
- Graph query logic is reusable across REST API, CLI, and internal workflow services.
- 100% automated enforcement of boundary invariants.
