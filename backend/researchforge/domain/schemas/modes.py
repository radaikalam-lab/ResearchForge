"""Provider operation modes and idempotency semantics."""

from enum import StrEnum


class IdempotencyMode(StrEnum):
    """Operation execution and caching semantics."""

    IDEMPOTENT = "IDEMPOTENT"
    NON_IDEMPOTENT = "NON_IDEMPOTENT"
    READ_ONLY = "READ_ONLY"
    MUTATING = "MUTATING"
