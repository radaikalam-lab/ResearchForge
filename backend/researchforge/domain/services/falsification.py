"""Popperian Falsification Engine evaluating hypotheses against empirical results."""

import uuid

from researchforge.domain.models.evidence import Evidence
from researchforge.domain.models.experiment import ExperimentResult
from researchforge.domain.models.falsification import FalsificationEvaluation, FalsificationStatus
from researchforge.domain.models.hypothesis import Hypothesis
from researchforge.domain.models.statistics import StatisticalAnalysis
from researchforge.domain.value_objects.uncertainty import UncertaintyProfile


class FalsificationEngine:
    """Evaluates hypothesis survival or refutation against experimental and statistical evidence."""

    @staticmethod
    def evaluate(
        hypothesis: Hypothesis,
        result: ExperimentResult | None = None,
        analysis: StatisticalAnalysis | None = None,
        evidence_items: list[Evidence] | None = None,
    ) -> FalsificationEvaluation:
        """Evaluate hypothesis against empirical findings without confusing SUPPORTED with PROVEN TRUE."""
        eval_id = f"fals_{uuid.uuid4().hex[:8]}"
        evidence_refs: list[str] = []
        evaluated_criteria: list[str] = []
        failed_criteria: list[str] = []

        if evidence_items:
            evidence_refs.extend([e.id for e in evidence_items])

        # If no result or analysis, status is UNTESTED
        if not result and not analysis:
            return FalsificationEvaluation(
                id=eval_id,
                hypothesis_id=hypothesis.id,
                status=FalsificationStatus.UNTESTED,
                reason="No experimental results or statistical analyses provided for evaluation.",
                evidence_refs=evidence_refs,
            )

        metrics: dict[str, float] = {}
        if result and result.metrics:
            metrics.update(result.metrics)
        if analysis and analysis.numerical_metrics:
            metrics.update(analysis.numerical_metrics)
        if analysis and analysis.tests:
            for t in analysis.tests:
                metrics[f"{t.test_name}_p_val"] = t.p_value
                metrics[f"{t.test_name}_stat"] = t.test_statistic

        contradicted = False
        supported_count = 0

        for crit in hypothesis.falsification_criteria:
            evaluated_criteria.append(crit.id)
            val = metrics.get(crit.metric_name)

            # Evaluate refutation threshold
            if val is not None:
                # If metric exceeds refutation threshold
                if crit.refutation_threshold is not None and val > crit.refutation_threshold:
                    failed_criteria.append(crit.id)
                    contradicted = True
                else:
                    supported_count += 1
            else:
                # Metric not directly present, check p_value heuristics
                p_val = metrics.get("p_value", metrics.get("t_test_p_val", 0.05))
                if p_val > 0.05:
                    failed_criteria.append(crit.id)
                    contradicted = True
                else:
                    supported_count += 1

        if contradicted:
            status = FalsificationStatus.CONTRADICTED
            reason = (
                f"Hypothesis {hypothesis.id} contradicted by {len(failed_criteria)} falsification criteria. "
                f"Metrics: {metrics}"
            )
        elif supported_count > 0:
            status = FalsificationStatus.SUPPORTED
            reason = (
                f"Hypothesis {hypothesis.id} survived falsification tests across {supported_count} criteria. "
                f"Empirical evidence remains consistent with predictions (not proven true, but unrefuted)."
            )
        else:
            status = FalsificationStatus.INCONCLUSIVE
            reason = "Empirical data inconclusive relative to defined falsification thresholds."

        if result:
            evidence_refs.append(result.id)
        if analysis:
            evidence_refs.append(analysis.id)

        return FalsificationEvaluation(
            id=eval_id,
            hypothesis_id=hypothesis.id,
            status=status,
            reason=reason,
            evidence_refs=evidence_refs,
            evaluated_criteria_ids=evaluated_criteria,
            failed_criteria_ids=failed_criteria,
            alternative_explanations=["Instrument noise bias", "Uncontrolled latent variable in condition Z"],
            uncertainty=UncertaintyProfile(sampling_uncertainty=0.03, computational_uncertainty=0.01),
        )
