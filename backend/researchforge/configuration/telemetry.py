"""Structured observability telemetry, correlation context, and secret sanitization filters."""

import json
import logging
import re
import time
from typing import Any

from researchforge.domain.base import current_iso_timestamp

logger = logging.getLogger("researchforge.telemetry")

# Patterns for detecting credentials and secrets
SECRET_KEY_PATTERNS = {"key", "secret", "token", "password", "auth", "bearer", "private_key"}
SECRET_VALUE_REGEX = re.compile(
    r"(?i)(key|secret|token|password|auth|bearer)[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_\-\.]{8,})[\"']?"
)


def sanitize_telemetry_payload(data: Any, max_string_len: int = 1000) -> Any:
    """Recursively scrub secrets and hash large payloads in telemetry records."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if any(s in k.lower() for s in SECRET_KEY_PATTERNS):
                sanitized[k] = "[REDACTED_SECRET]"
            else:
                sanitized[k] = sanitize_telemetry_payload(v, max_string_len)
        return sanitized
    elif isinstance(data, list):
        if len(data) > 50:
            return f"[DATA_ARRAY_TRUNCATED: len={len(data)}]"
        return [sanitize_telemetry_payload(x, max_string_len) for x in data]
    elif isinstance(data, str):
        if len(data) > max_string_len:
            import hashlib

            h = hashlib.sha256(data.encode("utf-8")).hexdigest()
            return f"[PAYLOAD_SHA256:{h}]"
        if SECRET_VALUE_REGEX.search(data):
            return SECRET_VALUE_REGEX.sub(r"\1: [REDACTED_SECRET]", data)
        return data
    return data


class TelemetryContext:
    """Scoped telemetry record for lifecycle and sandbox operations."""

    def __init__(
        self,
        operation: str,
        request_id: str = "",
        project_id: str = "",
        thread_id: str = "",
        entity_id: str = "",
        actor: str = "RESEARCHFORGE",
    ) -> None:
        self.operation = operation
        self.request_id = request_id
        self.project_id = project_id
        self.thread_id = thread_id
        self.entity_id = entity_id
        self.actor = actor
        self.start_time = time.perf_counter()

    def record_success(self, details: dict[str, Any] | None = None) -> dict[str, Any]:
        """Record successful operation event with elapsed duration."""
        duration_ms = (time.perf_counter() - self.start_time) * 1000.0
        record = {
            "timestamp": current_iso_timestamp(),
            "request_id": self.request_id,
            "project_id": self.project_id,
            "thread_id": self.thread_id,
            "entity_id": self.entity_id,
            "operation": self.operation,
            "actor": self.actor,
            "duration_ms": round(duration_ms, 2),
            "status": "SUCCESS",
            "error_type": None,
            "details": sanitize_telemetry_payload(details or {}),
        }
        logger.info(json.dumps(record))
        return record

    def record_failure(self, error: Exception, details: dict[str, Any] | None = None) -> dict[str, Any]:
        """Record failed operation event with exception classification."""
        duration_ms = (time.perf_counter() - self.start_time) * 1000.0
        record = {
            "timestamp": current_iso_timestamp(),
            "request_id": self.request_id,
            "project_id": self.project_id,
            "thread_id": self.thread_id,
            "entity_id": self.entity_id,
            "operation": self.operation,
            "actor": self.actor,
            "duration_ms": round(duration_ms, 2),
            "status": "FAILED",
            "error_type": type(error).__name__,
            "details": sanitize_telemetry_payload(details or {}),
        }
        logger.warning(json.dumps(record))
        return record
