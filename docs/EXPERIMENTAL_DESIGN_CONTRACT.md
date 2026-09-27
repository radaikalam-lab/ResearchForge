# ResearchForge — Experimental Design & Parameter Exploration Contract (Phase 2.4)

## 1. Architectural Authority Boundary

```text
Research Question
        ↓
Hypothesis
        ↓
Competing Models
        ↓
Model Comparison (Phase 2.3)
        ↓
Parameter / Observable Sensitivity (Phase 2.3)
        ↓
Candidate Experimental Designs (Phase 2.4)
        ↓
Design Evaluation & Pareto Frontier (Phase 2.4)
        ↓
Human / Domain Selection & Signed Decision
        ↓
Authoritative ExperimentDesign (Phase 2)
        ↓
Execution & Observables (Phase 2.2)
        ↓
Evidence & Falsification (Phase 1 / Phase 2)
```

## 2. Core Epistemic Laws

1. **Candidate Design $\neq$ Authoritative Experiment**: A generated design proposal has no right of execution until reviewed and authorized by human/domain authority.
2. **Model Difference $\neq$ Model Truth**: Observable divergence between competing models is evidence for discrimination, not proof of model validity.
3. **Useful Discrimination $> $ Discretization Noise**: A candidate is only discriminating if predicted model differences exceed numerical uncertainty ($D = \frac{\Delta \text{observable}}{\text{effective numerical uncertainty}} > 1$).
4. **Pareto Trade-offs $\neq$ Single Winner**: Multi-objective criteria (discrimination, resource cost, robustness) are exposed as a Pareto non-dominated set. No automated "best experiment" verdict is issued.
5. **Epistemic Novelty $\neq$ Production Authority**: Cognitia may propose exploratory ideas or candidate observables, but cannot promote, persist, or execute designs.

## 3. Controlled Vocabulary & Types

### 3.1 Design Objectives (`DesignObjective`)
- `MODEL_DISCRIMINATION`: Maximize observable divergence between competing theories.
- `PARAMETER_ESTIMATION`: Narrow bounds on unmeasured physical coefficients.
- `HYPOTHESIS_TESTING`: Target specific falsification criteria.
- `SENSITIVITY_CHARACTERIZATION`: Map gradient response across parameter regimes.
- `BOUNDARY_CONDITION_TEST`: Verify robustness under varying interface conditions.
- `ROBUSTNESS_TEST`: Evaluate behavior near stability and parameter limits.

### 3.2 Candidate Lifecycle Status (`DesignCandidateStatus`)
- `CANDIDATE`: Generated proposal awaiting evaluation.
- `EVALUATED`: Multi-objective discrimination and numerical metrics computed.
- `PROMOTED`: Explicitly authorized and converted to `ExperimentDesign`.
- `REJECTED`: Declining proposal recorded with rationale.

## 4. Formal Discrimination Metric

$$\mathcal{D} = \frac{|\mathcal{O}(M_A, \theta) - \mathcal{O}(M_B, \theta)|}{\delta_{\text{num}}(\theta)}$$

Where:
- $\mathcal{O}(M, \theta)$ is the target observable extracted from simulation under model $M$ and parameters $\theta$.
- $\delta_{\text{num}}(\theta)$ is the estimated numerical discretization error ($O(\Delta x^2 + \Delta t^2)$).
- $\mathcal{D} > 1$ represents viable experimental discrimination above numerical noise.
