"""
Tests for Pareto frontier calculation across multi-objective trade-offs (Phase 2.4).

Verifies:
    - Multi-objective dominance checking (maximize discrimination vs minimize cost vs maximize robustness)
    - Preservation of trade-offs rather than declaring a single authoritative winner
"""

import pytest
from researchforge.domain.models.design_exploration_operators import compute_pareto_frontier
from researchforge.domain.models.experimental_design_candidate import (
    CandidateDesignEvaluation,
    ParetoCandidateSet,
)


def _build_eval(cand_id: str, disc_score: float, cost: float, robustness: float) -> CandidateDesignEvaluation:
    return CandidateDesignEvaluation(
        evaluation_id=f"eval_{cand_id}",
        candidate_design_id=cand_id,
        discrimination_score=disc_score,
        resource_cost=cost,
        numerical_robustness=robustness,
        expected_observable_difference=disc_score * 0.1,
    )


def test_pareto_frontier_identifies_non_dominated_trade_offs() -> None:
    """
    Test Pareto calculation:
        Cand 1: High discrimination (10.0), High cost (10.0), High robustness (0.8) -> Non-dominated (best signal)
        Cand 2: Low discrimination (2.0), Low cost (1.0), High robustness (0.8)   -> Non-dominated (best cost)
        Cand 3: Low discrimination (1.5), High cost (12.0), Low robustness (0.2)  -> Dominated by Cand 1 & 2
    """
    evals = [
        _build_eval("cand_1", disc_score=10.0, cost=10.0, robustness=0.8),
        _build_eval("cand_2", disc_score=2.0, cost=1.0, robustness=0.8),
        _build_eval("cand_3", disc_score=1.5, cost=12.0, robustness=0.2),
    ]

    pareto = compute_pareto_frontier("proj_pareto", evals)
    assert isinstance(pareto, ParetoCandidateSet)
    assert set(pareto.non_dominated_candidate_ids) == {"cand_1", "cand_2"}
    assert "cand_3" not in pareto.non_dominated_candidate_ids
    assert len(pareto.non_dominated_candidate_ids) == 2


def test_pareto_preserves_multiple_designs_without_picking_winner() -> None:
    """
    Verify that the system returns all non-dominated candidates and does NOT declare a single winner.
    """
    evals = [
        _build_eval("cand_a", disc_score=8.0, cost=5.0, robustness=0.5),
        _build_eval("cand_b", disc_score=5.0, cost=2.0, robustness=0.5),
    ]
    pareto = compute_pareto_frontier("proj_pareto_2", evals)
    assert len(pareto.non_dominated_candidate_ids) == 2
    # Check that metadata does not contain a single 'winner'
    assert "winner" not in pareto.metadata


def test_pareto_raises_on_empty_evaluation_set() -> None:
    """Verify empty evaluations raise ValueError."""
    with pytest.raises(ValueError, match="empty evaluation set"):
        compute_pareto_frontier("proj_empty", [])
