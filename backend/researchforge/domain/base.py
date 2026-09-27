"""Domain base classes: Entity, AggregateRoot, and ValueObject with deterministic serialization."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(UTC)


def current_iso_timestamp() -> str:
    """Return current UTC timestamp in ISO 8601 string format."""
    return datetime.now(UTC).isoformat()


def canonical_json_dumps(obj: Any) -> str:
    """Produce deterministic, sorted JSON representation (RFC 8785 principles)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


class ValueObject(BaseModel):
    """Immutable, identity-less domain value object."""

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        validate_assignment=True,
    )

    def value_hash(self) -> str:
        """Compute SHA-256 hash of immutable value object payload."""
        canonical = canonical_json_dumps(self.model_dump(mode="json"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class Entity(BaseModel):
    """Identity-bearing domain entity with lifecycle and provenance tracking."""

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        frozen=False,
    )

    id: str = Field(description="Unique entity identifier")
    schema_version: str = Field(default="1.0.0", description="Semantic schema version")
    created_at: datetime = Field(default_factory=utc_now, description="Creation timestamp UTC")
    updated_at: datetime = Field(default_factory=utc_now, description="Last update timestamp UTC")
    provenance_refs: list[str] = Field(
        default_factory=list, description="Historical provenance event IDs referencing this entity"
    )
    last_provenance_event_id: str | None = Field(default=None, description="Most recent provenance ledger event ID")
    status: str = Field(default="DRAFT", description="Entity lifecycle status")

    @property
    def provenance_id(self) -> str | None:
        """Backward compatibility alias for last_provenance_event_id."""
        return self.last_provenance_event_id or (self.provenance_refs[-1] if self.provenance_refs else None)

    @provenance_id.setter
    def provenance_id(self, val: str | None) -> None:
        """Backward compatibility setter."""
        self.last_provenance_event_id = val
        if val and val not in self.provenance_refs:
            self.provenance_refs.append(val)

    def content_hash(self, exclude_fields: set[str] | None = None) -> str:
        """Compute deterministic SHA-256 hash over canonical representation."""
        data = self.model_dump(mode="json")
        default_excludes = {
            "provenance_id",
            "provenance_refs",
            "last_provenance_event_id",
            "updated_at",
        }
        if exclude_fields:
            default_excludes.update(exclude_fields)
        for field in default_excludes:
            data.pop(field, None)
        canonical = canonical_json_dumps(data)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AggregateRoot(Entity):
    """Aggregate root that owns transactional and consistency boundaries."""

    version: int = Field(default=1, description="Optimistic concurrency control version")

    def increment_version(self) -> None:
        """Increment aggregate version on mutation."""
        self.version += 1
        self.updated_at = utc_now()


# Backward compatibility alias
DomainModel = Entity
