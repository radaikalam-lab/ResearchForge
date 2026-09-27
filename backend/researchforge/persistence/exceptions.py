"""Persistence, transaction, concurrency, and idempotency exception types."""

from typing import Any


class PersistenceError(Exception):
    """Base exception for persistence failures."""


class OptimisticConcurrencyError(PersistenceError):
    """Raised when an aggregate entity version does not match database record on update."""

    def __init__(self, entity_id: str, expected_version: int, current_version: int) -> None:
        super().__init__(
            f"Optimistic concurrency violation on entity '{entity_id}': "
            f"attempted update with version {expected_version}, but database has version {current_version}."
        )
        self.entity_id = entity_id
        self.expected_version = expected_version
        self.current_version = current_version


class IdempotencyConflict(PersistenceError):
    """Raised when a request re-uses an idempotency key with conflicting parameters or operation."""

    def __init__(self, key: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(f"Idempotency conflict for key '{key}': {message}")
        self.key = key
        self.details = details or {}


class EntityNotFoundError(PersistenceError):
    """Raised when an entity is not found in repository."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(f"{entity_type} with ID '{entity_id}' was not found.")
        self.entity_type = entity_type
        self.entity_id = entity_id


class DatabaseMigrationError(PersistenceError):
    """Raised when a schema migration fails to apply."""
