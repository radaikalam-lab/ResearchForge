"""Database schema migration runner and version tracker for PostgreSQL and SQLite."""

from dataclasses import dataclass

from sqlalchemy import Engine, inspect, text

from researchforge.domain.base import current_iso_timestamp
from researchforge.persistence.models import Base


@dataclass
class MigrationStep:
    """Individual declarative migration step."""

    version: int
    name: str
    up_sql_sqlite: str
    up_sql_postgres: str
    down_sql: str = ""


# Initial canonical schema migration
MIGRATIONS: list[MigrationStep] = [
    MigrationStep(
        version=1,
        name="initial_canonical_schema",
        up_sql_sqlite="-- Initial schema created via Base.metadata.create_all",
        up_sql_postgres="-- Initial schema created via Base.metadata.create_all",
    ),
    MigrationStep(
        version=2,
        name="add_performance_indexes_and_idempotency_hash",
        up_sql_sqlite="""
        CREATE INDEX IF NOT EXISTS ix_provenance_event_type ON provenance_events(event_type);
        CREATE INDEX IF NOT EXISTS ix_provenance_entity_id ON provenance_events(entity_id);
        CREATE INDEX IF NOT EXISTS ix_threads_project_id ON research_threads(project_id);
        CREATE INDEX IF NOT EXISTS ix_runs_experiment_id ON experiment_runs(experiment_id);
        """,
        up_sql_postgres="""
        CREATE INDEX IF NOT EXISTS ix_provenance_event_type ON provenance_events(event_type);
        CREATE INDEX IF NOT EXISTS ix_provenance_entity_id ON provenance_events(entity_id);
        CREATE INDEX IF NOT EXISTS ix_threads_project_id ON research_threads(project_id);
        CREATE INDEX IF NOT EXISTS ix_runs_experiment_id ON experiment_runs(experiment_id);
        """,
    ),
]


class MigrationManager:
    """Manages applying, verifying, and rolling back database migrations."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.dialect_name = engine.dialect.name
        self._ensure_migration_table()

    def _ensure_migration_table(self) -> None:
        """Create schema_migrations table if it does not already exist."""
        with self.engine.begin() as conn:
            inspector = inspect(conn)
            if not inspector.has_table("schema_migrations"):
                if self.dialect_name == "sqlite":
                    conn.execute(
                        text(
                            """
                            CREATE TABLE schema_migrations (
                                version INTEGER PRIMARY KEY,
                                name VARCHAR(128) NOT NULL,
                                applied_at VARCHAR(64) NOT NULL
                            );
                            """
                        )
                    )
                else:
                    conn.execute(
                        text(
                            """
                            CREATE TABLE IF NOT EXISTS schema_migrations (
                                version INTEGER PRIMARY KEY,
                                name VARCHAR(128) NOT NULL,
                                applied_at VARCHAR(64) NOT NULL
                            );
                            """
                        )
                    )

    def get_applied_versions(self) -> list[int]:
        """Return list of integer migration versions applied so far."""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT version FROM schema_migrations ORDER BY version ASC"))
            return [row[0] for row in result]

    def get_current_version(self) -> int:
        """Return highest applied migration version, or 0 if none."""
        applied = self.get_applied_versions()
        return max(applied) if applied else 0

    def upgrade(self, target_version: int | None = None) -> list[int]:
        """Apply pending migrations up to target_version (or all if None)."""
        # Ensure base metadata tables exist first
        Base.metadata.create_all(bind=self.engine)

        applied = set(self.get_applied_versions())
        newly_applied: list[int] = []

        for step in MIGRATIONS:
            if target_version is not None and step.version > target_version:
                break
            if step.version not in applied:
                sql = step.up_sql_postgres if self.dialect_name == "postgresql" else step.up_sql_sqlite
                with self.engine.begin() as conn:
                    # Execute migration SQL statements if non-empty
                    statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
                    for stmt in statements:
                        conn.execute(text(stmt))
                    conn.execute(
                        text("INSERT INTO schema_migrations (version, name, applied_at) VALUES (:v, :n, :a)"),
                        {"v": step.version, "n": step.name, "a": current_iso_timestamp()},
                    )
                newly_applied.append(step.version)
        return newly_applied

    def downgrade_all(self) -> None:
        """Drop all tables and migration records (for test isolation)."""
        Base.metadata.drop_all(bind=self.engine)
        with self.engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS schema_migrations;"))
