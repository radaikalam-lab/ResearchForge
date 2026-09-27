# OBSERVABILITY & TELEMETRY CONTRACT

## 1. Principles
ResearchForge implements structured observability with correlation IDs across all workflows. Observability records must maintain complete contextual traceability while strictly preventing the leakage of private keys, tokens, or raw proprietary payloads into telemetry streams.

---

## 2. Telemetry Record Schema

Every high-level operation outputs a structured JSON log record with the following mandatory fields:

| Field | Type | Description |
|---|---|---|
| `timestamp` | `string` | ISO 8601 UTC timestamp |
| `request_id` | `string` | Unique trace / request identifier |
| `project_id` | `string` | Associated ResearchProject identifier |
| `thread_id` | `string` | Associated ResearchThread branch identifier |
| `entity_id` | `string` | Target aggregate or entity identifier |
| `operation` | `string` | Executed operation name |
| `actor` | `string` | Authenticated actor name |
| `duration_ms` | `float` | Wall-clock elapsed duration in milliseconds |
| `status` | `string` | `SUCCESS` or `FAILED` |
| `error_type` | `string` | Name of exception class on failure, or `null` |
| `details` | `object` | Sanitized key-value metadata |

---

## 3. Secret Sanitization Policy

All logged details pass through `sanitize_telemetry_payload()`:
1. **Redaction of Credential Keys**: Any dictionary key matching `key`, `secret`, `token`, `password`, `auth`, `bearer`, or `private_key` is replaced with `[REDACTED_SECRET]`.
2. **Regex Masking**: String values matching credential assignment patterns are masked.
3. **Payload Truncation / Content Digest**: Large numerical arrays, matrix dumps, or full-text documents are replaced with content hashes (`sha256:...`) to prevent telemetry log bloat.
