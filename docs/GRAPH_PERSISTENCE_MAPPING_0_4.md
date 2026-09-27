# GRAPH PERSISTENCE MAPPING (0.4)

## 1. Overview

This document details the exact mapping from the abstract **Semantic Graph** models to normalized relational storage in PostgreSQL / SQLite.

---

## 2. Table Mappings

### 2.1 Graph Metadata (`graph_metadata`)
| Column | Type | Semantic Graph Field | Description |
|---|---|---|---|
| `graph_id` | `VARCHAR(64)` PK | `ResearchGraph.graph_id` | Unique graph identifier |
| `schema_version` | `VARCHAR(32)` | `ResearchGraph.schema_version` | Frozen semantic schema version (0.4.0) |
| `content_hash` | `VARCHAR(64)` | Canonical hash | SHA-256 canonical hash of full graph |
| `node_count` | `INTEGER` | `len(ResearchGraph.nodes)` | Total node count |
| `edge_count` | `INTEGER` | `len(ResearchGraph.edges)` | Total edge count |
| `created_at` | `DATETIME` | Timestamp | Creation timestamp |
| `updated_at` | `DATETIME` | Timestamp | Last update timestamp |

### 2.2 Graph Nodes (`graph_nodes`)
| Column | Type | Semantic Graph Field | Description |
|---|---|---|---|
| `node_id` | `VARCHAR(64)` PK | `ResearchNode.node_id` | Graph node identifier |
| `graph_id` | `VARCHAR(64)` FK | Graph scope | Parent graph ID |
| `node_type` | `VARCHAR(64)` | `ResearchNode.node_type` | `ResearchNodeType` enum value |
| `entity_id` | `VARCHAR(64)` | `ResearchNode.entity_id` | Associated domain entity ID |
| `label` | `VARCHAR(255)` | `ResearchNode.label` | Human-readable label |
| `properties_json`| `TEXT` | `ResearchNode.properties` | Serialized property map |
| `provenance_ref`| `VARCHAR(64)` | `ResearchNode.provenance_ref` | Provenance event or entity ref |
| `content_hash` | `VARCHAR(64)` | `ResearchNode.content_hash` | Deterministic node hash |

### 2.3 Graph Edges (`graph_edges`)
| Column | Type | Semantic Graph Field | Description |
|---|---|---|---|
| `edge_id` | `VARCHAR(64)` PK | `ResearchEdge.edge_id` | Graph edge identifier |
| `graph_id` | `VARCHAR(64)` FK | Graph scope | Parent graph ID |
| `relation_type` | `VARCHAR(64)` | `ResearchEdge.relation_type` | `ResearchRelationType` enum value |
| `source_node_id`| `VARCHAR(64)` | `ResearchEdge.source_node_id`| Source node ID |
| `target_node_id`| `VARCHAR(64)` | `ResearchEdge.target_node_id`| Target node ID |
| `properties_json`| `TEXT` | `ResearchEdge.properties` | Edge properties |
| `provenance_ref`| `VARCHAR(64)` | `ResearchEdge.provenance_ref` | Provenance reference |
| `content_hash` | `VARCHAR(64)` | `ResearchEdge.content_hash` | Deterministic edge hash |

### 2.4 Graph Deltas (`graph_deltas`)
| Column | Type | Description |
|---|---|---|
| `delta_id` | `VARCHAR(64)` PK | Unique delta identifier |
| `graph_id` | `VARCHAR(64)` FK | Graph target |
| `delta_payload_json` | `TEXT` | Serialized list of delta operations |
| `parent_hash` | `VARCHAR(64)` | Graph hash before delta |
| `resulting_hash` | `VARCHAR(64)` | Graph hash after delta |
| `applied_at` | `DATETIME` | Timestamp applied |

---

## 3. Reconstruction Lifecycle

```
SQL Tables (graph_nodes, graph_edges, graph_metadata)
    ↓ SELECT WHERE graph_id = ?
Row records
    ↓ Deserialization
List of ResearchNode, ResearchEdge
    ↓ Validation (validate_graph)
ResearchGraph (in-memory, verified invariants)
    ↓ Hashing verification
Assert loaded_hash == metadata.content_hash
```
