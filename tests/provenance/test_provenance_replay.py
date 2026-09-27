"""Tests for provenance replay and historical state reconstruction (Section 25)."""

from researchforge.domain.state_machine import ResearchLifecycleState
from researchforge.provenance.event_types import ProvenanceEventType
from researchforge.provenance.ledger import ProvenanceLedger
from researchforge.provenance.models import ProvenanceActor
from researchforge.provenance.replay import ProvenanceReplayEngine
from researchforge.provenance.tracker import ProvenanceTracker


def test_provenance_replay_from_empty_state() -> None:
    """Reconstruct complete domain graph from provenance events alone."""
    ledger = ProvenanceLedger()
    tracker = ProvenanceTracker(ledger)

    # 1. Project creation
    e1 = tracker.track(
        actor=ProvenanceActor.HUMAN,
        actor_id="researcher_1",
        operation=ProvenanceEventType.PROJECT_CREATED,
        entity_id="proj_replay_test",
        entity_type="ResearchProject",
        parameters={"title": "Replay Verification Study", "state": "DRAFT"},
    )

    # 2. Question defined
    e2 = tracker.track(
        actor=ProvenanceActor.HUMAN,
        actor_id="researcher_1",
        operation=ProvenanceEventType.QUESTION_DEFINED,
        entity_id="q_replay_test",
        entity_type="ResearchQuestion",
        input_refs=[e1.entity_id],
        parameters={"question_text": "What is the relation between X and Y?", "project_id": "proj_replay_test"},
    )

    # 3. Hypothesis formed
    e3 = tracker.track(
        actor=ProvenanceActor.RESEARCHFORGE,
        actor_id="engine",
        operation=ProvenanceEventType.HYPOTHESIS_FORMED,
        entity_id="hyp_replay_test",
        entity_type="Hypothesis",
        input_refs=[e2.entity_id],
        parameters={
            "project_id": "proj_replay_test",
            "statement": "X increases Y monotonically",
            "mechanism": "Direct coupling",
        },
    )

    # 4. Experiment designed
    e4 = tracker.track(
        actor=ProvenanceActor.RESEARCHFORGE,
        actor_id="engine",
        operation=ProvenanceEventType.EXPERIMENT_DESIGNED,
        entity_id="exp_replay_test",
        entity_type="Experiment",
        input_refs=[e3.entity_id],
        parameters={
            "project_id": "proj_replay_test",
            "hypothesis_id": "hyp_replay_test",
            "name": "Scan Exp",
            "parameters": {"x_steps": [0, 1, 2]},
        },
    )

    # 5. Run completed
    tracker.track(
        actor=ProvenanceActor.RESEARCHFORGE,
        actor_id="sandbox",
        operation=ProvenanceEventType.RUN_COMPLETED,
        entity_id="run_replay_test",
        entity_type="ExperimentRun",
        input_refs=[e4.entity_id],
        parameters={
            "project_id": "proj_replay_test",
            "experiment_id": "exp_replay_test",
            "status": "COMPLETED",
            "output_hash": "abc123hash",
            "random_seed": 42,
        },
    )

    # 6. State transitioned to CONCLUSION_ACCEPTED
    tracker.track(
        actor=ProvenanceActor.HUMAN,
        actor_id="researcher_1",
        operation=ProvenanceEventType.STATE_TRANSITIONED,
        entity_id="proj_replay_test",
        entity_type="ResearchProject",
        parameters={"project_id": "proj_replay_test", "target_state": "CONCLUSION_ACCEPTED"},
    )

    # Replay
    replayed_state = ProvenanceReplayEngine.replay(ledger.all_events())

    assert replayed_state.replayed_events_count == 6
    assert "proj_replay_test" in replayed_state.projects
    proj = replayed_state.projects["proj_replay_test"]
    assert proj.title == "Replay Verification Study"
    assert proj.state == ResearchLifecycleState.CONCLUSION_ACCEPTED
    assert "q_replay_test" in proj.question_ids
    assert "hyp_replay_test" in proj.hypothesis_ids
    assert "exp_replay_test" in proj.experiment_ids

    assert "hyp_replay_test" in replayed_state.hypotheses
    hyp = replayed_state.hypotheses["hyp_replay_test"]
    assert hyp.statement == "X increases Y monotonically"

    assert "run_replay_test" in replayed_state.runs
    run = replayed_state.runs["run_replay_test"]
    assert run.status == "COMPLETED"
    assert run.output_hash == "abc123hash"
