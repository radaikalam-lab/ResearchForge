"""Tests for Typer/Rich CLI commands."""

import json

from researchforge.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_doctor() -> None:
    """Verify doctor command runs and reports diagnostic status."""
    result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["status"] == "HEALTHY"
    assert data["all_contracts_loaded"] is True


def test_cli_project_create_and_inspect() -> None:
    """Verify creating and inspecting project via CLI."""
    result = runner.invoke(app, ["project", "create", "-t", "CLI Test Project", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["title"] == "CLI Test Project"
    assert data["state"] == "DRAFT"


def test_cli_provenance_inspect() -> None:
    """Verify inspecting provenance ledger via CLI."""
    result = runner.invoke(app, ["provenance", "inspect", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["ledger_verified"] is True
