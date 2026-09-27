# Research Gap Analysis Contract (Phase 1)

## 1. Provider Boundary

The `GapAnalysisProvider` consumes structured evidence, extracted claims, and detected contradictions to identify candidate unexplored spaces.

```python
class GapAnalysisProvider(ABC):
    provider_name: str
    version: str = "1.0.0"

    @abstractmethod
    async def analyze_gaps(
        self,
        evidence_items: list[Evidence],
        claims: list[Claim] | None = None,
        contradictions: list[PotentialContradiction] | None = None,
    ) -> list[GapCandidate]:
        """Propose research gap candidates based on evidence and claim contradictions."""
        ...

    @abstractmethod
    async def evaluate_gap_validity(
        self,
        candidate: GapCandidate,
        evidence_items: list[Evidence],
    ) -> ResearchGap | None:
        """Promote a valid candidate to a domain ResearchGap entity."""
        ...
```

## 2. Gap Categories (`GapType`)

- `PARAMETER_GAP`: Unexplored parameter regime.
- `BOUNDARY_CONDITION_GAP`: Unknown transition behavior between regimes.
- `METHOD_GAP`: Insufficient or uncalibrated methodology.
- `DATA_GAP`: Lack of empirical observations.
- `POPULATION_GAP`: Unsampled experimental conditions.
- `TEMPORAL_GAP`: Time-dependent effects unmeasured.
- `CONTRADICTION_GAP`: Conflicting literature requiring controlled arbitration.
- `REPRODUCIBILITY_GAP`: Conflicting findings requiring replication.

## 3. Hypothesis Generation & Falsification Invariant

When formulating a `Hypothesis` from a `ResearchGap`:
1. Falsification criteria are strictly **mandatory** (`len(falsification_criteria) >= 1`).
2. Every criterion must specify an executable `condition_expression`, `metric_name`, and `refutation_threshold`.
3. Hypotheses missing falsification criteria are rejected by domain validation.
