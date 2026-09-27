"""Domain models package for ResearchForge."""

from researchforge.domain.models.artifact import (
    ArtifactType,
    Figure,
    Manuscript,
    ManuscriptSection,
    ResearchArtifact,
    Table,
)
from researchforge.domain.models.computation_plan import (
    AnalysisSpecification,
    ComputationPlan,
    DatasetSpecification,
    ExecutionBackendType,
    ExecutionSpecification,
)
from researchforge.domain.models.conclusion import (
    Conclusion,
    DecisionType,
    HumanDecision,
    ResearchFinding,
)
from researchforge.domain.models.epistemic import EpistemicAssessment, EpistemicTier
from researchforge.domain.models.evidence import (
    Claim,
    ClaimType,
    Evidence,
    EvidenceClaimBinding,
    EvidenceFragment,
    EvidenceType,
    Method,
    PotentialContradiction,
    ScientificModel,
    Variable,
)
from researchforge.domain.models.experiment import (
    Experiment,
    ExperimentPlan,
    ExperimentResult,
    ExperimentRun,
    ExperimentType,
)
from researchforge.domain.models.experiment_design import (
    ExperimentDesign,
    ExperimentSpecification,
)
from researchforge.domain.models.experimental_design_candidate import (
    CandidateDesignEvaluation,
    DesignCandidateStatus,
    DesignObjective,
    DiscriminationMetric,
    ExperimentalDesignCandidate,
    ObservableTarget,
    ParetoCandidateSet,
    ResourceRequirements,
)
from researchforge.domain.models.falsification import (
    FalsificationEvaluation,
    FalsificationStatus,
)
from researchforge.domain.models.gap import GapCandidate, GapType, ResearchGap
from researchforge.domain.models.hypothesis import (
    Assumption,
    AssumptionCategory,
    FalsificationCriterion,
    Hypothesis,
    HypothesisAlternative,
    Prediction,
)
from researchforge.domain.models.literature import Citation, Paper, Source, compute_source_identity
from researchforge.domain.models.metrics import (
    ResearchCompressionMetrics,
    ResearchEffortEstimate,
)
from researchforge.domain.models.model_comparison import (
    ComparisonMethod,
    ModelComparison,
    ModelComparisonResult,
    SensitivityMethod,
    SensitivitySample,
    SensitivityStudy,
)
from researchforge.domain.models.model_validation import ModelValidationStatus
from researchforge.domain.models.numerical_verification import (
    ConvergenceStudy,
    ErrorCategory,
    NumericalVerification,
    ReferenceSolution,
    ReferenceSolutionType,
    VerificationType,
)
from researchforge.domain.models.parameter_space import (
    ParameterConstraint,
    ParameterDefinition,
    ParameterSpace,
    ParameterType,
    SamplingStrategy,
)
from researchforge.domain.models.project import (
    ResearchConstraint,
    ResearchContext,
    ResearchObjective,
    ResearchProject,
    ResearchQuestion,
)
from researchforge.domain.models.simulation import (
    Simulation,
    SimulationMetadata,
    SimulationRun,
)
from researchforge.domain.models.statistics import (
    SensitivityAnalysis,
    StatisticalAnalysis,
    StatisticalTestResult,
)
from researchforge.domain.models.thread import ResearchThread

__all__ = [
    "AnalysisSpecification",
    "ArtifactType",
    "Assumption",
    "AssumptionCategory",
    "CandidateDesignEvaluation",
    "Citation",
    "Claim",
    "ClaimType",
    "ComparisonMethod",
    "ComputationPlan",
    "Conclusion",
    "ConvergenceStudy",
    "DatasetSpecification",
    "DecisionType",
    "DesignCandidateStatus",
    "DesignObjective",
    "DiscriminationMetric",
    "EpistemicAssessment",
    "EpistemicTier",
    "ErrorCategory",
    "Evidence",
    "EvidenceClaimBinding",
    "EvidenceFragment",
    "EvidenceType",
    "ExecutionBackendType",
    "ExecutionSpecification",
    "Experiment",
    "ExperimentDesign",
    "ExperimentPlan",
    "ExperimentResult",
    "ExperimentRun",
    "ExperimentSpecification",
    "ExperimentType",
    "ExperimentalDesignCandidate",
    "FalsificationCriterion",
    "FalsificationEvaluation",
    "FalsificationStatus",
    "Figure",
    "GapCandidate",
    "GapType",
    "HumanDecision",
    "Hypothesis",
    "HypothesisAlternative",
    "Manuscript",
    "ManuscriptSection",
    "Method",
    "ModelComparison",
    "ModelComparisonResult",
    "ModelValidationStatus",
    "NumericalVerification",
    "ObservableTarget",
    "Paper",
    "ParameterConstraint",
    "ParameterDefinition",
    "ParameterSpace",
    "ParameterType",
    "ParetoCandidateSet",
    "PotentialContradiction",
    "Prediction",
    "ReferenceSolution",
    "ReferenceSolutionType",
    "ResearchArtifact",
    "ResearchCompressionMetrics",
    "ResearchConstraint",
    "ResearchContext",
    "ResearchEffortEstimate",
    "ResearchFinding",
    "ResearchGap",
    "ResearchObjective",
    "ResearchProject",
    "ResearchQuestion",
    "ResearchThread",
    "ResourceRequirements",
    "SamplingStrategy",
    "ScientificModel",
    "SensitivityAnalysis",
    "SensitivityMethod",
    "SensitivitySample",
    "SensitivityStudy",
    "Simulation",
    "SimulationMetadata",
    "SimulationRun",
    "Source",
    "StatisticalAnalysis",
    "StatisticalTestResult",
    "Table",
    "Variable",
    "VerificationType",
    "compute_source_identity",
]
