"""Model validation status enum (Phase 2.3)."""

from enum import StrEnum


class ModelValidationStatus(StrEnum):
    """Explicit model validation status.

    Numerical validity is distinct from physical validation.
    """

    UNVERIFIED = "UNVERIFIED"
    NUMERICALLY_VERIFIED = "NUMERICALLY_VERIFIED"
    EMPIRICALLY_SUPPORTED = "EMPIRICALLY_SUPPORTED"
    VALIDATED_FOR_SCOPE = "VALIDATED_FOR_SCOPE"
    INVALIDATED_FOR_SCOPE = "INVALIDATED_FOR_SCOPE"
    PARTIALLY_VALIDATED = "PARTIALLY_VALIDATED"
