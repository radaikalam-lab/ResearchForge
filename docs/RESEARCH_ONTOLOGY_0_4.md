# RESEARCHFORGE RESEARCH ONTOLOGY (v0.4)

## 1. Domain Ontology Specification

The ResearchForge Ontology formally defines the entity classes, relationship properties, validation axioms, and epistemic boundaries governing scientific discovery workflows.

---

## 2. Entity Classes (Nodes)

### 2.1 Contextual & Scoping Aggregates
* **`ResearchProject` (`PROJECT`)**: Root container encapsulating the entire investigation lifecycle. Holds immutable ID, title, description, and state machine status.
* **`ResearchThread` (`THREAD`)**: Distinct sub-inquiry within a project allowing modular exploration.
* **`ResearchQuestion` (`QUESTION`)**: Structured inquiry specifying `primary_variable`, `target_phenomenon`, and mathematical/logical `scope_boundaries`.

### 2.2 Literature & Grounding Entities
* **`Source` (`SOURCE`)**: External publication or preprint (e.g. OpenAlex entry) with DOI, abstract, and normalized content hashes.
* **`EvidenceFragment` (`EVIDENCE_FRAGMENT`)**: Atomic piece of extracted text or numeric measurement with extraction confidence and exact location references.
* **`Claim` (`CLAIM`)**: Formal proposition extracted from literature or derived from data, categorized by `ClaimType` (`EMPIRICAL`, `THEORETICAL`, `PARAMETER_RELATIONSHIP`, `LIMITATION`, `NEGATIVE_RESULT`, etc.).

### 2.3 Epistemic & Gap Entities
* **`Evidence` (`EVIDENCE`)**: Multi-fragment empirical aggregate with associated `UncertaintyProfile` and validation status.
* **`EvidenceClaimBinding` (`BINDING`)**: Epistemic link asserting that an evidence item supports or refutes a specific claim.
* **`PotentialContradiction` (`CONTRADICTION`)**: Detected discrepancy between conflicting claims with parameter/scope/methodological differences documented.
* **`ResearchGap` (`RESEARCH_GAP`)**: Rigorously validated void in knowledge, motivating new hypotheses.
* **`Hypothesis` (`HYPOTHESIS`)**: Testable, falsifiable statement specifying explicit metric thresholds and falsification conditions (`FalsificationCriterion`).

### 2.4 Computational Execution Entities
* **`Experiment` (`EXPERIMENT`)**: Specification of execution parameters, datasets, and scripts designed to test a hypothesis.
* **`ExperimentRun` (`EXPERIMENT_RUN`)**: Deterministic execution instance with container/sandbox tracking, random seed, and execution output hashes.
* **`FalsificationEvaluation` (`FALSIFICATION_EVALUATION`)**: Assessment determining whether experiment results refute or support the hypothesis (`SUPPORTED`, `FALSIFIED`, `INCONCLUSIVE`).

### 2.5 Governance & Artifact Entities
* **`HumanDecision` (`HUMAN_DECISION`)**: Cryptographically signed human authorization approving transitions, hypotheses, or conclusions.
* **`Conclusion` (`CONCLUSION`)**: Scientifically accepted claim ratified by human decision.
* **`ResearchArtifact` (`ARTIFACT`)**: Reproducible package (manuscript JSON, code bundle, data archive) with SHA-256 integrity digest.

---

## 3. Relationship Rules & Axioms

Each relationship is registered in `ONTOLOGY_RELATION_RULES` with complete validation constraints:

```python
RelationRule(
    relation_type=ResearchRelationType.TESTS,
    allowed_sources={ResearchNodeType.EXPERIMENT},
    allowed_targets={ResearchNodeType.HYPOTHESIS},
    cardinality=Cardinality.MANY_TO_ONE,
    description="Computational experiment designed to falsify a hypothesis.",
    requires_provenance=True,
    is_directed=True,
)
```

### 3.1 Axiom Matrix

