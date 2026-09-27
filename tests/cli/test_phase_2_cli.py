"""CLI test suite for Phase 2 Graph and Experiment Planning commands."""

import json

from researchforge.cli.main import app
from researchforge.persistence.database import init_db
from typer.testing import CliRunner


def test_phase_2_cli_graph_and_experiment_commands() -> None:
    """Validate graph inspect, neighbors, and experiment design via Typer CLI."""
    init_db()

    runner = CliRunner()

    # Pre-populate project and hypothesis via CLI trajectory
    lit_res = runner.invoke(app, ["research", "run-literature-trajectory", "--json"])
    assert lit_res.exit_code == 0
    lit_data = json.loads(lit_res.stdout)
    project_id = lit_data["project_id"]
    hypothesis_id = "hyp_gap_cont_candidate"

    # 1. Plan Experiment via CLI
    exp_res = runner.invoke(
        app,
        [
            "experiment",
            "design",
            "-p",
            project_id,
            "-h",
            hypothesis_id,
            "-n",
            "CLI Experiment",
            "-s",
            "40",
            "--json",
        ],
    )
    assert exp_res.exit_code == 0
    assert "CLI Experiment Design" in exp_res.stdout

    # 2. Inspect Graph via CLI
    graph_res = runner.invoke(app, ["graph", "inspect", project_id, "--json"])
    assert graph_res.exit_code == 0
    assert "nodes" in graph_res.stdout

    # 3. Query Neighbors via CLI
    neigh_res = runner.invoke(
        app,
        ["graph", "neighbors", project_id, hypothesis_id, "--json"],
    )
    assert neigh_res.exit_code == 0
    assert "neighbors" in neigh_res.stdout
