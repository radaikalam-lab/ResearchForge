"""Strongly-typed entity identifiers for domain entities."""

from typing import NewType

ProjectId = NewType("ProjectId", str)
QuestionId = NewType("QuestionId", str)
ObjectiveId = NewType("ObjectiveId", str)
ConstraintId = NewType("ConstraintId", str)
ContextId = NewType("ContextId", str)

SourceId = NewType("SourceId", str)
PaperId = NewType("PaperId", str)
ClaimId = NewType("ClaimId", str)
EvidenceId = NewType("EvidenceId", str)
FragmentId = NewType("FragmentId", str)
CitationId = NewType("CitationId", str)
DatasetId = NewType("DatasetId", str)
VariableId = NewType("VariableId", str)
MethodId = NewType("MethodId", str)
ModelId = NewType("ModelId", str)

GapId = NewType("GapId", str)
HypothesisId = NewType("HypothesisId", str)
AssumptionId = NewType("AssumptionId", str)
PredictionId = NewType("PredictionId", str)
CriterionId = NewType("CriterionId", str)

ExperimentId = NewType("ExperimentId", str)
ExperimentPlanId = NewType("ExperimentPlanId", str)
RunId = NewType("RunId", str)
ResultId = NewType("ResultId", str)

SimulationId = NewType("SimulationId", str)
AnalysisId = NewType("AnalysisId", str)
FindingId = NewType("FindingId", str)
ConclusionId = NewType("ConclusionId", str)
ArtifactId = NewType("ArtifactId", str)
ManuscriptId = NewType("ManuscriptId", str)

ProvenanceEventId = NewType("ProvenanceEventId", str)
EpistemicAssessmentId = NewType("EpistemicAssessmentId", str)
DecisionId = NewType("DecisionId", str)
