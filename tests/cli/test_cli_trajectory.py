"""Tests for Typer CLI reference trajectory execution and provenance replay (Section 36)."""

import json

from researchforge.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_trajectory_run_command() -> None:
    """Proves CLI trajectory run completes with JSON output and valid entity IDs."""
    result = runner.invoke(app, ["trajectory", "run", "--json", "--title", "CLI Trajectory Test"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["status"] == "SUCCESS"
    assert data["project_id"].startswith("proj_")
    assert data["thread_id"].startswith("th_")
    assert data["falsification_status"] == "SUPPORTED"
    assert data["events_count"] >= 10


def test_cli_provenance_replay_command() -> None:
    """Proves CLI provenance replay verifies state reconstruction accurately."""
    result = runner.invoke(app, ["provenance", "replay", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["replayed_events"] == 2
    assert data["reconstructed_projects"] == 1
    assert data["replay_status"] == "VERIFIED_ACCURATE"


def test_cli_thread_create_command() -> None:
    """Proves CLI thread create command returns valid thread JSON."""
    result = runner.invoke(
        app,
        ["thread", "create", "--project-id", "proj_test_123", "--title", "Thread Beta", "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["project_id"] == "proj_test_123"
    assert data["title"] == "Thread Beta"
    assert data["state"] == "DRAFT"
