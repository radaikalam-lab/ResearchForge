"""Tests verifying secret sanitization and prevention of credential leakage in telemetry (Workstream J)."""

from researchforge.configuration.telemetry import (
    TelemetryContext,
    sanitize_telemetry_payload,
)


def test_telemetry_secret_scrubbing() -> None:
    """Validate that API keys, passwords, and private tokens are sanitized from telemetry payloads."""
    payload = {
        "user": "dr_curie",
        "api_key": "super_secret_api_key_12345",
        "nested": {
            "token": "bearer_secret_token_99999",
            "normal_field": "public_dataset_name",
        },
        "query": "search for api_key=unencrypted_param_secret in database",
    }

    sanitized = sanitize_telemetry_payload(payload)

    assert sanitized["api_key"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["token"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["normal_field"] == "public_dataset_name"
    assert "super_secret_api_key_12345" not in str(sanitized)
    assert "bearer_secret_token_99999" not in str(sanitized)


def test_telemetry_context_success_and_failure() -> None:
    """Validate TelemetryContext generates structured records without secret leakage."""
    ctx = TelemetryContext(
        operation="EXPERIMENT_RUN",
        request_id="req_telemetry_01",
        project_id="proj_01",
        actor="RESEARCHFORGE",
    )

    rec_success = ctx.record_success(details={"secret_token": "hidden_123", "status": "ok"})
    assert rec_success["status"] == "SUCCESS"
    assert rec_success["details"]["secret_token"] == "[REDACTED_SECRET]"
    assert rec_success["duration_ms"] >= 0.0

    rec_fail = ctx.record_failure(ValueError("Invalid argument"), details={"password": "pwd"})
    assert rec_fail["status"] == "FAILED"
    assert rec_fail["error_type"] == "ValueError"
    assert rec_fail["details"]["password"] == "[REDACTED_SECRET]"
