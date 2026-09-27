"""Formal provider error taxonomy (Section 29)."""


class ProviderError(Exception):
    """Base exception for all provider faults and failures."""

    def __init__(self, message: str, provider_name: str = "", details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.provider_name = provider_name
        self.details = details or {}


class ProviderUnavailable(ProviderError):
    """Raised when external service, daemon, or server is unreachable."""


class ProviderTimeout(ProviderError):
    """Raised when provider call exceeds allotted timeout."""


class ProviderRateLimited(ProviderError):
    """Raised when provider rate limits are encountered."""


class ProviderAuthenticationError(ProviderError):
    """Raised on invalid credentials or authorization failure."""


class ProviderCapabilityError(ProviderError):
    """Raised when provider lacks required capability grant."""


class InvalidProviderRequest(ProviderError):
    """Raised when request DTO fails semantic or schema validation."""


class ProviderResponseValidationError(ProviderError):
    """Raised when response payload violates expected DTO structure."""


class ProviderConflict(ProviderError):
    """Raised on concurrent mutation or entity state conflict."""