| Relation | Permitted Sources | Permitted Targets | Cardinality | Directional Invariant |
|---|---|---|---|---|
| `CONTAINS` | `PROJECT` | `THREAD`, `ARTIFACT` | `ONE_TO_MANY` | Project $\to$ Thread/Artifact |
| `HAS_THREAD` | `PROJECT` | `THREAD` | `ONE_TO_MANY` | Project $\to$ Thread |
| `ASKS` | `PROJECT`, `THREAD` | `QUESTION` | `ONE_TO_MANY` | Project/Thread $\to$ Question |
| `SOURCED_FROM` | `EVIDENCE`, `EVIDENCE_FRAGMENT`, `CLAIM` | `SOURCE` | `MANY_TO_ONE` | Evidence/Claim $\to$ Source |
| `CONTAINS_EVIDENCE` | `SOURCE`, `EVIDENCE` | `EVIDENCE_FRAGMENT` | `ONE_TO_MANY` | Source/Evidence $\to$ Fragment |
| `SUPPORTS` | `EVIDENCE`, `EVIDENCE_FRAGMENT`, `CLAIM` | `CLAIM`, `HYPOTHESIS` | `MANY_TO_MANY` | Evidence/Claim $\to$ Claim/Hypothesis |
| `REFUTES` | `EVIDENCE`, `EVIDENCE_FRAGMENT`, `CLAIM` | `CLAIM`, `HYPOTHESIS` | `MANY_TO_MANY` | Evidence/Claim $\to$ Claim/Hypothesis |
| `QUALIFIES` | `EVIDENCE`, `CLAIM`, `CONTRADICTION` | `CLAIM`, `HYPOTHESIS` | `MANY_TO_MANY` | Qualifier $\to$ Target |
| `CONTRADICTS` | `CLAIM`, `CONTRADICTION` | `CLAIM` | `MANY_TO_MANY` | Claim/Contradiction $\to$ Claim |
| `ADDRESSES` | `RESEARCH_GAP`, `HYPOTHESIS` | `QUESTION`, `RESEARCH_GAP` | `MANY_TO_MANY` | Gap/Hypothesis $\to$ Target |
| `MOTIVATES` | `QUESTION`, `CONTRADICTION`, `RESEARCH_GAP` | `RESEARCH_GAP`, `HYPOTHESIS` | `MANY_TO_MANY` | Motivator $\to$ Result |
| `DERIVED_FROM` | `CLAIM`, `EVIDENCE`, `RESEARCH_GAP` | `SOURCE`, `EVIDENCE_FRAGMENT`, `EVIDENCE` | `MANY_TO_MANY` | Derived Entity $\to$ Source Material |
| `TESTS` | `EXPERIMENT` | `HYPOTHESIS` | `MANY_TO_ONE` | Experiment $\to$ Hypothesis |
| `PRODUCES` | `EXPERIMENT`, `EXPERIMENT_RUN` | `EXPERIMENT_RUN`, `ARTIFACT` | `ONE_TO_MANY` | Producer $\to$ Product |
| `EVALUATES` | `FALSIFICATION_EVALUATION` | `HYPOTHESIS`, `EXPERIMENT_RUN` | `MANY_TO_ONE` | Evaluation $\to$ Subject |
| `INFORMS` | `FALSIFICATION_EVALUATION`, `HYPOTHESIS`, `EVIDENCE` | `HUMAN_DECISION` | `MANY_TO_MANY` | Finding $\to$ Human Review |
| `ESTABLISHES` | `HUMAN_DECISION` | `CONCLUSION` | `ONE_TO_ONE` | Human Decision $\to$ Conclusion |
| `MATERIALIZES_AS` | `PROJECT`, `CONCLUSION` | `ARTIFACT` | `ONE_TO_MANY` | Entity $\to$ Artifact |

---

## 4. Epistemic Governance

1. **No Circular Epistemic Validation**: A hypothesis cannot evaluate itself, nor can an experiment approve its own conclusion.
2. **Authority Decoupling**: AI/Cognitia advisory edges (`QUALIFIES`, `MOTIVATES`) carry zero production authority. Only human cryptographically signed decisions can transition state to `ESTABLISHES`.
