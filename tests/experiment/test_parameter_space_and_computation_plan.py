"""Unit tests for Phase 2 Parameter Space, Computation Plan, and Experiment Design contracts."""

from researchforge.domain.models.computation_plan import (
    AnalysisSpecification,
    ComputationPlan,
    DatasetSpecification,
    ExecutionBackendType,
    ExecutionSpecification,
    StatisticalAnalysis,
)
from researchforge.domain.models.experiment_design import (
    ExperimentDesign,
    ExperimentSpecification,
)
from researchforge.domain.models.parameter_space import (
    ParameterConstraint,
    ParameterDefinition,
    ParameterSpace,
    ParameterType,
    SamplingStrategy,
)


def test_parameter_space_contract() -> None:
    """Verify parameter space definition, types, constraints, and sampling strategy."""
    p1 = ParameterDefinition(
        id="p1",
        parameter_name="temperature",
        parameter_type=ParameterType.CONTINUOUS,
        unit="Kelvin",
        min_value=273.15,
        max_value=373.15,
        default_value=298.15,
        discretization_step=5.0,
    )
    p2 = ParameterDefinition(
        id="p2",
        parameter_name="solvent",
        parameter_type=ParameterType.CATEGORICAL,
        allowed_values=["water", "ethanol", "acetone"],
        default_value="water",
    )

    con = ParameterConstraint(
        id="c1",
        name="boiling_constraint",
        expression="temperature < 351.2 if solvent == 'ethanol' else temperature < 373.15",
        parameters_involved=["temperature", "solvent"],
    )

    ps = ParameterSpace(
        id="ps_chem_01",
        name="Solvent Reaction Space",
        parameters={"temperature": p1, "solvent": p2},
        constraints=[con],
        sampling_strategy=SamplingStrategy.LATIN_HYPERCUBE,
        sample_count=100,
    )

    assert ps.name == "Solvent Reaction Space"
    assert len(ps.parameters) == 2
    assert ps.parameters["temperature"].parameter_type == ParameterType.CONTINUOUS
    assert ps.parameters["solvent"].allowed_values == ["water", "ethanol", "acetone"]
    assert ps.sampling_strategy == SamplingStrategy.LATIN_HYPERCUBE
    assert ps.sample_count == 100


def test_computation_plan_and_execution_spec() -> None:
    """Verify computation plan, dataset schemas, analysis protocols, and resource limits."""
    exec_spec = ExecutionSpecification(
        id="exec_sandbox_01",
        backend_type=ExecutionBackendType.LOCAL_SANDBOX,
        environment_requirements={"python": ">=3.11", "numpy": ">=1.24"},
        timeout_seconds=600,
        reproducibility_seed=12345,
        network_isolated=True,
    )

    ds_spec = DatasetSpecification(
        id="ds_out_01",
        name="reaction_kinetics.parquet",
        schema_format="PARQUET",
        expected_columns=["time_sec", "yield_pct", "temperature_k"],
    )

    an_spec = AnalysisSpecification(
        id="an_ols_01",
        name="Arrhenius Activation Energy OLS",
        analysis_type="OLS_REGRESSION",
        statistical_tests=["OLS", "T_TEST"],
        alpha_threshold=0.01,
        power_target=0.90,
        target_variables=["yield_pct"],
        covariates=["temperature_k"],
    )

    plan = ComputationPlan(
        id="cp_01",
        name="Kinetics Computation Plan",
        execution_spec=exec_spec,
        dataset_specs=[ds_spec],
        analysis_specs=[an_spec],
        deterministic_execution_required=True,
    )

    assert plan.execution_spec.reproducibility_seed == 12345
    assert plan.dataset_specs[0].schema_format == "PARQUET"
    assert plan.analysis_specs[0].alpha_threshold == 0.01
    assert plan.deterministic_execution_required is True


def test_statistical_analysis_model() -> None:
    """Verify statistical analysis outcomes and falsification metrics."""
    analysis = StatisticalAnalysis(
        id="stat_01",
        analysis_spec_id="an_ols_01",
        dataset_spec_id="ds_out_01",
        dataset_uri="file:///data/reaction_kinetics.parquet",
        test_results={"r_squared": 0.96, "f_stat": 142.5},
        p_values={"temperature_k": 0.0004},
        effect_sizes={"slope": 1.84},
        confidence_intervals={"slope": [1.62, 2.06]},
        falsification_verdict="SUPPORTED",
        summary="Positive monotonic scaling verified with p < 0.001.",
    )

    assert analysis.falsification_verdict == "SUPPORTED"
    assert analysis.p_values["temperature_k"] == 0.0004
    assert analysis.test_results["r_squared"] == 0.96


def test_experiment_design_and_spec_fingerprint() -> None:
    """Verify ExperimentDesign links parameter space, computation plan, and falsification criteria."""
    ps = ParameterSpace(id="ps_01", name="Param Space")
    cp = ComputationPlan(id="cp_01", name="Comp Plan")

    design = ExperimentDesign(
        id="design_01",
        project_id="proj_01",
        hypothesis_id="hyp_01",
        name="High-Throughput Assay Design",
        parameter_space=ps,
        computation_plan=cp,
        falsification_criteria_refs=["crit_01", "crit_02"],
        version=1,
    )

    spec = ExperimentSpecification(
        id="spec_01",
        design_id=design.id,
        version=design.version,
        parameter_space_id=ps.id,
        computation_plan_id=cp.id,
        execution_spec_id=cp.execution_spec.id,
        falsification_criteria_ids=design.falsification_criteria_refs,
    )

    assert design.hypothesis_id == "hyp_01"
    assert len(design.falsification_criteria_refs) == 2
    assert spec.design_id == "design_01"
    assert spec.parameter_space_id == "ps_01"
